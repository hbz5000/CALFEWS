from __future__ import division
import numpy as np
import calendar
import pandas as pd
import json
from .util import *

class Delta():

  def __init__(self, df, key):
    self.T = len(df)
    self.index = df.index
    self.key = key
    self.forecastSCWYT = "AN"
    self.forecastSJWYT = "AN"
    self.last_year_vamp = 5.0

    for k,v in json.load(open('cord/delta/Delta_properties.json')).items():
      setattr(self,k,v)

    # Vectors for delta Inflows
    self.gains = np.zeros(self.T)
    self.gains_sac = df.SAC_gains * cfs_tafd
    self.gains_sj = df.SJ_gains * cfs_tafd
    self.depletions = df.delta_depletions * cfs_tafd
    self.ccc = df.CCC_pump * cfs_tafd
    self.barkerslough = df.BRK_pump *cfs_tafd
    self.vernalis_flow = np.zeros(self.T)
    self.eastside_streams = df.EAST_gains * cfs_tafd
    self.inflow = np.zeros(self.T)

	##Vectors for delta outflows/exports
    self.dmin = np.zeros(self.T)
    self.sodd_cvp = np.zeros(self.T)
    self.sodd_swp = np.zeros(self.T)
    self.TRP_pump = np.zeros(self.T)
    self.HRO_pump = np.zeros(self.T)
    self.outflow = np.zeros(self.T)
    self.surplus = np.zeros(self.T)
    self.x2 = np.zeros(self.T)
    self.x2[0] = 82.0
    self.x2constraint = {}
    self.x2constraint['W'] = np.zeros(366)
    self.x2constraint['AN'] = np.zeros(366)
    self.x2constraint['BN'] = np.zeros(366)
    self.x2constraint['D'] = np.zeros(366)
    self.x2constraint['C'] = np.zeros(366)

	##River Indicies
    self.eri = np.zeros(self.T)	
    self.forecastSRI = np.zeros(self.T)
    self.forecastSJI = np.zeros(self.T)

	##Old/Middle River Calculations
    self.hist_OMR = df.OMR * cfs_tafd
    self.hist_TRP_pump = df.TRP_pump * cfs_tafd
    self.hist_HRO_pump = df.HRO_pump * cfs_tafd
    self.OMR = np.zeros(self.T)
	
	##Variables for determining releases for export (initialize)
    self.cvp_aval_stor = 0.5
    self.swp_aval_stor = 0.5
    self.cvp_delta_outflow_pct = 0.75
    self.swp_delta_outflow_pct = 0.25
	
    self.swp_allocation = np.zeros(self.T)
    self.cvp_allocation = np.zeros(self.T)
    self.annual_HRO_pump = np.zeros(int(self.index.year[self.T-1]) - int(self.index.year[0]))
    self.annual_TRP_pump = np.zeros(int(self.index.year[self.T-1]) - int(self.index.year[0]))
	
    self.first_empty_day_SWP = 0
    self.first_empty_day_CVP = 0
    self.final_allocation_swp = 0.0
    self.final_allocation_cvp = 0.0


  def calc_expected_delta_outflow(self,shastaD,orovilleD,yubaD,folsomD,shastaMIN,orovilleMIN,yubaMIN,folsomMIN):
  #this function calculates an expectation for the volume of environmental releases expected to be made from each reservoir,
  #given the water year type
  #also calculates the dictionary self.max_tax_free - based on delta flow requirements, how much water can be pumped w/o triggering the inflow/export ratio rule at the delta pumps, for each water year type and both the cvp & swp shares
    expected_outflow_releases = {}
    self.max_tax_free = {}
    days_in_month = [31.0, 28.0, 31.0, 30.0, 31.0, 30.0, 31.0, 31.0, 30.0, 31.0, 30.0, 31.0]
    for wyt in ['W', 'AN', 'BN', 'D', 'C']:
      expected_outflow_releases[wyt] = np.zeros(366)
      self.max_tax_free[wyt] = {}
      self.max_tax_free[wyt]['swp'] = np.zeros(366)
      self.max_tax_free[wyt]['cvp'] = np.zeros(366)

    num_obs = np.zeros(366)
    num_obs_m = np.zeros(12)
    total_depletion = np.zeros(12)
    for t in range(1,self.T):
      d = int(self.index.dayofyear[t-1])
      y = int(self.index.year[t-1])
      dowy = water_day(d, calendar.isleap(y))
      m = int(self.index.month[t])
      zone = int(np.interp(dowy, self.san_joaquin_min_flow['d'], self.san_joaquin_min_flow['zone']))
      total_depletion[m-1] += min(self.depletions[t], 0.0)
      num_obs_m[m-1] += 1
      num_obs[dowy] += 1.0
      for wyt in ['W', 'AN', 'BN', 'D', 'C']:
	    ##Calc delta outflow requirements
        outflow_rule = self.min_outflow[wyt][m-1] * cfs_tafd
	    #Calc expected unstored flows
        vernalis_flows = max(self.gains_sj[t],self.san_joaquin_min_flow[wyt][zone-1]* cfs_tafd)
        trib_flow = max(shastaMIN[wyt][m-1]*cfs_tafd,shastaD[t]) + max(orovilleMIN[wyt][m-1]*cfs_tafd,orovilleD[t]) + max(yubaMIN[wyt][m-1]*cfs_tafd,yubaD[t]) + max(folsomMIN[wyt][m-1]*cfs_tafd,folsomD[t])
        #Calc releases needed to meet outflow req.
        expected_outflow_releases[wyt][dowy] += max(outflow_rule - min(self.gains_sac[t], 0.0) - self.eastside_streams[t] - vernalis_flows - min(self.depletions[t], 0.0)*cfs_tafd, 0.0)
	  	  
    #Account for delta depletions - ag use within delta
    expected_depletion = np.zeros(12)
    for x in range(0,12):
      expected_depletion[x] = total_depletion[x]/num_obs_m[x]
      if x == 3 or x == 4:
        pump_max_cvp = 750.0*cfs_tafd
        pump_max_swp = 750.0*cfs_tafd
      else:
        pump_max_cvp = 4300.0*cfs_tafd
        pump_max_swp = 6680.0*cfs_tafd
		
      #calc pumping limit before inflow/export ratio is met
      for wyt in ['W', 'AN', 'BN', 'D', 'C']:
        #outflow ratio 
        tax_free_pumping = (self.min_outflow[wyt][x]*cfs_tafd - expected_depletion[x])*((1/(1-self.export_ratio[wyt][x]))-1)
        if tax_free_pumping*0.55 > pump_max_cvp:
          self.max_tax_free[wyt]['cvp'][0] += pump_max_cvp*days_in_month[x]
          self.max_tax_free[wyt]['swp'][0] += min(tax_free_pumping - pump_max_cvp, pump_max_swp)*days_in_month[x]
        else:
          self.max_tax_free[wyt]['cvp'][0] += tax_free_pumping*0.55*days_in_month[x]
          self.max_tax_free[wyt]['swp'][0] += tax_free_pumping*0.45*days_in_month[x]

    for x in range(0,365):
      if x > 182 and x < 243:
        pump_max_cvp = 750.0*cfs_tafd
        pump_max_swp = 750.0*cfs_tafd
      else:
        pump_max_cvp = 4300.0*cfs_tafd
        pump_max_swp = 6680.0*cfs_tafd
      m = int(self.index.month[x])
      for wyt in ['W', 'AN', 'BN', 'D', 'C']:
        tax_free_pumping = (self.min_outflow[wyt][m-1]*cfs_tafd - expected_depletion[m-1])*((1/(1-self.export_ratio[wyt][m-1]))-1)
        if tax_free_pumping*0.55 > pump_max_cvp:
          self.max_tax_free[wyt]['cvp'][x+1] = self.max_tax_free[wyt]['cvp'][x] - pump_max_cvp
          self.max_tax_free[wyt]['swp'][x+1] = self.max_tax_free[wyt]['swp'][x] - min(tax_free_pumping - pump_max_cvp, pump_max_swp)
        else:
          self.max_tax_free[wyt]['cvp'][x+1] = self.max_tax_free[wyt]['cvp'][x] - tax_free_pumping*0.55
          self.max_tax_free[wyt]['swp'][x+1] = self.max_tax_free[wyt]['swp'][x] - tax_free_pumping*0.45
		  
      self.x2constraint['C'][x] = 90.0
      for wyt in ['W', 'AN', 'BN', 'D']:
        if x > 180 and x < 274:
          self.x2constraint[wyt][x] = 74.0 + 5.0*(x-181)/94
        elif x >= 274 and x < 318:
          self.x2constraint[wyt][x] = 79.0 + 6.0*(x-274)/44
        else:
          self.x2constraint[wyt][x] = 90.0

      for wyt in ['W', 'AN', 'BN', 'D', 'C']:
        expected_outflow_releases[wyt][x] = expected_outflow_releases[wyt][x]/num_obs[x]

		
    return expected_outflow_releases, expected_depletion
  
  def calc_rio_vista_rule(self,t):
    #maintian flow requirements on teh sacramento at rio vista (i.e., delta inflow)
    m = int(self.index.month[t])
    wyt = self.forecastSCWYT
    shasta_contr = max(self.rio_vista_min[wyt][m-1]*cfs_tafd - self.rio_gains,0.0)
    return shasta_contr
	
  def calc_vernalis_rule(self,t,NMI):
    ##Calculates delta rules at Vernalis (San Joaquin/delta confluence)
    d = int(self.index.dayofyear[t])
    m = int(self.index.month[t])
    y = int(self.index.year[t])
    wyt = self.forecastSJWYT
    dowy = water_day(d,calendar.isleap(y))

    
	##D_1641 RULES
    ##zone refers to one of four 'min flow' groupings throughout the year, based on WYT
	##Note: I forget why I wrote the Delta_property files like this, with the 'zones' but it works
    zone = int(np.interp(dowy, self.san_joaquin_min_flow['d'], self.san_joaquin_min_flow['zone']))
    d_1641_min = self.san_joaquin_min_flow[wyt][zone-1] * cfs_tafd	
    d_1641_flow = max(d_1641_min - self.vernalis_gains, 0.0)

    ##Exchequer and Don Pedro only make contributions during a given time of the year
    if m == 9 and d == 1:
      self.last_year_vamp = self.get_vamp_no(self.forecastSJWYT)
        
    if zone == 4:
      if y < 2009:
        vamp_pulse = max(self.vamp_rule(self.vernalis_gains) - self.vernalis_gains,0.0)
        merced_contr = vamp_pulse*0.5
        tuolumne_contr = vamp_pulse*0.25
        stanislaus_contr = vamp_pulse*0.25
      else:
        vamp_pulse = max(self.new_vamp_rule[wyt]*cfs_tafd - self.vernalis_gains,0.0)
        merced_contr = vamp_pulse*0.5
        tuolumne_contr = vamp_pulse*0.25
        stanislaus_contr = vamp_pulse*0.25     
    else:
      vamp_pulse = 0.0
      stanislaus_contr = d_1641_flow
      merced_contr = 0.0
      tuolumne_contr = 0.0
    
	##BIOPS RULES for Vernalis start in 2009, before then only d_1641 rule is used
    if y > 2009:
      #biops_min = np.interp(dowy,self.san_joaquin_min['biops_d'],self.san_joaquin_min['biops_on_off'])*np.interp(NMI,self.san_joaquin_min['biops_NMI'],self.san_joaquin_min['biops_flow']) * cfs_tafd
      biops_min = 0.0
    else:
      biops_min = 0.0
	
    ##BIOPS Releases are only made from New Melones (CVP reservoir)
    if biops_min > d_1641_min:
      stanislaus_contr += max(biops_min-self.vernalis_gains,0.0) - max(max(d_1641_min,vamp_pulse)-self.vernalis_gains,0.0)
	
    return merced_contr, tuolumne_contr, stanislaus_contr
  
  def vamp_rule(self,ix):
  ##Interpolates rules from tocs_rule in *_properties.json file to get the top of the conservation
  ##pool in order to determine flood control releases in reservoir.step
    flow = ix*tafd_cfs
    for i,v in enumerate(self.vamp_flows['forecast']):
      if flow < v:
        break
    ##Double-step or dry-year reduction: if its been wet, flow targets are
	##taken from the next-highest 'bracket' (double-stepping the brackets), if
	##its been dry, no VAMP releases are required
    this_year_no = self.get_vamp_no(self.forecastSJWYT)
    step_number = self.last_year_vamp + this_year_no

    if step_number > 6.9:
      vamp_target = self.vamp_flows['target'][i+1]*cfs_tafd##double step
    elif step_number < 4.1:
      vamp_target = 0.0##dry-year reduction
    else:
      vamp_target = self.vamp_flows['target'][i]*cfs_tafd#normal conditions
		
    return vamp_target
    
  def get_vamp_no(self,wyt):
    if wyt == 'W':
      vamp_no = 5.0
    elif wyt == 'AN':
      vamp_no = 4.0
    elif wyt == 'BN':
      vamp_no = 3.0
    elif wyt == 'D':
      vamp_no = 2.0
    elif wyt == 'C':
      vamp_no = 1.0
    return vamp_no
	
  def calc_outflow_release(self,t,cvp_stored_release, swp_stored_release):
    d = int(self.index.dayofyear[t])
    m = int(self.index.month[t])
    y = int(self.index.year[t])
    wyt = self.forecastSCWYT
    dowy = water_day(d ,calendar.isleap(y))
    #this function finds the additional releases needed to satisfy delta outflows
	#and splits them between CVP and SWP based on the 75/25 rule (given previous releases)
	
    #delta outflow minimum either salinity rule or delta outflow volume
    outflow_rule = self.min_outflow[wyt][m-1] * cfs_tafd
    if dowy > 180 and dowy < 318:
      if self.x2[t-1] > self.x2constraint[wyt][dowy]:
        x2outflow = 10**((self.x2constraint[wyt][dowy] - 10.16 - 0.945*self.x2[t])/(-1.487))
      else:
        x2outflow = 0.0
    else:
      x2outflow = 0.0
		
    salinity_rule = min(x2outflow*cfs_tafd,12000.0*cfs_tafd)  
    min_rule = max(outflow_rule, salinity_rule)
	
	#this minimum dout release does not account for cvp_stored_release or swp_stored_release
    dout = max(min_rule - self.depletions[t] - (self.total_inflow - cvp_stored_release - swp_stored_release),0.0)
    
    #only release extra is dout is bigger than what has already been released (for envmin & rio vista requirements)
    if dout > (cvp_stored_release + swp_stored_release):
      swp_dout = 0.25*(dout - cvp_stored_release - swp_stored_release)
      cvp_dout = 0.75*(dout - cvp_stored_release - swp_stored_release)
      self.cvp_outflow = cvp_stored_release + cvp_dout
      self.swp_outflow = swp_stored_release + swp_dout
    else:
      cvp_dout = 0.0
      swp_dout = 0.0
      if cvp_stored_release > 0.75*dout:
        self.cvp_outflow = dout - swp_stored_release
        self.swp_outflow = swp_stored_release
      else:
        self.cvp_outflow = cvp_stored_release
        self.swp_outflow = dout - cvp_stored_release
	  
    self.total_inflow += (cvp_dout + swp_dout)
    return cvp_dout, swp_dout   

  def assign_releases(self,shastaAS,folsomAS,orovilleAS,yubaAS,shastaODP,folsomODP,orovilleODP,yubaODP):
    cvp_AS = max(shastaAS,0.0) + max(folsomAS,0.0)
    swp_AS = max(yubaAS,0.0) + max(orovilleAS,0.0)
    cvp_ODP = max(shastaODP,0.0) + max(folsomODP,0.0)
    swp_ODP = max(yubaODP,0.0) + max(orovilleODP,0.0)
    total_ODP = cvp_ODP + swp_ODP

    if cvp_AS + swp_AS > 0.0:
      release_fraction_cvp = cvp_AS/(cvp_AS + swp_AS)
      release_fraction_swp = swp_AS/(cvp_AS + swp_AS)
      if swp_AS > 0.0:
        orovilleFrac = release_fraction_swp*max(orovilleAS, 0.0)/swp_AS
        yubaFrac = release_fraction_swp*max(yubaAS, 0.0)/swp_AS
      elif swp_ODP > 0.0:
        orovilleFrac = release_fraction_swp*max(orovilleODP, 0.0)/swp_ODP
        yubaFrac = release_fraction_swp*max(yubaODP, 0.0)/swp_ODP
      else:
        orovilleFrac = 0.0
        yubaFrac = 0.0
      if cvp_AS > 0.0:
        shastaFrac = release_fraction_cvp*max(shastaAS, 0.0)/cvp_AS
        folsomFrac = release_fraction_cvp*max(folsomAS, 0.0)/cvp_AS
      elif cvp_ODP > 0.0:
        shastaFrac = release_fraction_cvp*max(shastaODP, 0.0)/cvp_ODP
        folsomFrac = release_fraction_cvp*max(folsomODP, 0.0)/cvp_ODP
      else:
        shastaFrac = 0.0
        folsomFrac = 0.0
    elif total_ODP > 0.0:
      shastaFrac = max(shastaODP, 0.0)/total_ODP
      folsomFrac = max(folsomODP, 0.0)/total_ODP
      orovilleFrac = max(orovilleODP, 0.0)/total_ODP
      yubaFrac = max(yubaODP, 0.0)/total_ODP

    else:
      shastaFrac = 0.0
      folsomFrac = 0.0
      orovilleFrac = 0.0
      yubaFrac = 0.0
 
    return shastaFrac, folsomFrac, orovilleFrac, yubaFrac
	
  def meet_OMR_requirement(self, cvp_m, swp_m, t):
    d = int(self.index.dayofyear[t])
    m = int(self.index.month[t])
    y = int(self.index.year[t])
    wyt = self.forecastSCWYT
    dowy = water_day(d,calendar.isleap(y))

	####Old-Middle River Rule################################################################################################
	#The delta pumps make the old-middle river run backwards - there are restrictions (starting in 2008) about how big the negative flows can
	#become.  To model this, we use either a liner adjustment of flow at vernalis, or the observed flow (adding back in the pumping, to estimate
	#the 'natural' flow on the Old-Middle Rivers).  Once we have a model of the Old-Middle River, we assume that this flow is reduced (can become negative)
	# by 90% of the total pumping.  So, if the OMR limit is -5000CFS, & the natural flow is 1000CFS, pumping can be, maximum, 6000CFS/0.9
    if t < 4441:
      omrNat = self.vernalis_gains*.462 + 120*cfs_tafd#vernalis flow linear adjustment
    else:
      omrNat = self.hist_OMR[t] + (self.hist_TRP_pump[t] + self.hist_HRO_pump[t])*.9
	  
    ## OMR max negative flows are only binding Jan-June, the rest of the year flow can be anything
    omr_condition = np.interp(dowy, self.omr_reqr['d'], self.omr_reqr['flow']) * cfs_tafd
	##The OMR constraints are governed by fish-kill conditions at the pumps.  negative 5000 CFS is normal, but can also be reduced
	##here we use the actual declaration - any forward-in-time projection runs will have to be either simulated probabilistically or just run under
	##the normal condition (5000 cfs)
	###Note: OMR Flow adjustments come from here: http://www.water.ca.gov/swp/operationscontrol/calfed/calfedwomt.cfm
    fish_trigger_adj = np.interp(t, self.omr_reqr['t'], self.omr_reqr['adjustment']) * cfs_tafd
    if t < 4441:
      omrRequirement = fish_trigger_adj
    else:
      omrRequirement = max(omr_condition, fish_trigger_adj)
    
    maxTotPump = max((omrNat - omrRequirement)/.9, 0.0)
    	
    if cvp_m + swp_m > maxTotPump:
      if cvp_m < maxTotPump*0.55:
        swp_m = maxTotPump - cvp_m
      elif swp_m < maxTotPump*0.45:
        cvp_m = maxTotPump - swp_m
      else:
        swp_m = maxTotPump*0.45
        cvp_m = maxTotPump*0.55
		
    return cvp_m, swp_m
	

  def hypothetical_pumping(self, capacity_max, supply_max, pump_trigger, fraction, t):
    m = int(self.index.month[t])
    wyt = self.forecastSCWYT
    if pump_trigger == 0:
      if supply_max > 0.0:
        ##if we have the supply to maximize pumping, then the forgone pumping is equal 
        ##to the maximum pumping
        pumping_forgone = supply_max
      else:
        #if we don't, then the forgone pumping is what we'd release under the 'tax free rules' or the pumping constraint, whichever is smaller
        free_pumping = ((1/(1-self.export_ratio[wyt][m-1])) - 1)*(self.min_outflow[wyt][m-1] * cfs_tafd - self.depletions[t])*fraction
        pumping_forgone = min(capacity_max, free_pumping)
      new_constraint = 0.0
    else:
      pumping_forgone = 0.0
      new_constraint = supply_max 
	  
    return pumping_forgone, new_constraint

  def distribute_export_releases(self, t, pump_max, sodd_tot, min_daily_uncontrolled_1, min_daily_uncontrolled_2, available_storage_1, available_storage_2):
    #if the flood releases are bigger than the export releases, release at flood levels to export constraint
    total_flood = min_daily_uncontrolled_1 + min_daily_uncontrolled_2
    total_available_storage = available_storage_1 + available_storage_2
    if total_flood > sodd_tot:
      inf_constraint_frac = min(pump_max/total_flood, 1.0)#export constraint (as fraction of flood release)
      main_sodd = min_daily_uncontrolled_1*inf_constraint_frac
      secondary_sodd = min_daily_uncontrolled_2*inf_constraint_frac
    #distribute export releases (CVP) between reservoirs
    elif total_available_storage > 0.0:
      main_sodd = sodd_tot*max(available_storage_1,0.0)/total_available_storage
      secondary_sodd = sodd_tot*max(available_storage_2,0.0)/total_available_storage
    else:
      main_sodd = sodd_tot
      secondary_sodd = 0.0
	  
    return main_sodd, secondary_sodd
	
  def calc_flow_bounds(self, t, cvp_max, swp_max, cvp_max_alt, swp_max_alt, cvp_release2, swp_release2, cvp_AS, swp_AS):
    ### stored and unstored flow agreement between SWP & CVP
	### project releases for pumping must consider the I/E 'tax'
	### releases already made (environmental flows, delta outflows) and downstream gains can be credited against this tax, but
	### we first have to determine how much of each is assigned to the delta outflow.
    
	##the first step is applying all 'unstored' flows to the delta outflows
	##note: unstored_flows should be strictly positive, but available_unstored can be negative (need outflow/environmental releases to meet delta outflow requirements)
    m = int(self.index.month[t])
    wyt = self.forecastSCWYT
    d = int(self.index.dayofyear[t])
    y = int(self.index.year[t])
    dowy = water_day(d,calendar.isleap(y))
    outflow_rule = self.min_outflow[wyt][m-1] * cfs_tafd
	##Same salinity rule as in calc_flow_bounds
    if dowy > 180 and dowy < 318:
      if self.x2[t-1] > self.x2constraint[wyt][dowy]:
        x2outflow = 10**((self.x2constraint[wyt][dowy] - 10.16 - 0.945*self.x2[t])/(-1.487))
      else:
        x2outflow = 0.0
    else:
      x2outflow = 0.0
		
    salinity_rule = min(x2outflow*cfs_tafd,12000.0*cfs_tafd)

    min_rule = max(outflow_rule, salinity_rule)
    #unstored_flows = self.total_inflow - self.cvp_stored_release - self.swp_stored_release
    unstored_flows = self.total_inflow
    available_unstored = unstored_flows + self.depletions[t] - min_rule	
	
    if available_unstored < 0:
      ##if unstored flows cannot meet delta outflow requirements, 75% of the deficit comes
	  ##from releases made by CVP (25% from SWP releases) - calculated in calc_outflow_release
      cvp_frac = self.cvp_outflow/(self.cvp_outflow + self.swp_outflow)
      swp_frac = self.swp_outflow/(self.cvp_outflow + self.swp_outflow)
    else:
	  ##if unstored flows remain after meeting delta outflow requirements, the additional
	  ##flows are split 55/45 between CVP/SWP
      cvp_frac = 0.55
      swp_frac = 0.45
	
    #total volume that can be exported w/o additional inflows, based on delta required outflows & the E/I ratio
    tax_free_exports = ((1/(1-self.export_ratio[wyt][m-1])) - 1)*(min_rule - self.depletions[t])
    if cvp_release2 > 0:
      cvp_tax_free_fraction = max(min(cvp_AS/self.max_tax_free[wyt]['cvp'][dowy], 1.0), 0.0)
      cvp_portion = cvp_tax_free_fraction*0.55*tax_free_exports
    else:
      cvp_portion = 0.0
	  
    if swp_release2 > 0:
      swp_tax_free_fraction = max(min(swp_AS/self.max_tax_free[wyt]['swp'][dowy], 1.0), 0.0)
      swp_portion = swp_tax_free_fraction*0.45*tax_free_exports
    else:
      swp_portion = 0.0

    swp_tax_free_pumping = min(swp_portion, swp_max_alt)
    cvp_tax_free_pumping = min(cvp_portion, cvp_max_alt)

	##how many releases are needed for the 'untaxed exports' - given delta gains
    if available_unstored > tax_free_exports:
      cvp_releases_untaxed = 0.0
      swp_releases_untaxed = 0.0
    else:
      cvp_releases_untaxed = cvp_tax_free_pumping - max(cvp_frac*available_unstored, 0.0)
      swp_releases_untaxed = swp_tax_free_pumping - max(swp_frac*available_unstored, 0.0)

	##how much do we need to release for pumping diversions? (i.e. water balance)
	##we can use stored releases and any available unstored, as divided above (55/45)
	##if available unstored is less than zero, it comes out of stored release, as divided above (75/25)
    cvp_releases_for_pumping = cvp_max - cvp_frac*available_unstored
    swp_releases_for_pumping = swp_max - swp_frac*available_unstored

	##how much (if any) do we need to release to meet the I/E tax? (i.e. environmental requirements)
	##unstored_flows is always positive, so we split them 55/45 to make the 'tax' on each project pumping
    cvp_releases_for_tax = cvp_max/self.export_ratio[wyt][m-1] - 0.55*unstored_flows
    swp_releases_for_tax = swp_max/self.export_ratio[wyt][m-1] - 0.45*unstored_flows
	    
	##need to release the larger of the three requirements
    self.sodd_cvp[t] = max(cvp_releases_for_pumping, cvp_releases_for_tax, cvp_releases_untaxed, 0.0)
    self.sodd_swp[t] = max(swp_releases_for_pumping, swp_releases_for_tax, swp_releases_untaxed, 0.0)
	  
    ##unused flows from one project can be used to meet requirements for other project
    ##(i.e., if large stored releases (for environmental requirements) made from one project,
	##they may be greater than the total pumping/tax requirement, meaning the other project can
	##pump some of that water or use it to meet the 'tax'
    self.sodd_swp[t] -= min(self.sodd_cvp[t], 0.0)
    self.sodd_cvp[t] -= min(self.sodd_swp[t], 0.0)
    self.sodd_swp[t] = max(self.sodd_swp[t], 0.0)
    self.sodd_cvp[t] = max(self.sodd_cvp[t], 0.0)
    
		  
  def find_max_pumping(self, d, dowy, t, wyt):
    ##Find max pumping uses the delta pumping rules (from delta_properties) to find the maximum the pumps can
	##be run on a given day, from the D1641 and the BIOPS rules
    swp_intake_max = np.interp(d, self.pump_max['swp']['d'], self.pump_max['swp']['intake_limit']) * cfs_tafd
    swp_intake_max = max(swp_intake_max, np.interp(d, self.pump_max['swp']['d'], self.pump_max['swp']['vernalis_trigger'])*self.vernalis_gains/2.0, 0.0)
    cvp_intake_max = np.interp(d, self.pump_max['cvp']['d'],self.pump_max['cvp']['intake_limit']) * cfs_tafd
    cvp_intake_max = max(cvp_intake_max, np.interp(d, self.pump_max['cvp']['d'], self.pump_max['cvp']['vernalis_trigger'])*self.vernalis_gains/2.0, 0.0)

    san_joaquin_adj = np.interp(dowy, self.san_joaquin_add['d'], self.san_joaquin_add['mult']) * max(self.vernalis_gains, 0.0)
    if np.interp(t,self.san_joaquin_export_ratio['D1641_dates'],self.san_joaquin_export_ratio['D1641_on_off']) == 1:
      san_joaquin_ie_amt = np.interp(self.vernalis_gains*tafd_cfs, self.san_joaquin_export_ratio['D1641_flow_target'],self.san_joaquin_export_ratio['D1641_export_limit']) * cfs_tafd
    else:
      san_joaquin_ie_amt = np.interp(self.vernalis_gains*tafd_cfs, self.san_joaquin_export_ratio['flow'], self.san_joaquin_export_ratio['ratio']) * self.vernalis_gains
    
    san_joaquin_ie_used = np.interp(dowy, self.san_joaquin_export_ratio['d'], self.san_joaquin_export_ratio['on_off'])
    san_joaquin_ie = san_joaquin_ie_amt * san_joaquin_ie_used
    swp_max = min(max(swp_intake_max + san_joaquin_adj, san_joaquin_ie * 0.45), np.interp(d, self.pump_max['swp']['d'], self.pump_max['swp']['pmax']) * cfs_tafd)
    cvp_max = min(max(cvp_intake_max, san_joaquin_ie * 0.55), np.interp(d, self.pump_max['cvp']['d'], self.pump_max['cvp']['pmax']) * cfs_tafd)

    return cvp_max, swp_max
   	  
  def find_release(self, t, dowy, cvp_max, swp_max, cvpAS, swpAS):
  ###This function looks at how much water is available in storage & snowpack to be exported,
  ##then determines when the best time to release that water is (water is saved for part of year
  ##when the inflow/export 'tax' is lowest)
    wyt = self.forecastSCWYT
    y = int(self.index.year[t])
    m = int(self.index.month[t])
    pumping = {}
	###Maximum pumping capacity for each project, ceiling on projected exports
    pumping['swp']	= self.pump_max['swp']['intake_limit'][5] * cfs_tafd
    pumping['cvp'] = self.pump_max['cvp']['intake_limit'][5] * cfs_tafd
    storage = {}
    forecast_pumping = {}
	###available storage determined from reservoir class
    storage['swp'] = swpAS
    storage['cvp'] = cvpAS
    for project in ['cvp', 'swp']:
      ######The floor for pumping projections are the amount of available storage (including flow projections) in project
	  ######reservoirs, or the available 'tax free' pumping remaining that is caused by the delta E/I ratio not being binding due to 
      ######delta outflow/depletion requirements	  
      total_forecast = min(storage[project], self.max_tax_free[wyt][project][dowy])
	  ###Remaining available storage is pumped during the period with the lowest remaining E/I ratio 'tax'
      if dowy < 123:
        ##E/I ratio is 0.65 duing oct-jan, 0.35 during feb-jun, and 0.65 from july-oct
        total_taxed_oct_jan = (123.0 - dowy)*pumping[project] - (self.max_tax_free[wyt][project][dowy] - self.max_tax_free[wyt][project][122])
        total_taxed_feb_june = 150.0*pumping[project] - (self.max_tax_free[wyt][project][123] - self.max_tax_free[wyt][project][273])
        total_taxed_july_sept = 92.0*pumping[project] - self.max_tax_free[wyt][project][274]
      elif dowy < 274:
        total_taxed_oct_jan = 0.0
        total_taxed_feb_june = (273.0 - dowy)*pumping[project] - (self.max_tax_free[wyt][project][dowy] - self.max_tax_free[wyt][project][273])
        total_taxed_july_sept = 92.0*pumping[project] - self.max_tax_free[wyt][project][274]
      else:
        total_taxed_oct_jan = 0.0
        total_taxed_feb_june = 0.0
        total_taxed_july_sept = (365.0 - dowy)*pumping[project] - self.max_tax_free[wyt][project][dowy]
      ###Can we pump more water than the remaining YTD tax-free volume?
      storage_available = max(storage[project] - self.max_tax_free[wyt][project][dowy], 0.0)
      additional_pumping_oct_jan = min(storage_available*self.export_ratio[wyt][0], total_taxed_oct_jan)
      additional_pumping_july_sept = min(max((storage_available - total_taxed_oct_jan/self.export_ratio[wyt][0])*self.export_ratio[wyt][0], 0.0), total_taxed_july_sept)
      additional_pumping_feb_june = min(max((storage_available - (total_taxed_oct_jan + total_taxed_july_sept)/self.export_ratio[wyt][0])*self.export_ratio[wyt][2], 0.0), total_taxed_feb_june)
      forecast_pumping[project] = total_forecast + additional_pumping_oct_jan + additional_pumping_july_sept + additional_pumping_feb_june
      ###Turn pumping toggle off if the storage can be pumped at a lower 'tax' rate later in the year
      if project == 'swp':
        if swpAS < (self.max_tax_free[wyt]['swp'][dowy] + total_taxed_july_sept/self.export_ratio[wyt][0]):
          swp_max = 0.0
      elif project == 'cvp':
        if cvpAS < (self.max_tax_free[wyt]['cvp'][dowy] + total_taxed_july_sept/self.export_ratio[wyt][0]):
          cvp_max = 0.0
    ###Send pumping forecasts to the contract class	
    self.forecastSWPPUMP = forecast_pumping['swp']
    self.forecastCVPPUMP = forecast_pumping['cvp']
	
    #numdaysP0 = max(61 - dowy, 0.0)
    #numdaysP1 = 92 - max(dowy - 274, 0.0)##July-September
    #numdaysP1a = max(62 - max(dowy - 61, 0.0), 0.0)##December - January
    #numdaysP2 = max(59 - max(dowy - 124, 0.0), 0.0)## February, March
    #numdaysP3 = max(61 - max(dowy - 180, 0.0), 0.0)## April, May
    #numdaysP2a = max(30 - max(dowy - 241, 0.0), 0.0)## June

    #totalP0 = min(swpAS, p1_stor_swp*numdaysP0)*self.export_ratio[wyt][8]
    #totalP1a = min(swpAS - p1_stor_swp*numdaysP0, p1_stor_swp*numdaysP1)*self.export_ratio[wyt][8]
    #totalP1 = min(swpAS - p1_stor_swp*(numdaysP1 + numdaysP0), p1_stor_swp*numdaysP1a)*self.export_ratio[wyt][8]
    #totalP2 = min(swpAS - p1_stor_swp*(numdaysP1 + numdaysP1a + numdaysP0), p2_stor_swp*numdaysP2)*self.export_ratio[wyt][2]
    #totalP3 = min(swpAS - p1_stor_swp*(numdaysP1 + numdaysP1a + numdaysP0) - p2_stor_swp*numdaysP2, p3_stor_swp*numdaysP3)*self.export_ratio[wyt][4]
    #totalP2a = min(swpAS - p1_stor_swp*(numdaysP1 + numdaysP1a + numdaysP0) - p2_stor_swp*numdaysP2 - p3_stor_swp*numdaysP3, p2_stor_swp*numdaysP2a)*self.export_ratio[wyt][2]
    #self.forecastSWPPUMP = max(totalP1,0.0) + max(totalP1a,0.0) + max(totalP2,0.0) + max(totalP2a,0.0) + max(totalP3,0.0)

    #totalP0 = min(cvpAS, p1_stor_cvp*numdaysP0)*self.export_ratio[wyt][8]
    #totalP1 = min(cvpAS - p1_stor_cvp*numdaysP0, p1_stor_cvp*numdaysP1)*self.export_ratio[wyt][8]
    #totalP1a = min(cvpAS - p1_stor_cvp*(numdaysP1 + numdaysP0), p1_stor_cvp*numdaysP1a)*self.export_ratio[wyt][8]
    #totalP2 = min(cvpAS - p1_stor_cvp*(numdaysP1 + numdaysP1a + numdaysP0), p2_stor_cvp*numdaysP2)*self.export_ratio[wyt][2]
    #totalP3 = min(cvpAS - p1_stor_cvp*(numdaysP1 + numdaysP1a + numdaysP0) - p2_stor_cvp*numdaysP2, p3_stor_cvp*numdaysP3)*self.export_ratio[wyt][4]
    #totalP2a = min(cvpAS - p1_stor_cvp*(numdaysP1 + numdaysP1a + numdaysP0) - p2_stor_cvp*numdaysP2 - p3_stor_cvp*numdaysP3, p2_stor_cvp*numdaysP2a)*self.export_ratio[wyt][2]
    #self.forecastCVPPUMP = max(totalP1,0.0) + max(totalP1a,0.0) + max(totalP2,0.0) + max(totalP2a,0.0) + max(totalP3,0.0)
        
    return cvp_max, swp_max


  def step(self, t, cvp_flows, swp_flows, swp_pump, cvp_pump, swp_release, cvp_release, swp_AS, cvp_AS):
    ##Takes releases (cvp_flows & swp_flows) and gains, and divides water between delta outflows, CVP exports, and SWP exports (and delta depletions)
	##Basically runs through the operations of calc_flow_bounds, only w/actual reservoir releases
    d = int(self.index.dayofyear[t])
    m = int(self.index.month[t])
    wyt = self.forecastSCWYT
    y = int(self.index.year[t])
    dowy = water_day(d,calendar.isleap(y))

	##Same outflow rule as in calc_flow_bounds
    outflow_rule = self.min_outflow[wyt][m-1] * cfs_tafd
	##Same salinity rule as in calc_flow_bounds
    if dowy > 180 and dowy < 318:
      if self.x2[t-1] > self.x2constraint[wyt][dowy]:
        x2outflow = 10**((self.x2constraint[wyt][dowy] - 10.16 - 0.945*self.x2[t])/(-1.487))
      else:
        x2outflow = 0.0
    else:
      x2outflow = 0.0
		
    salinity_rule = min(x2outflow*cfs_tafd,12000.0*cfs_tafd)

    min_rule = max(outflow_rule, salinity_rule)
    unstored_flows = self.total_inflow
    surplus = unstored_flows + self.depletions[t] - min_rule
    self.surplus[t] = surplus
	#Same export ratio as in calc_weekly_storage_release
    export_ratio = self.export_ratio[wyt][m-1]
	#Same max pumping rules as in calc_weekly_storage release
    cvp_max, swp_max = self.find_max_pumping(d, dowy, t, wyt)
      
    if surplus < 0:
      ##if unstored flows cannot meet delta outflow requirements, 75% of the deficit comes
	  ##from releases made by CVP (25% from SWP releases)
      if self.cvp_outflow + self.swp_outflow > 0.0:	  
        cvp_frac = self.cvp_outflow/(self.cvp_outflow+self.swp_outflow)
        swp_frac = self.swp_outflow/(self.cvp_outflow+self.swp_outflow)
      else:
        cvp_frac = 0.0
        swp_frac = 0.0
    else:
	  ##if unstored flows remain after meeting delta outflow requirements, the additional
	  ##flows are split 55/45 between CVP/SWP
      cvp_frac = 0.55
      swp_frac = 0.45
    tax_free_exports = ((1/(1-self.export_ratio[wyt][m-1])) - 1)*(min_rule - self.depletions[t])

    cvp_surplus_inflow = cvp_flows + cvp_frac * surplus
    swp_surplus_inflow = swp_flows + swp_frac * surplus
    cvp_tax_frac = 0.55
    swp_tax_frac = 0.45
    if cvp_surplus_inflow < cvp_tax_frac*tax_free_exports:
      self.TRP_pump[t] = max(cvp_surplus_inflow, 0.0)
      remaining_tax_free = tax_free_exports - max(cvp_surplus_inflow, 0.0)
      if swp_surplus_inflow > remaining_tax_free:
        self.HRO_pump[t] = remaining_tax_free
      else:
        self.HRO_pump[t] = swp_surplus_inflow
    elif swp_surplus_inflow < swp_tax_frac*tax_free_exports:
      self.HRO_pump[t] = max(swp_surplus_inflow, 0.0)
      remaining_tax_free = tax_free_exports - max(swp_surplus_inflow, 0.0)
      if cvp_surplus_inflow > remaining_tax_free:
        self.TRP_pump[t] = remaining_tax_free
      else:
        self.TRP_pump[t] = cvp_surplus_inflow
    else:
      self.HRO_pump[t] = swp_surplus_inflow
      self.TRP_pump[t] = cvp_surplus_inflow
		
    swp_remaining = swp_flows + swp_frac * surplus - self.HRO_pump[t]
    cvp_remaining = cvp_flows + cvp_frac * surplus - self.TRP_pump[t]

    self.TRP_pump[t] += max(cvp_remaining * export_ratio, 0.0)
    self.HRO_pump[t] += max(swp_remaining * export_ratio, 0.0)

    #self.HRO_pump[t] = max(min((swp_flows + 0.45 * unstored_flows) * export_ratio, swp_flows + swp_frac * surplus),0.0)
    if swp_release == 0 and cvp_release == 1:
      swp_max = max(min(swp_pump - min(cvp_max, self.TRP_pump[t]), swp_max), 0.0)
    elif cvp_release == 0 and swp_release == 1:
      cvp_max = max(min(cvp_pump - min(swp_max, self.HRO_pump[t]), cvp_max), 0.0)
    elif swp_release == 0 and cvp_release == 0:
      swp_max = max(min(swp_pump, swp_max), 0.0)
      cvp_max = max(min(cvp_pump, cvp_max), 0.0)
	
    if self.TRP_pump[t] > cvp_max:
      self.TRP_pump[t] = cvp_max
      self.HRO_pump[t] = max(min(cvp_flows + swp_flows + surplus - self.TRP_pump[t], (cvp_flows + swp_flows + unstored_flows)*export_ratio - self.TRP_pump[t],swp_max),0.0)
  
    if self.HRO_pump[t] > swp_max:
      self.HRO_pump[t] = swp_max
      self.TRP_pump[t] = max(min(cvp_flows + swp_flows + surplus - self.HRO_pump[t], (cvp_flows + swp_flows + unstored_flows)*export_ratio - self.HRO_pump[t],cvp_max),0.0)
    
    if self.TRP_pump[t] < 0.0:
      self.HRO_pump[t] = max(self.HRO_pump[t] + self.TRP_pump[t],0.0)
      self.TRP_pump[t] = 0.0
    elif self.HRO_pump[t] < 0.0:
      self.TRP_pump[t] = max(self.TRP_pump[t] + self.HRO_pump[t],0.0)
      self.HRO_pump[t] = 0.0


	##Same as in calc_weekly_storage_release
    cvp_max, swp_max = self.meet_OMR_requirement(cvp_max, swp_max, t)
    self.TRP_pump[t], self.HRO_pump[t] = self.meet_OMR_requirement(self.TRP_pump[t], self.HRO_pump[t], t)

    self.outflow[t] = cvp_flows + swp_flows + unstored_flows - self.TRP_pump[t] - self.HRO_pump[t] + self.depletions[t]
    if self.outflow[t] > 0.0:
      self.x2[t+1] = 10.16 + 0.945*self.x2[t] - 1.487*np.log10(self.outflow[t]*tafd_cfs)
    else:
      self.x2[t+1] = 10.16 + 0.945*self.x2[t] - 1.487*np.log10(50.0)

	##Calculate X2 values, for salinity rules - note, if outflow is negative (may happen under extreme conditions in which not enough storage to meet negative gains)
	##X2 is calculated w/an outflow of 50 cfs b/c log calcs require positive flow
	  
    self.OMR[t] = self.hist_OMR[t] + self.hist_TRP_pump[t] + self.hist_HRO_pump[t] - self.TRP_pump[t] - self.HRO_pump[t]
    self.calc_project_allocation(t, swp_AS, cvp_AS)
    
  	
  def calc_project_allocation(self,t, SWP_AS, CVP_AS):
    y = int(self.index.year[t])
    m = int(self.index.month[t])
    da = int(self.index.day[t-1])
    startYear = int(self.index.year[0])
    if m < 10:
      wateryear = y -(startYear + 1)
    else:
      wateryear = y - startYear
    if m == 10 and da == 1:
      self.swp_allocation[t] = self.forecastSWPPUMP + self.annual_HRO_pump[wateryear-1]
      self.cvp_allocation[t] = self.forecastCVPPUMP + self.annual_TRP_pump[wateryear-1]
      self.first_empty_day_SWP = 0
      self.first_empty_day_CVP = 0
    else:
      if SWP_AS < 0.0 and self.first_empty_day_SWP == 0:
        self.final_allocation_swp = self.annual_HRO_pump[wateryear-1]
        self.swp_allocation[t] = self.final_allocation_swp
        self.first_empty_day_SWP = 1
      elif SWP_AS < 0.0:
        self.swp_allocation[t] = self.final_allocation_swp
      else:
        self.swp_allocation[t] = self.forecastSWPPUMP + self.annual_HRO_pump[wateryear-1]
	
      if CVP_AS < 0.0 and self.first_empty_day_CVP == 0:
        self.final_allocation_cvp = self.annual_TRP_pump[wateryear-1]
        self.cvp_allocation[t] = self.final_allocation_cvp
        self.first_empty_day_CVP = 1
      elif CVP_AS < 0.0:
        self.cvp_allocation[t] = self.final_allocation_cvp
      else:
        self.cvp_allocation[t] = self.forecastCVPPUMP + self.annual_TRP_pump[wateryear-1]

    self.annual_HRO_pump[wateryear-1] += self.HRO_pump[t]
    self.annual_TRP_pump[wateryear-1] += self.TRP_pump[t]
	  
  def accounting_as_df(self, index):
    df = pd.DataFrame()
    names = ['TRP_pump','HRO_pump', 'total_outflow','SWP_allocation', 'CVP_allocation', 'X2', 'SCINDEX', 'SJINDEX']
    things = [self.TRP_pump, self.HRO_pump, self.outflow, self.swp_allocation, self.cvp_allocation, self.x2, self.forecastSRI, self.forecastSJI]
    for n,t in zip(names,things):
      df['%s_%s' % (self.key,n)] = pd.Series(t, index=index)
    return df