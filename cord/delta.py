from __future__ import division
import numpy as np
import calendar
import matplotlib.pyplot as plt
import pandas as pd
import json
from .util import *

class Delta():

  def __init__(self, df, df_short, key, model_mode):
    self.model_mode = model_mode
    self.T = len(df)
    self.day_year = df.index.dayofyear
    self.day_month = df.index.day
    self.month = df.index.month
    self.year = df.index.year
    self.starting_year = self.year[0]
    self.ending_year = self.year[-1]
    self.number_years = self.ending_year - self.starting_year
    self.dowy = water_day(self.day_year, self.year)
    self.water_year = water_year(self.month, self.year, self.starting_year)
    self.T_short = len(df_short)
    self.short_day_year = df_short.index.dayofyear
    self.short_month = df_short.index.month
    self.short_year = df_short.index.year
    self.short_starting_year = self.short_year[0]
    self.short_ending_year = self.short_year[-1]
    self.short_dowy = water_day(self.short_day_year, self.short_year)
    self.short_water_year = water_year(self.short_month, self.short_year, self.short_starting_year)

    self.leap = leap(np.arange(min(self.year), max(self.year) + 2))
    year_list = np.arange(min(self.year), max(self.year) + 2)
    self.days_in_month = days_in_month(year_list, self.leap)
    self.dowy_eom = dowy_eom(year_list, self.leap)
    self.non_leap_year = first_non_leap_year(self.dowy_eom)


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
    self.vernalis_flow = np.zeros(self.T)
    self.eastside_streams = df.EAST_gains * cfs_tafd
    self.inflow = np.zeros(self.T)
    self.ccc = df.CCC_pump * cfs_tafd
    self.barkerslough = df.BRK_pump *cfs_tafd



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
    self.sac_fnf = np.zeros(self.number_years)
	##Old/Middle River Calculations
    if self.model_mode == 'validation':
      if 'OMR' in df:
        self.hist_OMR = df.OMR * cfs_tafd
        self.hist_TRP_pump = df.TRP_pump * cfs_tafd
        self.hist_HRO_pump = df.HRO_pump * cfs_tafd
        self.omr_record_start = 4440
      else:
        self.omr_record_start = self.T + 1

      self.omr_rule_start = 2007
      self.vamp_rule_start = 2009
    else:
      self.omr_record_start = self.T + 1
      self.omr_rule_start = -1
      self.vamp_rule_start = -1
      self.fish_condition = np.random.random_sample((self.T,))
    self.OMR = np.zeros(self.T)
	
	##Variables for determining releases for export (initialize)
    self.cvp_aval_stor = 0.5
    self.swp_aval_stor = 0.5
    self.cvp_delta_outflow_pct = 0.75
    self.swp_delta_outflow_pct = 0.25
	
    self.swp_allocation = np.zeros(self.T)
    self.cvp_allocation = np.zeros(self.T)
    self.annual_HRO_pump = np.zeros(self.number_years)
    self.annual_TRP_pump = np.zeros(self.number_years)
    self.remaining_tax_free_storage = {}
    self.remaining_tax_free_storage['swp'] = np.zeros(self.T)
    self.remaining_tax_free_storage['cvp'] = np.zeros(self.T)
	
    self.first_empty_day_SWP = 0
    self.first_empty_day_CVP = 0
    self.final_allocation_swp = 0.0
    self.final_allocation_cvp = 0.0

  def set_sensitivity_factors(self, delta_outflow_factor, omr_flow_factor, omr_prob_factor):
    for wyt in ['W', 'AN', 'BN', 'D', 'C']:
      for monthcount in range(0,12):
        self.min_outflow[wyt][monthcount] = self.min_outflow[wyt][monthcount]*delta_outflow_factor
    for omr_threshold in range(0, 4):
      self.omr_reqr['probability'][omr_threshold] = omr_prob_factor*(omr_threshold+1.0)
      self.omr_reqr['shortage_flow'][omr_threshold] = omr_flow_factor - (5000.0 + omr_flow_factor)*omr_threshold/4.0

  def calc_expected_delta_outflow(self,shastaD,orovilleD,yubaD,folsomD,shastaMIN,orovilleMIN,yubaMIN,folsomMIN, gains_sac_short, gains_sj_short, depletions_short, eastside_short):
  #this function calculates an expectation for the volume of environmental releases expected to be made from each reservoir,
  #given the water year type
  #also calculates the dictionary self.max_tax_free - based on delta flow requirements, how much water can be pumped w/o triggering the inflow/export ratio rule at the delta pumps, for each water year type and both the cvp & swp shares
	
    expected_outflow_releases = {}
    self.max_tax_free = {}
    for wyt in ['W', 'AN', 'BN', 'D', 'C']:
      expected_outflow_releases[wyt] = np.zeros(366)
      self.max_tax_free[wyt] = {}
      self.max_tax_free[wyt]['swp'] = np.zeros(366)
      self.max_tax_free[wyt]['cvp'] = np.zeros(366)

    num_obs = np.zeros(366)
    num_obs_m = np.zeros(12)
    total_depletion = np.zeros(12)
    for t in range(1,self.T_short):
      m = self.short_month[t - 1]
      dowy = self.short_dowy[t - 1]
      y = self.short_year[t - 1] - self.short_starting_year
      zone = int(np.interp(dowy, self.san_joaquin_min_flow['d'], self.san_joaquin_min_flow['zone']))
      total_depletion[m-1] += min(depletions_short[t], 0.0)
      num_obs_m[m-1] += 1
      num_obs[dowy] += 1.0
      for wyt in ['W', 'AN', 'BN', 'D', 'C']:
	    ##Calc delta outflow requirements
        outflow_rule = self.min_outflow[wyt][m-1] * cfs_tafd
	    #Calc expected unstored flows
        vernalis_flows = max(gains_sj_short[t],self.san_joaquin_min_flow[wyt][zone-1]* cfs_tafd)
        trib_flow = max(shastaMIN[wyt][m-1]*cfs_tafd,shastaD[t]) + max(orovilleMIN[wyt][m-1]*cfs_tafd,orovilleD[t]) + max(yubaMIN[wyt][m-1]*cfs_tafd,yubaD[t]) + max(folsomMIN[wyt][m-1]*cfs_tafd,folsomD[t])
        #Calc releases needed to meet outflow req.
        expected_outflow_releases[wyt][dowy] += max(outflow_rule - min(gains_sac_short[t], 0.0) - eastside_short[t] - vernalis_flows - min(depletions_short[t], 0.0)*cfs_tafd, 0.0)
	  	  
    #Account for delta depletions - ag use within delta
    self.expected_depletion = np.zeros(12)
    for x in range(0,12):
      self.expected_depletion[x] = total_depletion[x]/num_obs_m[x]
      if x == 3 or x == 4:
        pump_max_cvp = 750.0*cfs_tafd
        pump_max_swp = 750.0*cfs_tafd
      else:
        pump_max_cvp = 4300.0*cfs_tafd
        pump_max_swp = 6680.0*cfs_tafd
		
      #calc pumping limit before inflow/export ratio is met
      for wyt in ['W', 'AN', 'BN', 'D', 'C']:
        #outflow ratio 
        tax_free_pumping = (self.min_outflow[wyt][x]*cfs_tafd - self.expected_depletion[x])*((1/(1-self.export_ratio[wyt][x]))-1)
        if tax_free_pumping*0.55 > pump_max_cvp:
          self.max_tax_free[wyt]['cvp'][0] += pump_max_cvp*self.days_in_month[0][x]
          self.max_tax_free[wyt]['swp'][0] += min(tax_free_pumping - pump_max_cvp, pump_max_swp)*self.days_in_month[0][x]
        else:
          self.max_tax_free[wyt]['cvp'][0] += tax_free_pumping*self.days_in_month[0][x]*0.55
          self.max_tax_free[wyt]['swp'][0] += tax_free_pumping*self.days_in_month[0][x]*0.45
    for x in range(0,365):
      if x > 182 and x < 243:
        pump_max_cvp = 750.0*cfs_tafd
        pump_max_swp = 750.0*cfs_tafd
      else:
        pump_max_cvp = 4300.0*cfs_tafd
        pump_max_swp = 6680.0*cfs_tafd
      m = self.month[x]
	  
      for wyt in ['W', 'AN', 'BN', 'D', 'C']:
        tax_free_pumping = (self.min_outflow[wyt][m-1]*cfs_tafd - self.expected_depletion[m-1])*((1/(1-self.export_ratio[wyt][m-1]))-1)
        if tax_free_pumping*0.55 > pump_max_cvp:
          self.max_tax_free[wyt]['cvp'][x+1] = self.max_tax_free[wyt]['cvp'][x] - pump_max_cvp
          self.max_tax_free[wyt]['swp'][x+1] = self.max_tax_free[wyt]['swp'][x] - min(tax_free_pumping - pump_max_cvp, pump_max_swp)
        else:
          self.max_tax_free[wyt]['cvp'][x+1] = self.max_tax_free[wyt]['cvp'][x] - tax_free_pumping*0.55
          self.max_tax_free[wyt]['swp'][x+1] = self.max_tax_free[wyt]['swp'][x] - tax_free_pumping*0.45
		  
      self.x2_dict = {}
      self.x2_dict['date'] = {}
      self.x2_dict['value'] = {}
      self.x2_dict['date']['W'] = 318.0
      self.x2_dict['date']['AN'] = 274.0
      self.x2_dict['date']['BN'] = 260.0
      self.x2_dict['date']['D'] = 255.0
      self.x2_dict['date']['C'] = 255.0
      self.x2_dict['value']['W'] = 77.0
      self.x2_dict['value']['AN'] = 80.0
      self.x2_dict['value']['BN'] = 80.0
      self.x2_dict['value']['D'] = 89.0
      self.x2_dict['value']['C'] = 90.0

      for wyt in ['W', 'AN', 'BN', 'D', 'C']:
        self.x2constraint[wyt][x] = 90.0
        if wyt == 'C':
          if x < 75:
            self.x2constraint[wyt][x] = 90.0 - 5.0*x/75.0
          elif x < 180:
            self.x2constraint[wyt][x] = 85.0
        else:
          if x < 75:
            self.x2constraint[wyt][x] = 87.5 - 2.5*x/75.0
          elif x < 180:
            self.x2constraint[wyt][x] = 85.0 - 8.0*(x-75)/105.0
          elif x > 334:
            self.x2constraint[wyt][x] = 90.0 - 2.5*(x-334)/31.0
      for wyt in ['W', 'AN', 'BN', 'D', 'C']:
        expected_outflow_releases[wyt][x] = expected_outflow_releases[wyt][x]/num_obs[x]

    return expected_outflow_releases, self.expected_depletion
  
  def calc_rio_vista_rule(self, t, cvp_stored_release, swp_stored_release):
    #maintian flow requirements on teh sacramento at rio vista (i.e., delta inflow)
    m = self.month[t]
    wyt = self.forecastSCWYT
    din = max(self.rio_vista_min[wyt][m-1]*cfs_tafd - (self.rio_gains- cvp_stored_release - swp_stored_release),0.0)
    if din > (cvp_stored_release + swp_stored_release):
      swp_din = 0.25*din - swp_stored_release
      cvp_din = 0.75*din - cvp_stored_release
      if swp_din < 0.0:
        cvp_din += swp_din
        swp_din = 0.0
      if cvp_din < 0.0:
        swp_din += cvp_din
        cvp_din = 0.0
    else:
      cvp_din = 0.0
      swp_din = 0.0
	  
    self.rio_gains += (cvp_din + swp_din)

    return cvp_din, swp_din
	
  def calc_vernalis_rule(self,t,NMI):
    ##Calculates delta rules at Vernalis (San Joaquin/delta confluence)
    d = self.day_year[t]
    y = self.year[t]
    m = self.month[t]
    wyt = self.forecastSJWYT
    dowy = self.dowy[t]

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
      if y < self.vamp_rule_start:
        vamp_pulse = max(self.vamp_rule(self.vernalis_gains) - self.vernalis_gains - d_1641_flow,0.0)
        merced_contr = vamp_pulse*0.5
        tuolumne_contr = vamp_pulse*0.5
        stanislaus_contr = d_1641_flow
      else:
        vamp_pulse = max(self.new_vamp_rule[wyt]*cfs_tafd - self.vernalis_gains - d_1641_flow,0.0)
        merced_contr = vamp_pulse*0.5
        tuolumne_contr = vamp_pulse*0.5
        stanislaus_contr = d_1641_flow     
    else:
      vamp_pulse = 0.0
      stanislaus_contr = d_1641_flow
      merced_contr = 0.0
      tuolumne_contr = 0.0
    
	##BIOPS RULES for Vernalis start in 2009, before then only d_1641 rule is used
    if y > self.vamp_rule_start:
      #biops_min = np.interp(dowy,self.san_joaquin_min['biops_d'],self.san_joaquin_min['biops_on_off'])*np.interp(NMI,self.san_joaquin_min['biops_NMI'],self.san_joaquin_min['biops_flow']) * cfs_tafd
      biops_min = 0.0
    else:
      biops_min = 0.0
	
    ##BIOPS Releases are only made from New Melones (CVP reservoir)
    #if biops_min > d_1641_min:
      #stanislaus_contr += max(biops_min-self.vernalis_gains,0.0) - max(max(d_1641_min,vamp_pulse)-self.vernalis_gains,0.0)
	
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
    m = self.month[t]
    wyt = self.forecastSCWYT
    dowy = self.dowy[t]
    #this function finds the additional releases needed to satisfy delta outflows
	#and splits them between CVP and SWP based on the 75/25 rule (given previous releases)
	
    #delta outflow minimum either salinity rule or delta outflow volume
    outflow_rule = self.min_outflow[wyt][m-1] * cfs_tafd

    if dowy > 180 and dowy < self.x2_dict['date'][wyt]:
      self.x2constraint[wyt][dowy] = self.x2[t-1] + (77.0 - self.x2[t-1])*(dowy-180.0)/(self.x2_dict['date'][wyt] - 180.0)
    elif dowy > self.x2_dict['date'][wyt] and dowy < 318:
      self.x2constraint[wyt][dowy] = self.x2[t-1] + (self.x2_dict['value'][wyt] - self.x2[t-1])*(dowy-self.x2_dict['date'][wyt])/(318.0 - self.x2_dict['date'][wyt])
    if wyt == 'C' and dowy > 180 and dowy < 255:
      self.x2constraint[wyt][dowy] = 85.0
    
    if self.x2[t] > self.x2constraint[wyt][dowy]:
      x2outflow = 10**((self.x2constraint[wyt][dowy] - 10.16 - 0.945*self.x2[t])/(-1.487))
    else:
      x2outflow = 0.0
		
    salinity_rule = min(x2outflow*cfs_tafd,11400.0*cfs_tafd)  
    min_rule = max(outflow_rule, salinity_rule)
	
	#this minimum dout release does not account for cvp_stored_release or swp_stored_release
    dout = max(min_rule - self.depletions[t] - (self.total_inflow - cvp_stored_release - swp_stored_release),0.0)
    
    #only release extra is dout is bigger than what has already been released (for envmin & rio vista requirements)
    if dout > (cvp_stored_release + swp_stored_release):
      swp_dout = 0.25*dout - swp_stored_release
      cvp_dout = 0.75*dout - cvp_stored_release
      if swp_dout < 0.0:
        cvp_dout += swp_dout
        swp_dout = 0.0
      if cvp_dout < 0.0:
        swp_dout += cvp_dout
        cvp_dout = 0.0
    else:
      cvp_dout = 0.0
      swp_dout = 0.0
	  
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
    wyt = self.forecastSCWYT
    dowy = self.dowy[t]

    ####Old-Middle River Rule################################################################################################
	#The delta pumps make the old-middle river run backwards - there are restrictions (starting in 2008) about how big the negative flows can
	#become.  To model this, we use either a liner adjustment of flow at vernalis, or the observed flow (adding back in the pumping, to estimate
	#the 'natural' flow on the Old-Middle Rivers).  Once we have a model of the Old-Middle River, we assume that this flow is reduced (can become negative)
	# by 90% of the total pumping.  So, if the OMR limit is -5000CFS, & the natural flow is 1000CFS, pumping can be, maximum, 6000CFS/0.9
    if t > self.omr_record_start:
      omrNat = self.hist_OMR[t] + (self.hist_TRP_pump[t] + self.hist_HRO_pump[t])*.94
      pumping_coef = 0.94
    else:
      if self.vernalis_gains < 16000.0*cfs_tafd:
        omrNat = self.vernalis_gains*0.471 + 83.0*cfs_tafd
        pumping_coef = 0.911
      elif self.vernalis_gains < 28000.0*cfs_tafd:
        omrNat = self.vernalis_gains*0.681 - 3008.0*cfs_tafd
        pumping_coef = 0.94
      else:
        omrNat = self.vernalis_gains*0.633 - 1644.0*cfs_tafd
        pumping_coef = 0.94
	  
    ## OMR max negative flows are only binding Jan-June, the rest of the year flow can be anything
    omr_condition = np.interp(dowy, self.omr_reqr['d'], self.omr_reqr['flow']) * cfs_tafd
    omr_condition_2 = np.interp(dowy, self.omr_addition['d'], self.omr_addition[wyt]) * cfs_tafd
	##The OMR constraints are governed by fish-kill conditions at the pumps.  negative 5000 CFS is normal, but can also be reduced
	##here we use the actual declaration - any forward-in-time projection runs will have to be either simulated probabilistically or just run under
	##the normal condition (5000 cfs)
	###Note: OMR Flow adjustments come from here: http://www.water.ca.gov/swp/operationscontrol/calfed/calfedwomt.cfm
    if self.model_mode == 'validation':
      fish_trigger_adj = np.interp(t, self.omr_reqr['t'], self.omr_reqr['adjustment']) * cfs_tafd
    elif dowy > 92 and dowy < 258:
      if self.fish_condition[t] < self.omr_reqr['probability'][0]:
        fish_trigger_adj = self.omr_reqr['shortage_flow'][0] *cfs_tafd
      elif self.fish_condition[t] < self.omr_reqr['probability'][1]:
        fish_trigger_adj = self.omr_reqr['shortage_flow'][1] *cfs_tafd
      elif self.fish_condition[t] < self.omr_reqr['probability'][2]:
        fish_trigger_adj = self.omr_reqr['shortage_flow'][2] *cfs_tafd
      elif self.fish_condition[t] < self.omr_reqr['probability'][3]:
        fish_trigger_adj = self.omr_reqr['shortage_flow'][3] *cfs_tafd
      else:
        fish_trigger_adj = -9999999.0
    else:
      fish_trigger_adj = -9999999.0
	  
    if self.year[t] < self.omr_rule_start:
      omrRequirement = fish_trigger_adj
    elif self.year[t] == self.omr_rule_start and self.month[t] < 12:
      omrRequirement = fish_trigger_adj
    else:
      omrRequirement = max(omr_condition, omr_condition_2, fish_trigger_adj)
    
    maxTotPump = max((omrNat - omrRequirement)/pumping_coef, 0.0)
    	
    #project_ratio = self.pump_max['swp']['intake_limit'][0]/(self.pump_max['cvp']['intake_limit'][0] + self.pump_max['swp']['intake_limit'][0])
    project_ratio = 0.5
    if cvp_m + swp_m > maxTotPump:
      if cvp_m < maxTotPump*(1.0 - project_ratio):
        swp_m = maxTotPump - cvp_m
      elif swp_m < maxTotPump*(project_ratio):
        cvp_m = maxTotPump - swp_m
      else:
        swp_m = maxTotPump*(project_ratio)
        cvp_m = maxTotPump*(1.0 - project_ratio)
		
    return cvp_m, swp_m
	

  def hypothetical_pumping(self, capacity_max, supply_max, pump_trigger, fraction, t):
    m = self.month[t]
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

  def distribute_export_releases(self, t, pump_max, sodd_tot, flood_storage_1, flood_storage_2, available_storage_1, available_storage_2):
    total_flood_storage = max(flood_storage_1, 0.0) + max(flood_storage_2, 0.0)
    total_available_storage = max(available_storage_1, 0.0) + max(available_storage_2, 0.0)
    if total_available_storage > 0.0:
      if total_flood_storage > total_available_storage:
        main_sodd = sodd_tot*max(flood_storage_1, 0.0)/total_flood_storage
        secondary_sodd = sodd_tot*max(flood_storage_2, 0.0)/total_flood_storage
      else:
        main_sodd = sodd_tot*max(available_storage_1,0.0)/total_available_storage
        secondary_sodd = sodd_tot*max(available_storage_2,0.0)/total_available_storage
    elif total_flood_storage > 0.0:
      main_sodd = sodd_tot*max(flood_storage_1, 0.0)/total_flood_storage
      secondary_sodd = sodd_tot*max(flood_storage_2, 0.0)/total_flood_storage
    else:
      main_sodd = sodd_tot
      secondary_sodd = 0.0
	  
    return main_sodd, secondary_sodd
	
  def calc_flow_bounds(self, t, cvp_max, swp_max, cvp_max_alt, swp_max_alt, cvp_release, swp_release, cvp_AS, swp_AS, cvp_flood, swp_flood, swp_over_dead_pool, cvp_over_dead_pool, swp_flood_volume, cvp_flood_volume):
    ### stored and unstored flow agreement between SWP & CVP
	### project releases for pumping must consider the I/E 'tax'
	### releases already made (environmental flows, delta outflows) and downstream gains can be credited against this tax, but
	### we first have to determine how much of each is assigned to the delta outflow.
    
	##the first step is applying all 'unstored' flows to the delta outflows
	##note: unstored_flows should be strictly positive, but available_unstored can be negative (need outflow/environmental releases to meet delta outflow requirements)
    d = self.day_year[t]
    m = self.month[t]
    wyt = self.forecastSCWYT
    dowy = self.dowy[t]
    year = self.year[t] - self.starting_year
    outflow_rule = self.min_outflow[wyt][m-1] * cfs_tafd
    cvp_frac = 0.55
    swp_frac = 0.45
	##Same salinity rule as in calc_flow_bounds
	  
    if self.x2[t] > self.x2constraint[wyt][dowy]:
      x2outflow = 10**((self.x2constraint[wyt][dowy] - 10.16 - 0.945*self.x2[t])/(-1.487))
    else:
      x2outflow = 0.0
		
    salinity_rule = min(x2outflow*cfs_tafd,11400.0*cfs_tafd)

    min_rule = max(outflow_rule, salinity_rule)
    unstored_flows = self.total_inflow
    available_unstored = unstored_flows + self.depletions[t] - min_rule
	
    #total volume that can be exported w/o additional inflows, based on delta required outflows & the E/I ratio (i.e., if enough inflow is coming into the delta to meet the minimum outflow requirements, how much (additional) inflows can we export before we hit the I/E ratio)
    tax_free_exports = ((1/(1-self.export_ratio[wyt][m-1])) - 1)*(min_rule - self.depletions[t])
    tax_free_exports = min(tax_free_exports, (np.interp(d, self.pump_max['swp']['d'], self.pump_max['swp']['intake_limit']) + np.interp(d, self.pump_max['cvp']['d'], self.pump_max['cvp']['intake_limit']))*cfs_tafd)
	
    #total expected remaining 'tax free' flows for the rest of the year, based on meeting min outflow requirements
    tax_free_available = self.max_tax_free[wyt]['cvp'][dowy] + self.max_tax_free[wyt]['swp'][dowy]#from this date until the end of the year
    tax_free_flood = max(self.max_tax_free[wyt]['cvp'][dowy] + self.max_tax_free[wyt]['swp'][dowy] - self.max_tax_free[wyt]['cvp'][self.dowy_eom[year][3]] - self.max_tax_free[wyt]['swp'][self.dowy_eom[year][3]], 1.0)#from this date until the end of the 'flood control' season (April 1)
    tax_free_oct_nov = max(self.max_tax_free[wyt]['cvp'][dowy] + self.max_tax_free[wyt]['swp'][dowy] - self.max_tax_free[wyt]['cvp'][self.dowy_eom[year][10]] - self.max_tax_free[wyt]['swp'][self.dowy_eom[year][10]], 1.0) #from this date until the end of november (i.e. baseflow period before reservoir refil usually begins)

	  
      #is there room in the state portion of San Luis Reservoir?
      #state water project releases are the same as central valley project, but there is an additional 'saved water' supplement from lake oroville.  The end-of-the-year target at oroville tries to save 50% of the beginning of the year storage over 1MAF - so if there were 1.5 MAF at the beginning of the year, we'd aim for 1.25MAF at teh end of the eyar.  that extra 'saved' water of 0.25MAF can be used in dry and critical years to pump water - as long as its only up to the 'tax
    if cvp_release > 0:
      cvp_tax_free_fraction = min(max(cvp_flood_volume/tax_free_available, cvp_AS/tax_free_available, 0.0), 1.0)
    else:
      cvp_tax_free_fraction = min(max(cvp_flood_volume/tax_free_available, 0.0), 1.0)

    if swp_release > 0:
      swp_tax_free_fraction = min(max(swp_flood_volume/tax_free_available, swp_AS/tax_free_available, swp_over_dead_pool/tax_free_available, 0.0), 1.0)
    else:
      swp_tax_free_fraction = min(max(swp_flood_volume/tax_free_available, 0.0), 1.0)


	#how much of the 'tax-free' pumping space can be used by the CVP?  
    cvp_portion = min(max(cvp_frac*tax_free_exports, tax_free_exports - min(max(swp_tax_free_fraction*tax_free_exports, swp_frac*available_unstored), swp_max_alt)), cvp_tax_free_fraction*tax_free_exports)

    cvp_tax_free_pumping = min(cvp_portion, cvp_max_alt)

	#how much of hte 'tax-free' pumping space can be used by the SWP?
    swp_portion = min(max(swp_frac*tax_free_exports, tax_free_exports - min(max(cvp_tax_free_fraction*tax_free_exports, cvp_frac*available_unstored), cvp_max_alt)), swp_tax_free_fraction*tax_free_exports)
    swp_tax_free_pumping = min(swp_portion, swp_max_alt)
	
    cvp_tax_free_pumping, swp_tax_free_pumping = self.meet_OMR_requirement(cvp_tax_free_pumping, swp_tax_free_pumping, t)

	##how many releases are needed for the 'untaxed exports' (i.e. water balance) - given delta gains
    cvp_flood_constraint =  min(cvp_flood, max(cvp_max_alt - cvp_frac*available_unstored, cvp_max_alt/self.export_ratio[wyt][m-1] - cvp_frac*unstored_flows))
    swp_flood_constraint = min(swp_flood, max(swp_max_alt - swp_frac*available_unstored, swp_max_alt/self.export_ratio[wyt][m-1] - swp_frac*unstored_flows))
    cvp_releases = max(max(cvp_tax_free_pumping, cvp_max) - cvp_frac*available_unstored, cvp_flood_constraint)
    swp_releases = max(max(swp_tax_free_pumping, swp_max) - swp_frac*available_unstored, swp_flood_constraint)
   
    ##unused flows from one project can be used to meet requirements for other project
    ##(i.e., if large stored releases (for environmental requirements) made from one project,
	##they may be greater than the total pumping/tax requirement, meaning the other project can
	##pump some of that water or use it to meet the 'tax'
    swp_releases += min(cvp_releases, 0.0)
    cvp_releases += min(swp_releases, 0.0)
    swp_releases = max(swp_releases, 0.0)
    cvp_releases = max(cvp_releases, 0.0)

	##how much (if any) do we need to release to meet the I/E tax? (i.e. environmental requirements)
	##unstored_flows is always positive, so we split them 55/45 to make the 'tax' on each project pumping
    cvp_tax = max(cvp_tax_free_pumping, cvp_max)/self.export_ratio[wyt][m-1] - cvp_frac*unstored_flows
    swp_tax = max(swp_tax_free_pumping, swp_max)/self.export_ratio[wyt][m-1] - swp_frac*unstored_flows


    ##unused flows from one project can be used to meet requirements for other project
    ##(i.e., if large stored releases (for environmental requirements) made from one project,
	##they may be greater than the total pumping/tax requirement, meaning the other project can
	##pump some of that water or use it to meet the 'tax'
    swp_tax += min(cvp_tax, 0.0)
    cvp_tax += min(swp_tax, 0.0)
    swp_tax = max(swp_tax, 0.0)
    cvp_tax = max(cvp_tax, 0.0)

	##need to release the larger of the three requirements
    self.sodd_cvp[t] = max(cvp_releases, cvp_tax)
    self.sodd_swp[t] = max(swp_releases, swp_tax)    
		  
  def find_max_pumping(self, d, dowy, t, wyt):
    ##Find max pumping uses the delta pumping rules (from delta_properties) to find the maximum the pumps can
	##be run on a given day, from the D1641 and the BIOPS rules
    swp_intake_max = np.interp(d, self.pump_max['swp']['d'], self.pump_max['swp']['intake_limit']) * cfs_tafd
    swp_intake_max = max(swp_intake_max, np.interp(d, self.pump_max['swp']['d'], self.pump_max['swp']['vernalis_trigger'])*self.vernalis_gains/2.0, 0.0)
    cvp_intake_max = np.interp(d, self.pump_max['cvp']['d'],self.pump_max['cvp']['intake_limit']) * cfs_tafd
    cvp_intake_max = max(cvp_intake_max, np.interp(d, self.pump_max['cvp']['d'], self.pump_max['cvp']['vernalis_trigger'])*self.vernalis_gains/2.0, 0.0)

    san_joaquin_adj = np.interp(dowy, self.san_joaquin_add['d'], self.san_joaquin_add['mult']) * max(self.vernalis_gains, 0.0)
    if np.interp(t,self.d_1641_export['D1641_dates'],self.d_1641_export['D1641_on_off']) == 1:
      san_joaquin_ie_amt = np.interp(self.vernalis_gains*tafd_cfs, self.d_1641_export['flow_target'],self.d_1641_export['export_limit']) * cfs_tafd
      san_joaquin_ie_used = np.interp(dowy, self.d_1641_export['d'], self.d_1641_export['on_off'])
    else:
      if self.vernalis_gains < 6000.0*cfs_tafd:
        san_joaquin_ie_amt = 1500.0*cfs_tafd
      else:
        san_joaquin_ie_amt = np.interp(self.vernalis_gains*tafd_cfs, self.san_joaquin_export_ratio['flow'], self.san_joaquin_export_ratio['ratio']) * self.vernalis_gains
      san_joaquin_ie_used = np.interp(dowy, self.san_joaquin_export_ratio['d'], self.san_joaquin_export_ratio['on_off'])
	  
    san_joaquin_ie = san_joaquin_ie_amt * san_joaquin_ie_used
    if san_joaquin_ie_used > 0.0:
      swp_max = min(san_joaquin_ie * 0.5, np.interp(d, self.pump_max['swp']['d'], self.pump_max['swp']['pmax']) * cfs_tafd)
      cvp_max = min(san_joaquin_ie * 0.5, np.interp(d, self.pump_max['cvp']['d'], self.pump_max['cvp']['pmax']) * cfs_tafd)
    else:
      swp_max = min(swp_intake_max + san_joaquin_adj, np.interp(d, self.pump_max['swp']['d'], self.pump_max['swp']['pmax']) * cfs_tafd)
      cvp_max = min(cvp_intake_max, np.interp(d, self.pump_max['cvp']['d'], self.pump_max['cvp']['pmax']) * cfs_tafd)
	
    return cvp_max, swp_max
   	  
  # def find_release_flood_prep(self, m, dowy, proj_surplus, numdays, min_release, key):
  #   dowy_md = [122, 150, 181, 211, 242, 272, 303, 334, 365, 31, 60, 91]
  #   month_evaluate = m - 1
  #   if numdays < 366.0:
  #     numday_counter = numdays
  #     this_month_days = dowy_md[month_evaluate] - dowy
  #     total_gains = 0.0
  #     gains_before_spill = proj_surplus[key][month_evaluate]*max(this_month_days,numdays)/self.days_in_month[month_evaluate]
  #     numday_counter -= this_month_days
  #     month_evaluate += 1
  #     while numday_counter > 0:
  #       if month_evaluate > 11:
  #         month_evaluate -= 12
  #       gains_before_spill = proj_surplus[key][month_evaluate]*min(numday_counter/self.days_in_month[month_evaluate], 1.0)
  #       numday_counter -= self.days_in_month[month_evaluate]
  #       month_evaluate += 1
  #     if numdays < 7.0:
  #       average_gains = self.pump_max[key]['intake_limit'][0]*cfs_tafd
  #     else:
  #       average_gains = proj_surplus[key][m-1]/self.days_in_month[m-1]
  #     if average_gains + min_release > self.pump_max[key]['intake_limit'][0]*cfs_tafd:
  #       flood_prep_release = 1.0
  #     else:
  #       flood_prep_release = 0.0
  #   else:
  #     flood_prep_release = 0.0
  #
  #   return flood_prep_release

  def find_release(self, t, m, dowy, cvp_max, swp_max, cvpAS, swpAS, cvp_release, swp_release, proj_surplus, max_pumping):
  ###This function looks at how much water is available in storage & snowpack to be exported,
  ##then determines when the best time to release that water is (water is saved for part of year
  ##when the inflow/export 'tax' is lowest)
    wyt = self.forecastSCWYT
    year = self.year[t] - self.starting_year
    pumping = {}
	###Maximum pumping capacity for each project, ceiling on projected exports
    pumping['swp']	= self.pump_max['swp']['intake_limit'][5] * cfs_tafd
    pumping['cvp'] = self.pump_max['cvp']['intake_limit'][5] * cfs_tafd
    storage = {}
    flood_release = {}
    forecast_pumping = {}
	###available storage determined from reservoir class
    storage['swp'] = swpAS
    storage['cvp'] = cvpAS
    for project in ['cvp', 'swp']:
      self.remaining_tax_free_storage[project][t] = self.max_tax_free[wyt][project][dowy]

      ######The floor for pumping projections are the amount of available storage (including flow projections) in project
	  ######reservoirs, or the available 'tax free' pumping remaining that is caused by the delta E/I ratio not being binding due to 
      ######delta outflow/depletion requirements	  
      total_forecast = min(storage[project], self.max_tax_free[wyt][project][dowy])
      taxable_space = 0.0
      taxable_space2 = 0.0
	  ###Remaining available storage is pumped during the period with the lowest remaining E/I ratio 'tax'
      monthcounter = m - 1        
      running_storage = storage[project]
      running_days = self.dowy_eom[year][monthcounter] - dowy

      if monthcounter == 3 or monthcounter == 4:
        pumping['swp']	= self.pump_max['swp']['intake_limit'][2] * cfs_tafd
        pumping['cvp'] = self.pump_max['cvp']['intake_limit'][2] * cfs_tafd
      else:
        pumping['swp']	= self.pump_max['swp']['intake_limit'][5] * cfs_tafd
        pumping['cvp'] = self.pump_max['cvp']['intake_limit'][5] * cfs_tafd
      if self.year[t] > self.omr_rule_start:
        pumping['swp'] = min(pumping['swp'], max_pumping['swp'][monthcounter]/self.days_in_month[year][monthcounter])
        pumping['cvp'] = min(pumping['cvp'], max_pumping['cvp'][monthcounter]/self.days_in_month[year][monthcounter])
      if self.year[t] == self.omr_rule_start and m == 12:
        pumping['swp'] = min(pumping['swp'], max_pumping['swp'][monthcounter]/self.days_in_month[year][monthcounter])
        pumping['cvp'] = min(pumping['cvp'], max_pumping['cvp'][monthcounter]/self.days_in_month[year][monthcounter])


      #total water available for pumping that isn't stored in reservoir (river gains)
      total_uncontrolled = proj_surplus[project][monthcounter]*running_days/self.days_in_month[year][monthcounter]
      #water available to pump w/o exceeding the I/E tax
      untaxed_releases = max(self.max_tax_free[wyt][project][dowy] - self.max_tax_free[wyt][project][self.dowy_eom[year][monthcounter]+1] - total_uncontrolled, 0.0)
      #total pumping from uncontrolled or untaxed flows
      if monthcounter == 7 or monthcounter == 8:
        untaxed = min(total_uncontrolled + min(running_storage, untaxed_releases), pumping[project]*running_days)
      else:
        untaxed = min(total_uncontrolled + min(running_storage, untaxed_releases), pumping[project]*running_days)
	  ##space for pumping that exceeds the I/E tax
      ############################
	  #if monthcounter > 5 or monthcounter == 0:
        #taxable_space += max(pumping[project]*running_days - untaxed, 0.0)
      #elif monthcounter > 0 and monthcounter < 3:
        #taxable_space2 += max(pumping[project]*running_days - untaxed, 0.0)
      #elif monthcounter == 5:
        #taxable_space2 += max(pumping[project]*running_days - untaxed, 0.0)
      #update running storage
      #running_storage -= min(running_storage, untaxed_releases)
      monthcounter += 1
      if monthcounter == 12:
        monthcounter -= 12
      cross_counter_y = 0
      for x in range(0,12):
        if monthcounter == 9:
          break
        if monthcounter == 0:
          cross_counter_y = 1
        if monthcounter == 3 or monthcounter == 4:
          pumping['swp'] = self.pump_max['swp']['intake_limit'][2] * cfs_tafd
          pumping['cvp'] = self.pump_max['cvp']['intake_limit'][2] * cfs_tafd
        else:
          pumping['swp'] = self.pump_max['swp']['intake_limit'][5] * cfs_tafd
          pumping['cvp'] = self.pump_max['cvp']['intake_limit'][5] * cfs_tafd
		  
        running_days += self.days_in_month[year+cross_counter_y][monthcounter]
        if self.year[t] > self.omr_rule_start:
          pumping['swp'] = min(pumping['swp'], max_pumping['swp'][monthcounter]/self.days_in_month[year+cross_counter_y][monthcounter])
          pumping['cvp'] = min(pumping['cvp'], max_pumping['cvp'][monthcounter]/self.days_in_month[year+cross_counter_y][monthcounter])
        if self.year[t] == self.omr_rule_start and m == 12:
          pumping['swp'] = min(pumping['swp'], max_pumping['swp'][monthcounter]/self.days_in_month[year+cross_counter_y][monthcounter])
          pumping['cvp'] = min(pumping['cvp'], max_pumping['cvp'][monthcounter]/self.days_in_month[year+cross_counter_y][monthcounter])

        #total water available for pumping that isn't stored in reservoir (river gains)
        total_uncontrolled = proj_surplus[project][monthcounter]
        #water available to pump w/o exceeding the I/E tax
        dowy_begin = self.dowy_eom[year+cross_counter_y][monthcounter] - self.days_in_month[year+cross_counter_y][monthcounter]
        dowy_end = self.dowy_eom[year+cross_counter_y][monthcounter]
        untaxed_releases = max(self.max_tax_free[wyt][project][dowy_begin] - self.max_tax_free[wyt][project][dowy_end+1] - total_uncontrolled, 0.0)
        #total pumping from uncontrolled or untaxed flows
        if monthcounter == 7 or monthcounter == 8:
          untaxed += min(total_uncontrolled + min(running_storage, untaxed_releases), pumping[project]*self.days_in_month[year+cross_counter_y][monthcounter])
        else:
          untaxed += min(total_uncontrolled + min(running_storage, untaxed_releases), pumping[project]*self.days_in_month[year+cross_counter_y][monthcounter])
	    ##space for pumping that exceeds the I/E tax
		#########
        #if monthcounter > 5 or monthcounter == 0:
          #taxable_space += max(pumping[project]*self.days_in_month[year+cross_counter_y][monthcounter] - untaxed, 0.0)
        #elif monthcounter > 0 and monthcounter < 3:
          #taxable_space2 += max(pumping[project]*self.days_in_month[year+cross_counter_y][monthcounter] - untaxed, 0.0)
        #elif monthcounter == 5:
          #taxable_space2 += max(pumping[project]*self.days_in_month[year+cross_counter_y][monthcounter] - untaxed, 0.0)
        #update running storage
        running_storage -= min(running_storage, untaxed_releases)
        monthcounter += 1
        if monthcounter == 12:
          monthcounter -= 12


		  
      if running_storage > 0.0:
        if project == 'swp':
          #self.forecastSWPPUMP = untaxed + max(min(taxable_space, running_storage*self.export_ratio[wyt][0]), 0.0) + max(min(taxable_space2, (running_storage - taxable_space/self.export_ratio[wyt][0])*self.export_ratio[wyt][1]), 0.0)
          self.forecastSWPPUMP = untaxed
        elif project == 'cvp':
          #self.forecastCVPPUMP = untaxed + max(min(taxable_space, running_storage*self.export_ratio[wyt][0]), 0.0) + max(min(taxable_space2, (running_storage - taxable_space/self.export_ratio[wyt][0])*self.export_ratio[wyt][1]), 0.0)
          self.forecastCVPPUMP = untaxed

      else:
        if project == 'swp':
          self.forecastSWPPUMP = untaxed
        elif project == 'cvp':
          self.forecastCVPPUMP = untaxed        
		
      #if dowy < 123:
        ##E/I ratio is 0.65 duing oct-jan, 0.35 during feb-jun, and 0.65 from july-oct
        #total_taxed_oct_jan = (123.0 - dowy)*pumping[project] - (self.max_tax_free[wyt][project][dowy] - self.max_tax_free[wyt][project][122])
        #total_taxed_feb_june = 150.0*pumping[project] - (self.max_tax_free[wyt][project][123] - self.max_tax_free[wyt][project][273])
        #total_taxed_july_sept = 92.0*pumping[project] - self.max_tax_free[wyt][project][274]
      #elif dowy < 274:
        #total_taxed_oct_jan = 0.0
        #total_taxed_feb_june = (273.0 - dowy)*pumping[project] - (self.max_tax_free[wyt][project][dowy] - self.max_tax_free[wyt][project][273])
        #total_taxed_july_sept = 92.0*pumping[project] - self.max_tax_free[wyt][project][274]
     # else:
        #total_taxed_oct_jan = 0.0
        #total_taxed_feb_june = 0.0
        #total_taxed_july_sept = (365.0 - dowy)*pumping[project] - self.max_tax_free[wyt][project][dowy]
      ###Can we pump more water than the remaining YTD tax-free volume?
      #storage_available = max(storage[project] - self.max_tax_free[wyt][project][dowy], 0.0)
      #additional_pumping_oct_jan = min(storage_available*self.export_ratio[wyt][0], total_taxed_oct_jan)
      #additional_pumping_july_sept = min(max((storage_available - total_taxed_oct_jan/self.export_ratio[wyt][0])*self.export_ratio[wyt][0], 0.0), total_taxed_july_sept)
      #additional_pumping_feb_june = min(max((storage_available - (total_taxed_oct_jan + total_taxed_july_sept)/self.export_ratio[wyt][0])*self.export_ratio[wyt][2], 0.0), total_taxed_feb_june)
      #forecast_pumping[project] = total_forecast + additional_pumping_oct_jan + additional_pumping_july_sept + additional_pumping_feb_june
      ###Turn pumping toggle off if the storage can be pumped at a lower 'tax' rate later in the year
      #next_year_tax_free = self.max_tax_free[wyt][project][0] - self.max_tax_free[wyt][project][123]
      if project == 'swp':
        if swp_release == 0:
          swp_max = 0.0
        else:
          if swpAS < max(self.max_tax_free[wyt]['swp'][dowy], pumping['swp']):
            swp_max = 0.0
        
      elif project == 'cvp':
        if cvp_release == 0:
          cvp_max = 0.0
        else:
          if cvpAS < max(self.max_tax_free[wyt]['cvp'][dowy], pumping['cvp']):
            cvp_max = 0.0
    ###Send pumping forecasts to the contract class	
    #self.forecastSWPPUMP = forecast_pumping['swp']
    #self.forecastCVPPUMP = forecast_pumping['cvp']
    return cvp_max, swp_max


  def step(self, t, cvp_flows, swp_flows, swp_pump, cvp_pump, swp_AS, cvp_AS):
    ##Takes releases (cvp_flows & swp_flows) and gains, and divides water between delta outflows, CVP exports, and SWP exports (and delta depletions)
	##Basically runs through the operations of calc_flow_bounds, only w/actual reservoir releases
    d = self.day_year[t]
    m = self.month[t]
    wyt = self.forecastSCWYT
    dowy = self.dowy[t]
    cvp_frac = 0.55
    swp_frac = 0.45

	##Same outflow rule as in calc_flow_bounds
    outflow_rule = self.min_outflow[wyt][m-1] * cfs_tafd
	##Same salinity rule as in calc_flow_bounds
    if self.x2[t] > self.x2constraint[wyt][dowy]:
      x2outflow = 10**((self.x2constraint[wyt][dowy] - 10.16 - 0.945*self.x2[t])/(-1.487))
    else:
      x2outflow = 0.0
    salinity_rule = min(x2outflow*cfs_tafd,11400.0*cfs_tafd)

    min_rule = max(outflow_rule, salinity_rule)
    unstored_flows = self.total_inflow
    surplus = unstored_flows + self.depletions[t] - min_rule	
    self.surplus[t] = surplus
	#Same export ratio as in calc_weekly_storage_release
    export_ratio = self.export_ratio[wyt][m-1]
	#Same max pumping rules as in calc_weekly_storage release
    cvp_max, swp_max = self.find_max_pumping(d, dowy, t, wyt)
      
    tax_free_exports = ((1/(1-self.export_ratio[wyt][m-1])) - 1)*(min_rule - self.depletions[t])
    tax_free_exports = min(tax_free_exports, (np.interp(d, self.pump_max['swp']['d'], self.pump_max['swp']['intake_limit']) + np.interp(d, self.pump_max['cvp']['d'], self.pump_max['cvp']['intake_limit']))*cfs_tafd)

    cvp_surplus_inflow = cvp_flows + cvp_frac * surplus
    swp_surplus_inflow = swp_flows + swp_frac * surplus
    if cvp_surplus_inflow < cvp_frac*tax_free_exports:
      self.TRP_pump[t] = max(cvp_surplus_inflow, 0.0)
      remaining_tax_free = tax_free_exports - max(cvp_surplus_inflow, 0.0)
      if swp_surplus_inflow > remaining_tax_free:
        self.HRO_pump[t] = remaining_tax_free
      else:
        self.HRO_pump[t] = swp_surplus_inflow
    elif swp_surplus_inflow < swp_frac*tax_free_exports:
      self.HRO_pump[t] = max(swp_surplus_inflow, 0.0)
      remaining_tax_free = tax_free_exports - max(swp_surplus_inflow, 0.0)
      if cvp_surplus_inflow > remaining_tax_free:
        self.TRP_pump[t] = remaining_tax_free
      else:
        self.TRP_pump[t] = cvp_surplus_inflow
    else:
      self.HRO_pump[t] = swp_surplus_inflow
      self.TRP_pump[t] = cvp_surplus_inflow
		
    swp_remaining = swp_flows  + swp_frac * surplus - self.HRO_pump[t]
    cvp_remaining = cvp_flows  + cvp_frac * surplus - self.TRP_pump[t]
	
    self.TRP_pump[t] += max(cvp_remaining * export_ratio, 0.0)
    self.HRO_pump[t] += max(swp_remaining * export_ratio, 0.0)
    
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
    if t < (self.T-1):
      if self.outflow[t] > 0.0:
        self.x2[t+1] = 10.16 + 0.945*self.x2[t] - 1.487*np.log10(self.outflow[t]*tafd_cfs)
      else:
        self.x2[t+1] = 10.16 + 0.945*self.x2[t] - 1.487*np.log10(50.0)

	##Calculate X2 values, for salinity rules - note, if outflow is negative (may happen under extreme conditions in which not enough storage to meet negative gains)
	##X2 is calculated w/an outflow of 50 cfs b/c log calcs require positive flow
    if t > self.omr_record_start:
      self.OMR[t] = self.hist_OMR[t] + self.hist_TRP_pump[t] + self.hist_HRO_pump[t] - self.TRP_pump[t] - self.HRO_pump[t]
    else:
      if self.vernalis_gains < 16000.0*cfs_tafd:
        self.OMR[t] = self.vernalis_gains*0.471 + 83.0*cfs_tafd - 0.911*(self.TRP_pump[t] + self.HRO_pump[t])
      elif self.vernalis_gains < 28000.0*cfs_tafd:
        self.OMR[t] = self.vernalis_gains*0.681 - 3008.0*cfs_tafd  - 0.94*(self.TRP_pump[t] + self.HRO_pump[t])
      else:
        self.OMR[t] = self.vernalis_gains*0.633 - 1644.0*cfs_tafd  - 0.94*(self.TRP_pump[t] + self.HRO_pump[t])

    self.calc_project_allocation(t, swp_AS, cvp_AS)
    
  	
  def calc_project_allocation(self,t, SWP_AS, CVP_AS):
    m = self.month[t]
    da = self.day_month[t]
    wateryear = self.water_year[t]
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
	
	
  def create_flow_shapes_omr(self, df_short):
    omr_series = df_short['OMR'].values * cfs_tafd
    pump_series = df_short['HRO_pump'].values * cfs_tafd
    pump_series2 = df_short['TRP_pump'].values * cfs_tafd
    flow_series = omr_series + (pump_series + pump_series2)*0.94
    omr_short_record_start = 4440

    fnf_series = np.zeros(len(df_short))
    for fnf_keys in ['NML', 'DNP', 'EXC', 'MIL']:
      fnf_ind = df_short['%s_fnf'% fnf_keys].values / 1000000.0
      fnf_series += fnf_ind
    startYear = self.short_year[omr_short_record_start]
    endYear = self.short_ending_year
    numYears = endYear - startYear
    self.omr_regression = {}
    self.omr_regression['slope'] = np.zeros((365,12))
    self.omr_regression['intercept'] = np.zeros((365,12))
    monthly_flow = np.zeros((12, (endYear - startYear)))
    running_fnf = np.zeros((365,(endYear - startYear)))
    prev_fnf = 0.0
    for t in range(omr_short_record_start,(self.T_short)):
      m = self.short_month[t]
      dowy = self.short_dowy[t]
      wateryear = self.short_water_year[t] - self.short_water_year[omr_short_record_start]
      monthly_flow[m-1][wateryear] += flow_series[t-1]
      prev_fnf += fnf_series[t-1]
      running_fnf[dowy][wateryear] = np.sum(fnf_series[(t-30):t])

    for x in range(0,365):
      if self.key == "XXX":
        fig = plt.figure()
      #regress for gains in oct-mar period and april-jul period. use non-leap year.
      coef_save = np.zeros((12,2))
      for mm in range(0,12):
        if x <= self.dowy_eom[self.non_leap_year][mm]:
          one_year_runfnf = running_fnf[x]
          monthly_flow_predict = monthly_flow[mm]
        else:
          monthly_flow_predict = np.zeros(numYears-1)
          one_year_runfnf = np.zeros(numYears-1)
          for yy in range(1,numYears):
            monthly_flow_predict[yy-1] = monthly_flow[mm][yy]
            one_year_runfnf[yy-1] = running_fnf[x][yy-1]

        coef = np.polyfit(one_year_runfnf, monthly_flow_predict, 1)
        self.omr_regression['slope'][x][mm] = coef[0]
        self.omr_regression['intercept'][x][mm] = coef[1]
        if self.key == "XXX":
          coef_save[mm][0] = coef[0]
          coef_save[mm][1] = coef[1]
          r = np.corrcoef(one_year_runfnf,monthly_flow_predict)[0,1]
          print(x, end = " ")
          print(mm, end = " ")
          print(r, end = " ")
          print(self.key)
      if self.key == "XXX":
        for mm in range(0,12):
          ax1 = fig.add_subplot(4,3,mm+1)
          if x <= self.dowy_eom[self.non_leap_year][mm]:
            monthly_flow_predict = monthly_flow[mm]
            one_year_runfnf = running_fnf[x]
          else:
            monthly_flow_predict = np.zeros(numYears-1)
            one_year_runfnf = np.zeros(numYears-1)
            for yy in range(1,numYears):
              monthly_flow_predict[yy-1] = monthly_flow[mm][yy]
              one_year_runfnf[yy-1] = running_fnf[x][yy-1]

          ax1.scatter(one_year_runfnf, monthly_flow_predict, s=50, c='red', edgecolor='none', alpha=0.7)
          ax1.plot([0.0, np.max(one_year_runfnf)], [coef_save[mm][1], (np.max(one_year_runfnf)*coef_save[mm][0] + coef_save[mm][1])],c='red')
          ax1.set_xlim([np.min(one_year_runfnf), np.max(one_year_runfnf)])
        plt.show()
        plt.close()
	  
  def accounting_as_df(self, index):
    df = pd.DataFrame()
    names = ['TRP_pump','HRO_pump', 'total_outflow','SWP_allocation', 'CVP_allocation', 'X2', 'SCINDEX', 'SJINDEX', 'tax_swp', 'tax_cvp']
    things = [self.TRP_pump, self.HRO_pump, self.outflow, self.swp_allocation, self.cvp_allocation, self.x2, self.forecastSRI, self.forecastSJI, self.remaining_tax_free_storage['swp'], self.remaining_tax_free_storage['cvp']]
    for n,t in zip(names,things):
      df['%s_%s' % (self.key,n)] = pd.Series(t, index=index)
    return df