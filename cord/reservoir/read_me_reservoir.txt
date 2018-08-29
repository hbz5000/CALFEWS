{
  "capacity": 3537 - reservoir capacity
  "env_min_flow":{ - minimum reservoir outflow requirements (cfs) by water year type and month
    "W": [1700,1700,1700,1000,1000,1000,1000,1000,1000,1700,1700,1700],
    "AN": [1700,1700,1700,1000,1000,1000,1000,1000,1000,1700,1700,1700],
    "BN": [1200,1200,1000,1000,1000,1000,1000,1000,1000,1200,1200,1200],
    "D":  [1200,1200,1000,1000,1000,1000,1000,1000,1000,1200,1200,1200],
    "C":  [1200,1200,1000,1000,1000,1000,1000,1000,1000,1200,1200,1200]
  },
  "temp_releases":{ - minimum flow requirements at 'downstream gauge' - includes gains/losses on the reach btw reservoir and gauge
    "W": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    "AN": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    "BN": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    "D": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    "C": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
  },
  "nodd_meets_envmin": true, - for SWP/CVP reservoirs, do north-of-delta deliveries meet the environmental flow requirements (above)?
  "has_downstream_target_flow": true - is there a target flow downstream (i.e., is temp_releases binding?)
  "tocs_rule":{
    "index": [999, 11.0, 3.5, 0.0], - thresholds for flood control index values
	- day of the water year where the flood control pool changes (new rows for different values in 'tocs_rule.index')
    "dowy":  [[0,15,197,273,351,366],
              [0,15,197,273,351,366],
              [0,15,197,235,351,366],
              [0,15,197,235,351,366]],
    storage - max storage for flood control rules - each colum corresponds to a 'dowy' segement (i.e, at day 15, 197, 273..etc the storage is found by moving one colume to the right) and each row corresponds to an index segment (i.e., at index value 11.0, 3.5.. etc we move one row down)
    "storage": [[3162,2787,2788,3537,3537,3162],
                [3162,2787,2788,3537,3537,3162],
                [3349.5,3163,3163,3537,3537,3349.5],
                [3349.5,3163,3163,3537,3537,3349.5]]
  },
  "carryover_target": {-for each water year type, what is the target storage on October 1?
    "W": 1000,
    "AN": 1000,
    "BN": 1000,
    "D": 1000,
    "C": 1000
  },
  "carryover_excess_use": 0.5, - %of storage above the target that can be used for releases (i.e., if we start at 1700 tAF, then 0.5*(1700-1000) = 350 tAF for release)
  "nodd": [0,0,0,0,0,0,0,0,0,0,0,0], - north of delta demands (related to SWP and CVP reservoirs)
  "sodd_pct": 1.0, - percent of project exports to south met by this reservoir (DO NOT USE HERE - this variable is overwritten in the northern model)
  "sodd_curtail_pct": { - how much should we curtail exports based on the water year type (DO NOT USE HERE - this variable is overwritten in the northern model)
    "W": 1.0,
    "AN": 1.0,
    "BN": 1.0,
    "D": 0.8,
    "C": 0.4
  },
  "exceedence": { - what z-score should we use to estimate reservoir inflow (i.e., 2 = 90% confidence that inflow will be greater, 10 = 50% confidence)
    "W": 2,
    "AN": 2,
    "BN": 2,
    "D": 2,
    "C": 2
  },
  "melt_start": 4, - what month does melt season start
  "max_outflow": 150000, - maximum release from reservoir
  "delta_outflow_pct": 0.25, - how much of the delta outflow reqruiement is met at this reservoir
  "dead_pool": 852 - dead pool (inaccessable) storage
}
