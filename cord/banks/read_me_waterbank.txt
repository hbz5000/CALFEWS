{
  Participant list - all districts that can bank water at this waterbank (not all 'participants' need to have an ownership share - some participants can just have access to 'unused' space)
  "participant_list": ["DLR","KCWA","ID4","SMI","TJC","PVT","WRM"],
  "initial_recharge": 600.0, - recharge rate, CFS NOTE: this rate decreases over time under continual use of the recharge basin
  "recovery": 0.0 - total recovery capacity (tAF/day)
  "tot_storage": 1.188 - total above-ground storage in the waterbank (every day, the storage is decreased by the recharge rate) 
  "recharge_decline": [1.0, 0.94, 0.88, 0.88, 0.88, 0.88, 0.99, 0.99, 0.99, 0.99, 0.99, 0.99, 0.99] - monthly decline in the recharge capacity of a direct recharge basin under continuous use (i.e., after 1 month - recharge is 94% of capacity, after 2 - 82% (0.94*0.88), etc..)
  "ownership": { - ownership percentages (how much of the recharge/recovery capacity does this district have priority to?)
    "DLR": 0.0962,
    "KCWA": 0.0,
    "ID4": 0.0962,
    "SMI": 0.0667,
    "TJC": 0.02,
    "PVT": 0.4806,
    "WRM": 0.2403
  },
}
