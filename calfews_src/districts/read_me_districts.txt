{
  "contract_list": ["friant1", "friant2"] - list of surface water contract names that are owned by the district
  "turnout_list": ["fkc"] - list of canal names that the district has access to
  "in_leiu_banking": true - does the district have an in-leiu banking program?
  NOTE: if in_leiu-_banking is false, the district does not have a participant_list, or leiu_ownership
  "participant_list": ["SOC", "OXV", "LWT", "KRT"] - what districts participate in the in-leiu banking program
  "leiu_ownership" -{ownership of the in-leiu capacity (determines which districts have 'priority' and which have to use leftover space
    "SOC": 1.0,percent of the capacity (1.0 = 100%) owned by "SOC" (district key)
    "OXV": 0.0,
    "LWT": 0.0,
    "KRT": 0.0
  },
  "leiu_recovery": 0.0 - total groundwater recovery (pump into canal) capacity in the district (tafd)
  "in_district_direct_recharge": 0.0 - total direct recharge rate for in-district spreading basins (CFS)
  "in_district_storage": 0.0 - total above ground storage capacity for in-district spreading basins
  "loss_rate": 0.1 - losses encountered when spreading water for recharge
  "recovery_fraction": 0.5 - total SW contract allocation, as a % of total district demand, below which the district requests recovery
  "surface_water_sa" = 1.0 - what percentage of the acreage (by water demand) can be reached by the SW supply system
  "must_fill" = 0 - does the district need to be met 100% of the time? (only used for districts that represent pumping into aqueduct branches
  "seasonal_connection" = 1.0 - is the district always connected to canal turnouts (for rivers that go dry parts of the year)
  "seepage" = 1.25 - multiplication factor for district demands to account for seepage through canals
  "inleiuharcut" = 0.9 - for in-leiu water banks, what % of delivered water is credited to member accounts?
  "recharge_decline": [1.0, 0.94, 0.88, 0.88, 0.88, 0.88, 0.99, 0.99, 0.99, 0.99, 0.99, 0.99, 0.99] - %monthly decline in the recharge capacity of a direct recharge basin under continuous use (i.e., after 1 month - recharge is 94% of capacity, after 2 - 82% (0.94*0.88), etc..)
  
  "project_contract": { - for each contract, what % of the total contract allocation is owned by the district
    "tableA": 0.0, - SWP delta
    "cvpdelta": 0.0, - CVP delta
    "friant1": 0.0625, - CVP Friant Class 1
    "friant2": 0.028265524, - CVP Friant Class 2
    "cvc": 0.0, - Cross Valley Canal
    "exchange": 0.0, - CVP exchange contractors
    "hidden": 0.0, - hidden valley contracts (not used)
    "buchannon": 0.0, - CVP Buchannon division (not used)
    "eastside": 0.0 - CVP Eastside contracts (not used)
  },
   Water rights on the local streams owned by the districct
  "rights": {
    "tuolumne": { Tuolumne River
      "capacity": 0.0 - % of storage (reservoir) capacity owned
      "carryover": 0.0 - % of carryover capacity owned
      "numrights": 1 - how many different water rights are owned
      "d": [0, 366] - what days of the year are attached to the water rights
      "start": [9999999, 9999999] - at what flow do the water rights kick in?
      "volume": [0, 0] - what is the maximum volume attached to teh water rights
      "fraction": [1.0, 1.0] - what fraction of the flow (starting at a flow of 'start', until a volume of 'volume' has been reached), does the district have a right to?
    },
    "merced": {Merced River
      "capacity": 0.0,
      "carryover": 0.0,
      "numrights": 1,
      "d": [0, 366],
      "start": [9999999, 9999999],
      "volume": [0, 0],
      "fraction": [1.0, 1.0]
    },
    "kings": {Kings River
      "capacity": 0.0,
      "carryover": 0.0,
      "numrights": 1,
      "d": [0, 366],
      "start": [9999999, 9999999],
      "volume": [0, 0],
      "fraction": [1.0, 1.0]
    },
    "kaweah": {Kaweah River
      "capacity": 0.0,
      "carryover": 0.0,
      "numrights": 1,
      "d": [0, 366],
      "start": [9999999, 9999999],
      "volume": [0, 0],
      "fraction": [1.0, 1.0]
    },
    "tule": {Tule River
      "capacity": 0.0,
      "carryover": 0.0,
      "numrights": 1,
      "d": [0, 366],
      "start": [9999999, 9999999],
      "volume": [0, 0],
      "fraction": [1.0, 1.0]
    },
    "kern": {Kern River
      "capacity": 0.0,
      "carryover": 0.0,
      "numrights": 1,
      "d": [0, 366],
      "start": [9999999, 9999999],
      "volume": [0, 0],
      "fraction": [1.0, 1.0]
    }
  },
  "service": {
    "storage": 0.0 - how much storage (in tAF) exists within the district
    "unlined": 0.0 - how many miles of unlined canals contained in the district
    "recharge": 0.0 - how much recharge is inside the district
  },
  "crop_list": ["almond", "alfalfa", "cotton", "grain", "field_misc", "idle"], - what crops are grown
  "zone": "zone15", - what is the crop zone of the district (to determine ET demands for different crops)
  "acreage":{ - what acreages of the above crops are grown, in each water year type
    "W": [17.414, 2.768, 1.472, 1.371, 7.102, 7.863],
    "AN": [17.414, 2.768, 1.472, 1.371, 7.102, 7.863],
    "BN": [17.414, 2.768, 1.472, 1.371, 7.102, 7.863],
    "D": [17.414, 2.768, 1.472, 1.371, 7.102, 7.863],
    "C": [17.414, 2.768, 1.472, 1.371, 7.102, 7.863]
  },
  "MDD": 0.0, - what is the annual municipal/urban/non-ag water demand
  "urban_profile":[0.08333, 0.08333, 0.08333, 0.08333, 0.08333, 0.08333, 0.08333, 0.08333, 0.08333, 0.08333, 0.08333, 0.08333] - what fraction of that demand occcurs in each month
}
