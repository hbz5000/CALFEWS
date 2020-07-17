{
  Outflow requirements for the delta as a whole (including SAC, SJ, Eastside gains, and delta depletions) - by water year type & month
  "min_outflow": {
    "W": [6000,7100,7100,7100,7100,7100,8000,4000,3000,4000,4500,4500],
    "AN": [6000,7100,7100,7100,7100,7100,8000,4000,3000,4000,4500,4500],
    "BN": [6000,7100,7100,7100,7100,7100,6500,4000,3000,4000,4500,4500],
    "D": [6000,7100,7100,7100,7100,7100,5000,3500,3000,4000,4500,4500],
    "C": [4500,7100,7100,7100,7100,7100,4000,3000,3000,3000,3500,3500]
  },
  
  Maximum ratio of exports (CVP + SWP) to delta inflows (not including delta depletions) - by water year type & month
  "export_ratio": {
    "W": [0.65,0.35,0.35,0.35,0.35,0.35,0.65,0.65,0.65,0.65,0.65,0.65],
    "AN": [0.65,0.35,0.35,0.35,0.35,0.35,0.65,0.65,0.65,0.65,0.65,0.65],
    "BN": [0.65,0.40,0.35,0.35,0.35,0.35,0.65,0.65,0.65,0.65,0.65,0.65],
    "D": [0.65,0.40,0.35,0.35,0.35,0.35,0.65,0.65,0.65,0.65,0.65,0.65],
    "C": [0.65,0.45,0.35,0.35,0.35,0.35,0.65,0.65,0.65,0.65,0.65,0.65]
  },
  Maximum pumping at SWP pumps and CVP pumps for different days (calender days, not days of the water year - 92 = April 1st)
  Vernalis trigger is the part of the year when the intake limit can be increased based on San Joaquin flow at Vernalis
  "pump_max": {
    "swp": {
      "d": [1, 92, 93, 153, 154, 366],
      "intake_limit": [6680, 6680, 750, 750, 6680, 6680],
      "pmax": [8850, 8850, 8850, 8850, 8850, 8850],
      "vernalis_trigger": [0.0, 0.0, 1.0, 1.0, 0.0, 0.0]
    },
    "cvp": {
      "d": [1,92,93,153,154,366],
      "intake_limit": [4300,4300,750,750,4300,4300],
      "pmax": [4300,4300,4300,4300,4300,4300],
      "vernalis_trigger": [0.0, 0.0, 1.0, 1.0, 0.0, 0.0]
    }
  },
  Old-Middle River rules - flow on the Old& Middle Rivers run backwards when the delta pumps are on - this is the rule for limiting the negative flow on the river (-5000 CFS).  't' and 'adjustment' are to note when, during the calibration period, that the limit refers to the calibration period in which the rule was more conservative than (-5000CFS) because of fish kills at the pump.  We cannot model this in 'projection' scenarios, but we can vary the limit between -5000 CFS and -2500 CFS to observe the effect from a stochastic represenation of the rule
  "omr_reqr": {
    "d": [0, 91, 92, 257, 258, 366],
    "flow": [-999999, -999999, -5000, -5000, -999999, -999999],
    "t": [0, 4104, 4105, 4114, 4115, 4166, 4167, 4180, 4186, 4193, 4200, 4221, 4222, 4251, 4252, 4283, 4284, 4536, 4537, 4543, 4544, 4571, 4572, 4578, 4579, 4611, 4612, 4639, 4640, 4646, 5226, 5227, 5231, 5232, 5256, 5257, 5306, 5307, 5351, 5352, 5358, 5359, 5620, 5621, 5627, 5628, 5674, 5675, 5690, 5691, 7032, 7033, 7039, 7040, 1000000],
    "adjustment": [-999999, -999999, -2000, -2000, -999999, -999999, -3000, -3000, -2000, -2000, -2500, -2500, -999999, -999999, -2000, -2000, -999999, -999999, -4000, -4000, -999999, -999999, -4000, -4000, -999999, -999999, -1500, -1500, -3500, -999999, -999999, -3500, -3500, -999999, -999999, -2500, -2500, -999999, -999999, -3500, -3500, -999999, -999999, -3500, -3500, -2500, -2500, -3500, -3500, -999999, -999999, -3500, -3500, -999999, -999999]
  },
  Minimum flow on the Sacramento River at rio vista (i.e., delta inflow contribution from the Sacramento River)
  "rio_vista_min": {
    "W": [0,0,0,0,0,0,0,0,3000,4000,4500,4500],
    "AN": [0,0,0,0,0,0,0,0,3000,4000,4500,4500],
    "BN": [0,0,0,0,0,0,0,0,3000,4000,4500,4500],
    "D": [0,0,0,0,0,0,0,0,3000,4000,4500,4500],
    "C": [0,0,0,0,0,0,0,0,3000,3000,3500,3500]
  },
  Minimum flow on the San Joaquin based on the BiOps New Melones index rule (biops_d & on_off used to determine when rule is binding, and 'biops_NMI and biops_flow' are used to determine the minimum flow based on the new melones inex
  "san_joaquin_min": {
	"biops_d": [0, 181, 182, 242, 243, 366],
    "biops_on_off": [0.0, 0.0, 1.0, 1.0, 0.0, 0.0],
    "biops_NMI": [0, 999, 1000, 1399, 1400, 1999, 2000, 2499, 2500, 100000],
    "biops_flow": [0, 0, 1500, 1500, 3000, 3000, 4500, 4500, 6000, 6000]
  },
  Minimum flow rule - zone refers to which colums from the 'W', 'AN', 'BN'...etc types and corresponds with the 'd' vector
  "san_joaquin_min_flow": {
    "d": [0, 30, 31, 122, 123, 181, 182, 241, 242, 272, 273, 365],
    "zone": [1, 1, 2, 2, 3, 3, 4, 4, 3, 3, 2, 2],
    "W": [1000, 0, 3420, 0],
    "AN": [1000, 0, 3420, 0],
    "BN": [1000, 0, 2280, 0],
    "D": [1000, 0, 2280, 0],
    "C": [1000, 0, 1140, 0]
  },
  #vamp_flows regulates releases from Don Pedro, New Melones, and Exchqeuer dams
  #originally based on forecast - the new_vamp_rule replaces is based on water eyar type
  "vamp_flows": {
    "forecast": [1999.0, 3199.0, 4449.0, 5699.0, 7000.0, 9999999999999.0],
    "target": [2000.0, 3200.0, 4450.0, 5700.0, 7000.0, 7000.0, 7000.0]	
  },
  "new_vamp_rule": {
    "W": 7330.0,
    "AN": 5730.0,
    "BN": 4620.0,
    "D": 4020.0,
    "C": 3110.0
  }, 
  During certain parts of the year, minimum pumping levels can be increased based on flow from the san joaquin (mult is the % of flow that can be additionally pumped)
  "san_joaquin_add": {
    "d": [0, 73, 74, 164, 165, 366],
    "mult": [0.0, 0.0, 0.333, 0.333, 0.0, 0.0]
  },
  #during parts of the year, there is also a ratio between san joaquin flow and total delta exports
  "san_joaquin_export_ratio":{
    "flow": [0, 5999, 6000, 21749, 21750, 999999],
    "ratio": [0.0, 0.0, 0.25, 0.25, 1.0, 1.0],
	"d": [0, 181, 182, 242, 243, 366],
    "on_off": [0.0, 0.0, 1.0, 1.0, 0.0, 0.0],
    "D1641_flow_target": [0, 3200, 4450, 5700, 7000, 10000000],
    "D1641_export_limit": [1500, 1500, 1500, 2250, 3000, 3000],
    "D1641_dates":[0, 4745, 4745, 10000],
    "D1641_on_off":[1.0, 1.0, 0.0, 0.0]
  },
  EC targets/model_params are for salinity measurements - model calculations were changed to be based on X2 calculations, so these values are not used  
  "ec_target": {
    "collinsville": {"W": [null, 2.64, 2.64, 2.64, 2.64, 2.64, null, null, null, null, null, null],
                     "AN": [null, 2.64, 2.64, 2.64, 2.64, 2.64, null, null, null, null, null, null],
                     "BN": [null, 2.64, 2.64, 2.64, 2.64, 2.64, null, null, null, null, null, null],
                     "D": [null, 2.64, 2.64, 2.64, 2.64, 2.64, null, null, null, null, null, null],
                     "C": [null, 2.64, 2.64, 2.64, 2.64, 2.64, null, null, null, null, null, null]},

    "emmaton": {"W": [null, null, null, 0.45, 0.45, 0.45, 0.45, 0.45, null, null, null, null],
                "AN": [null, null, null, 0.45, 0.45, 0.45, 0.63, 0.63, null, null, null, null],
                "BN": [null, null, null, 0.45, 0.45, 0.45, 1.14, 1.14, null, null, null, null],
                "D": [null, null, null, 0.45, 0.45, 0.45, 1.67, 1.67, null, null, null, null],
                "C": [null, null, null, 2.78, 2.78, 2.78, 2.78, 2.78, null, null, null, null]},

    "jerseypoint": {"W": [null, null, null, 0.45, 0.45, 0.45, 0.45, 0.45, null, null, null, null],
                    "AN": [null, null, null, 0.45, 0.45, 0.45, 0.45, 0.45, null, null, null, null],
                    "BN": [null, null, null, 0.45, 0.45, 0.45, 0.74, 0.74, null, null, null, null],
                    "D": [null, null, null, 0.45, 0.45, 0.45, 1.35, 1.35, null, null, null, null],
                    "C": [null, null, null, 2.20, 2.20, 2.20, 2.20, 2.20, null, null, null, null]}
  },
  "model_params": {"emmaton": [4.06662745, 2.36449617, -3.44927871, 17],
                   "collinsville": [4.26498281, 2.29738551, -3.69736123, 8],
                   "jerseypoint": [3.55662917, 2.25417983, -3.70881883, 12]},

			   

}
