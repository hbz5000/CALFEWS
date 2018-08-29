CVP deliveries example
https://www.usbr.gov/mp/cvp-water/docs/cvp-water-deliveries.pdf

It's not possible to get this totally right. The contracted amounts are not always what's delivered. There is a priority though.

CVP: 2 MAF/yr NOD, ~2.5 MAF/yr SOD. 
NOD has first priority. During the drought, SOD got almost zero.
In good years Tracy pumping is around 2.5 MAF/yr.
Pumping does not follow the seasonal demand distribution. So releases from CVP reservoirs for NOD demand are during summer, but releases anytime can be pumped into SNL.


Assume total NOD consumptive demand is:
# north of delta demand, in TAFD
nodd = np.array([2,2,3,5,8,11,12,8,6,5,4,2]) / cfs_tafd

This is divided between SHA/FOL. Assume the divide is proportional to their storage volumes 4552/(4552+975) = 82% SHA, 18% FOL

