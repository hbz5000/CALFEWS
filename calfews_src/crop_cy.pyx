# cython: profile=True
import numpy as np 
import matplotlib.pyplot as plt
import scipy
import pandas as pd
import json
from .util import *


cdef class Crop():

  def __iter__(self):
    self.iter_count = 0
    return self
  
  def __next__(self):
    if self.iter_count == 0:
      self.iter_count += 1
      return self
    else:
      raise StopIteration

  def __len__(self):
    return 1
    
  def __init__(self, key, uncertainty_dict):
    self.key = key
    self.tau = {}
    self.beta = {}
    self.delta = {}
    self.gamma = {}
    self.leontief = {}
    self.eta = {}
    self.baseline_inputs = {}
    self.baseline_revenue = {}
    self.econ_factors = {}
    self.pmp_keys = {}
    self.pmp_keys['TAU'] = self.tau
    self.pmp_keys['BETA'] = self.beta
    self.pmp_keys['DELTA'] = self.delta
    self.pmp_keys['GAMMA'] = self.gamma
    self.pmp_keys['ETA'] = self.eta
    self.pmp_keys['LEONTIEF'] = self.leontief
    self.pmp_keys['INPUTS'] = self.baseline_inputs
    self.pmp_keys['REV'] = self.baseline_revenue
    self.crop_keys = {}
    self.crop_keys['ALFAL'] = 'alfalfa'
    self.crop_keys['ALPIS'] = 'pistachio'
    self.crop_keys['CORN'] = 'corn'
    self.crop_keys['COTTN'] = 'cotton'
    self.crop_keys['CUCUR'] = 'melon'
    self.crop_keys['DRYBN'] = 'field_misc'
    self.crop_keys['FRTOM'] = 'tomato'
    self.crop_keys['GRAIN'] = 'grain'
    self.crop_keys['ONGAR'] = 'onion'
    self.crop_keys['OTHDEC'] = 'deciduous_misc'
    self.crop_keys['OTHFLD'] = 'field_misc'
    self.crop_keys['OTHTRK'] = 'field_misc'
    self.crop_keys['PASTR'] = 'pasture'
    self.crop_keys['POTATO'] = 'potatoe'
    self.crop_keys['PRTOM'] = 'tomato'
    self.crop_keys['RICE'] = 'rice'
    self.crop_keys['SAFLR'] = 'safflower'
    self.crop_keys['SBEET'] = 'vegetable_small'
    self.crop_keys['SUBTRP'] = 'subtropical_misc'
    self.crop_keys['VINE'] = 'grape'
    self.sub = 0.17

    ### get etM for each crop
    for k,v in json.load(open('calfews_src/crop/%s_properties.json' % key)).items():
      setattr(self,k,v)
    ### scale etM based on multiplier
    if 'etM_multiplier' in uncertainty_dict:
      for crop, cropdict in self.etM.items():
        if crop != 'precip':
          for wyt, etM_list in cropdict.items():
            self.etM[crop][wyt] = [etM * uncertainty_dict['etM_multiplier'] for etM in etM_list]
		
  def set_pmp_parameters(self, all_parameters, district):
    for parameter_name in all_parameters:
      parameter_data = all_parameters[parameter_name]
      district_index = parameter_data['Region'] == district
      district_crops = parameter_data['Crop'][district_index]
      district_values = parameter_data['Level'][district_index]
    
      if 'Input' in parameter_data:
        district_factors = parameter_data['Input'][district_index]
    
      parameter_dict = self.pmp_keys[parameter_name]
      for y in parameter_data.index[district_index]:
        if 'Input' in parameter_data:
          if district_factors[y] in parameter_dict:
            parameter_dict[district_factors[y]][district_crops[y]] = district_values[y]
          else:
            parameter_dict[district_factors[y]] = {}
            parameter_dict[district_factors[y]][district_crops[y]] = district_values[y]
        else:
          parameter_dict[district_crops[y]] = district_values[y]
		  
  def set_econ_parameters(self, econ_parameters, district):
    for parameter_name in econ_parameters:
      econ_data = econ_parameters[parameter_name]
      district_list = list(econ_data['DISTRICT'])
      district_index = district_list.index(district)
      if parameter_name == 'WCST':
        self.water_source_list = []
        for source in econ_data:
          if source != 'DISTRICT':
            self.water_source_list.append(source)
            self.econ_factors[source + '_price'] = econ_data[source][district_index]
      elif parameter_name == 'WSOU':
        for source in econ_data:
          if source != 'DISTRICT':
            self.econ_factors[source] = econ_data[source][district_index]

      elif parameter_name == 'LABOR' or parameter_name == 'SUPPL':
        self.econ_factors[parameter_name] = {}
        for crop in econ_data:
          self.leontief[parameter_name][crop] = econ_data[crop][district_index]
          self.econ_factors[parameter_name] = 1.0
      elif parameter_name == 'PRICE' or parameter_name == 'LANDCOST':
        self.econ_factors[parameter_name] = {}
        for crop in econ_data:
          self.econ_factors[parameter_name][crop] = econ_data[crop][district_index]

  def find_pmp_acreage(self, water_source_constraint, land_constraint, x0):
    bb = (0.0, land_constraint)
    bnds = []
    for crop in self.crop_list:	  
      bnds.append(bb)
    water_constraint = 0.0
    water_cost = 0.0
    self.econ_factors['WATER'] = {}
    for source in water_source_constraint:
      water_constraint += water_source_constraint[source]
      water_cost += water_source_constraint[source]*self.econ_factors[source + '_price']
    for crop in self.crop_list:
      if crop == 'ALFAL' or crop == 'PASTR':
        self.econ_factors['WATER'][crop] = 50.0
      else:
        self.econ_factors['WATER'][crop] = water_cost/water_constraint
    con1 = {'type': 'ineq', 'fun': self.constrain_resource, 'args' : (land_constraint, 'LAND')}
    con2 = {'type': 'ineq', 'fun': self.constrain_resource, 'args' : (water_constraint, 'WATER')}
    cons = [con1, con2]
    minimizer_kwargs = {"method":'SLSQP',"bounds": bnds, "constraints":cons}
    sol = scipy.optimize.basinhopping(self.calc_ag_profit,x0,minimizer_kwargs=minimizer_kwargs)
  
    return sol.x

  def constrain_resource(self, x, resource_constraint, resource_type):
    sum_resource = 0.0
    i = 0
    for crop in self.crop_list:
      sum_resource += x[i]*self.leontief[resource_type][crop]
      i += 1
    return resource_constraint - sum_resource
  
  def calc_ag_profit(self, x):
    total_revenue = 0.0
    i = 0
    for crop in self.crop_list:
      total_factor_beta = 0.0
      if x[i] > 0.0:
        for factor in ['LAND', 'WATER']:
          total_factor_beta += self.beta[factor][crop]*((x[i]*self.leontief[factor][crop])**((self.sub-1.0)/self.sub))
        for factor in ['SUPPL', 'LABOR']:
          total_factor_beta += self.beta[factor][crop]*((self.leontief[factor][crop])**((self.sub-1.0)/self.sub))##needs to be fixed in PMP calibration
		
      if total_factor_beta > 0.0:
        total_factor_beta = total_factor_beta**(self.sub/(self.sub-1.0))
      else:
        total_factor_beta = 0.0
	  
      total_revenue -= self.econ_factors['PRICE'][crop]*self.tau[crop]*total_factor_beta
      total_revenue += self.delta[crop]*np.exp(self.gamma[crop]*x[i])
      total_revenue += self.econ_factors['WATER'][crop]*x[i]*self.leontief['WATER'][crop]
       
      for factor in ['SUPPL', 'LABOR']:
        total_revenue += self.leontief[factor][crop]####needs to be fixed in PMP calibration

      i += 1
    
    return total_revenue
  
  def make_crop_list(self):
    self.crop_list = []
    for y in self.baseline_inputs['LAND']:
      if self.baseline_inputs['LAND'][y] > 50.0:
        self.crop_list.append(y)
