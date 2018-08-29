{
  "total": 4056.205 - total (maximum) contract allocation (tAF)
  "maxForecastValue": 2400.0 - maximum value for early-year forecasts that rely on preivous year's allocatoin (i.e., if previous year's allocation was greater than this value, use this value instead of last year's allocation
  "carryover": 1020.0 - maximum contract carryover into next year
  "type": "contract" - either a contract (from SWP/CVP) or water right (from local sources)
  "name": "tableA" - name for contract
  "allocation_priority": 1 - if allocation priority is equal to 1, this means that this contract's allocation is filled first using flow projections into the reservoir.  If its not equal to one, then all 'priority' contracts at that reservoir must reach their full allocation before any allocation is made to this contract
  "storage_priority": 1 - if storage priority is equal to 1, then surface storage is available immediately to fill requests on the contract allocation as soon as it comes into the reservoir.  If it is not, water from this contract's allocation is only available once the entire allocation from priority storage contracts has either been delivered or is currently in surface water storage
  "contractors": ["DLR", "EWS", "TLB", "SCV", "BDM", "LHL", "BLR", "SMI", "CWO", "RRB", "BVA", "KND", "HML", "WKN", "WRM", "THC", "TJC", "ID4", "SBM", "SJM", "CCM", "SCM"], - list of districts w/ allocations to this contract (not used in the model)
  "reduction":{ - for some contracts, the max allocation can be reduced depending on teh water year type.  The reduction fraction is multiplied by the 'total' to determine the full allocation in a given water year type.
    "W": 1.0,
    "AN": 1.0,
    "BN": 1.0,
    "D": 1.0,
    "C": 1.0
  }
}
