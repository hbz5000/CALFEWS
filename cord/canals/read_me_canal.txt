{
  Canals have 3 different 'flow types' - normal (moving across their index from 0 > end); 'reverse' (moving across their index from end > 0) and 'closed' - does not allow for anything to move across their canal.  Many canals are only 1 directional, thus have a capacity of 0.0 across their entire range.  2 directional canals have capacities in both directions, which can be different.
  Capacity is in CFS and corresponds to the nodes in the modelso.canal_district dictionary lists corresponding to the name of the canal
  "capacity": {
    "normal": [1000.0, 1000.0, 1000.0, 1000.0, 1000.0, 0.0],
    "reverse": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
    "closed": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
	},
   Turnout is exactly the same as capacity, only turnout corresponds to the capacity with which water can be taken out of or put into the canal
  "turnout": {
    "normal": [0.0, 1000.0, 1000.0, 1000.0, 1000.0],
    "reverse": [0.0, 0.0, 0.0, 0.0, 0.0],
    "closed": [0.0, 0.0, 0.0, 0.0, 0.0]
  },
  "flow_directions": { - flow directions determine the direction of flow of OTHER canals that intersect with the current canal.  It should be read as if you are on this canal, and the next node is another canal.  What direction is that canal set up to flow?  This can be different if you are recharging or recovering water (basically - this tells us if water is COMING from the new canal, or water is GOING to the new canal, as we search through the canals to distribute water.
    "recharge": {
      "fkc": "closed",
      "caa": "closed",
      "xvc": "closed"
      },
    "recovery": {
      "fkc": "closed",
      "caa": "normal",
      "xvc": "closed"
      }
  },
  "name": "aec"
}
