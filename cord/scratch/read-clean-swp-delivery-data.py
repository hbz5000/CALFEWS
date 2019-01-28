import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

### Script for reading, cleaning, organizing SWP delivery data, to be compared with modeled deliveries
# Read data ~~NOTE: before running this, save xlsx as csv, then manually fix column names by removing lead/trail whitespace, and replacing spaces between words with _
deliveries = pd.read_csv("cord/data/input/SWP_delivery_data_2000_2018.csv")

# Clean white space, etc
deliveries.To_Reach = deliveries.To_Reach.apply(lambda x: x.replace(' ',''))
deliveries.WT_Group = deliveries.WT_Group.apply(lambda x: x.replace(' ',''))
deliveries.Water_Type = deliveries.Water_Type.apply(lambda x: x.replace(' ',''))
deliveries.Agency_Name = deliveries.Agency_Name.apply(lambda x: x.replace(' ',''))
deliveries.JAN = pd.to_numeric(deliveries.JAN.apply(lambda x: x.replace(' ','').replace('-','0').replace(',','')))
deliveries.FEB = pd.to_numeric(deliveries.FEB.apply(lambda x: x.replace(' ','').replace('-','0').replace(',','')))
deliveries.MAR = pd.to_numeric(deliveries.MAR.apply(lambda x: x.replace(' ','').replace('-','0').replace(',','')))
deliveries.APR = pd.to_numeric(deliveries.APR.apply(lambda x: x.replace(' ','').replace('-','0').replace(',','')))
deliveries.MAY = pd.to_numeric(deliveries.MAY.apply(lambda x: x.replace(' ','').replace('-','0').replace(',','')))
deliveries.JUN = pd.to_numeric(deliveries.JUN.apply(lambda x: x.replace(' ','').replace('-','0').replace(',','')))
deliveries.JUL = pd.to_numeric(deliveries.JUL.apply(lambda x: x.replace(' ','').replace('-','0').replace(',','')))
deliveries.AUG = pd.to_numeric(deliveries.AUG.apply(lambda x: x.replace(' ','').replace('-','0').replace(',','')))
deliveries.SEP = pd.to_numeric(deliveries.SEP.apply(lambda x: x.replace(' ','').replace('-','0').replace(',','')))
deliveries.OCT = pd.to_numeric(deliveries.OCT.apply(lambda x: x.replace(' ','').replace('-','0').replace(',','')))
deliveries.NOV = pd.to_numeric(deliveries.NOV.apply(lambda x: x.replace(' ','').replace('-','0').replace(',','')))
deliveries.DEC = pd.to_numeric(deliveries.DEC.apply(lambda x: x.replace(' ','').replace('-','0').replace(',','')))

# sum annual for each delivery type/year
deliveries['Annual'] = deliveries.JAN + deliveries.FEB + deliveries.MAR + deliveries.APR + deliveries.MAY + \
                       deliveries.JUN + deliveries.JUL + deliveries.AUG + deliveries.SEP + deliveries.OCT + \
                       deliveries.NOV + deliveries.DEC






### aggregate different groups/reaches together for comparison to model output. See "model.py", initialize_water_districts function, for district 3-letter uppercase abbreviations
deliveries['Agency_Group'] = 'other'
deliveries.Agency_Group.loc[deliveries.Agency_Name == 'DUDLEYRIDGEWATERDISTRICT'] = 'DLR'
deliveries.Agency_Group.loc[deliveries.Agency_Name == 'TULARELAKEBASINWSD'] = 'TLB'
deliveries.Agency_Group.loc[deliveries.Agency_Name == 'WESTLANDSWATERDISTRICT'] = 'WSL'
deliveries.Agency_Group.loc[deliveries.Agency_Name == 'MADERAIRRIGATIONDISTRICT'] = 'MAD'

deliveries.Agency_Group.loc[deliveries.Agency_Name == 'KERN-TULAREWATERDISTRICT'] = 'KRT'
deliveries.Agency_Group.loc[deliveries.Agency_Name == 'LOWERTULERIVER'] = 'LWT'

deliveries.Agency_Group.loc[deliveries.Agency_Name == 'KERNCOUNTYWA'] = 'kcwa'
deliveries.Agency_Group.loc[deliveries.Agency_Name == 'FRIANTWATERUSERSAUTHORITY'] = 'fwua'

deliveries.Agency_Group.loc[(deliveries.Agency_Name == 'BROWNSVALLEYIRRIGATIONDIST') |
                            (deliveries.Agency_Name == 'BUTTEWATERDISTRICT') |
                            (deliveries.Agency_Name == 'CITYOFYUBACITY') |
                            (deliveries.Agency_Name == 'COUNTYOFBUTTE') |
                            (deliveries.Agency_Name == 'GARDENHIGHWAYMUTUALWATERCOMPANY') |
                            (deliveries.Agency_Name == 'PLACERCOUNTYWATERAGENCY') |
                            (deliveries.Agency_Name == 'PLUMASMUTUALWATERCOMPANY') |
                            (deliveries.Agency_Name == 'RICHVALEIRRIGATIONDISTRICT') |
                            (deliveries.Agency_Name == 'SOUTHFEATHERWATER&POWERAGENCY') |
                            (deliveries.Agency_Name == 'SOUTHSUTTERWATERDISTRICT') |
                            (deliveries.Agency_Name == 'SUTTEREXTENSIONWATERDISTRICT') |
                            (deliveries.Agency_Name == 'THERMALITOWATERANDSEWERDISTRICT') |
                            (deliveries.Agency_Name == 'TRI-VALLEYWATERDISTRICT') |
                            (deliveries.Agency_Name == 'WESTERNCANALWATERDISTRICT')] = 'sacramentoriver'

deliveries.Agency_Group.loc[(deliveries.Agency_Name == 'NAPACOUNTYFC&WCD') |
                            (deliveries.Agency_Name == 'SOLANOCOUNTYWATERAGENCY')] = 'northbay'

deliveries.Agency_Group.loc[(deliveries.Agency_Name == 'ALAMEDACOUNTYFC&WCD-ZONE7') |
                            (deliveries.Agency_Name == 'ALAMEDACOUNTYWD')] = 'southbay'

deliveries.Agency_Group.loc[(deliveries.Agency_Name == 'CITYOFTRACY')] = 'delta'

deliveries.Agency_Group.loc[(deliveries.Agency_Name == 'DELPUERTOWATERDISTRICT') |
                            (deliveries.Agency_Name == 'OAKFLATWATERDISTRICT') |
                            (deliveries.Agency_Name == 'SANLUISWATERDISTRICT') |
                            (deliveries.Agency_Name == 'SanLuis&DeltaMendotaWaterAuth') |
                            (deliveries.Agency_Name == 'TRANQUILLITYIRRIGATIONDISTRICT')] = 'deltamendotacanal'

deliveries.Agency_Group.loc[(deliveries.Agency_Name == 'PACHECOPASSWATERDISTRICT') |
                            (deliveries.Agency_Name == 'SANBENITOWATERDISTRICT') |
                            (deliveries.Agency_Name == 'SANTACLARAVALLEYWD')] = 'pachecotunnel'

deliveries.Agency_Group.loc[(deliveries.Agency_Name == 'SANLUISOBISPOCOUNTYFC&WCD') |
                            (deliveries.Agency_Name == 'SANTABARBARACOUNTYFC&WCD')] = 'centralcoast'

deliveries.Agency_Group.loc[(deliveries.Agency_Name == 'HILLSVALLEYIRRIGATIONDISTRICT')] = 'other_maderacanal'

deliveries.Agency_Group.loc[(deliveries.Agency_Name == 'CITYOFDOSPALOS') |
                            (deliveries.Agency_Name == 'MERCEDIRRIGATIONDISTRICT')] = 'other_mercedco'

deliveries.Agency_Group.loc[(deliveries.Agency_Name == 'BROADVIEWWATERDISTRICT') |
                            (deliveries.Agency_Name == 'CITYOFCOALINGA') |
                            (deliveries.Agency_Name == 'CITYOFHURON') |
                            (deliveries.Agency_Name == 'COUNTYOFFRESNO') |
                            (deliveries.Agency_Name == 'PANOCHEWATERDISTRICT')] = 'other_fresnoco'

deliveries.Agency_Group.loc[(deliveries.Agency_Name == 'AVENAL,CITYOF') |
                            (deliveries.Agency_Name == 'AvenalStatePrison') |
                            (deliveries.Agency_Name == 'COUNTYOFKINGS') |
                            (deliveries.Agency_Name == 'EMPIREWESTSIDEID')] = 'other_kingsco'

deliveries.Agency_Group.loc[(deliveries.Agency_Name == 'COUNTYOFTULARE') |
                            (deliveries.Agency_Name == 'PIXLEYIRRIGATIONDISTRICT')] = 'other_tulareco'

deliveries.Agency_Group.loc[(deliveries.Agency_Name == 'RAGGULCHWATERDISTRICT')] = 'other_kernco'

deliveries.Agency_Group.loc[(deliveries.Agency_Name == 'ANTELOPEVALLEY-EASTKERNWA') |
                            (deliveries.Agency_Name == 'CASTAICLAKEWA') |
                            (deliveries.Agency_Name == 'COACHELLAVALLEYWD') |
                            (deliveries.Agency_Name == 'CRESTLINE-LAKEARROWHEADWA') |
                            (deliveries.Agency_Name == 'DESERTWATERAGENCY') |
                            (deliveries.Agency_Name == 'LITTLEROCKCREEKID') |
                            (deliveries.Agency_Name == 'MOJAVEWATERAGENCY') |
                            (deliveries.Agency_Name == 'PALMDALEWATERDISTRICT') |
                            (deliveries.Agency_Name == 'SANBERNARDINOVALLEYMWD') |
                            (deliveries.Agency_Name == 'SANGABRIELVALLEYMWD') |
                            (deliveries.Agency_Name == 'SANGORGONIOPASSWA') |
                            (deliveries.Agency_Name == 'THEMETROPOLITANWATERDISTRICTOF') |
                            (deliveries.Agency_Name == 'VENTURACOUNTYWPD')] = 'socal'

deliveries.Agency_Group.loc[(deliveries.Agency_Name == 'CADEPTOFFISHANDGAME') |
                            (deliveries.Agency_Name == 'CADEPTOFPARKSANDRECREATION') |
                            (deliveries.Agency_Name == 'CADEPTOFWATERRESOURCES') |
                            (deliveries.Agency_Name == 'EWA-STATE') |
                            (deliveries.Agency_Name == 'KERNNATIONALWILDLIFEREFUGE') |
                            (deliveries.Agency_Name == "SANJOAQUINVALLEYNAT'LCEMETERY") |
                            (deliveries.Agency_Name == 'USBUREAUOFRECLAMATION')] = 'statefederal'


### now split up KCWA contractors using Reach numbers from Table 22 of State Water Project Operations Data monthly report (Dec 1998 and Jun 2017)
# R8D is either DLR or TLB or County of Kings according to pdf, but only one here says DLR for Bill_To_Agency_Name
deliveries.Agency_Group.loc[(deliveries.Agency_Group == 'kcwa') &
                            (deliveries.To_Reach == 'VCA-R8D')] = 'DLR'
# R9 Lost Hills or Berrenda Mesa
deliveries.Agency_Group.loc[(deliveries.Agency_Group == 'kcwa') &
                            (deliveries.To_Reach == 'VCA-R9')] = 'LHL'
# R10A many possibilities
deliveries.Agency_Group.loc[(deliveries.Agency_Group == 'kcwa') &
                            (deliveries.To_Reach == 'VCA-R10A')] = 'LHL_BLR_BVA_SMI_statefederal'
# R11B always Belridge
deliveries.Agency_Group.loc[(deliveries.Agency_Group == 'kcwa') &
                            (deliveries.To_Reach == 'VCA-R11B')] = 'BLR'
# R12D Belridge or West Kern
deliveries.Agency_Group.loc[(deliveries.Agency_Group == 'kcwa') &
                            (deliveries.To_Reach == 'VCA-R12D')] = 'BLR_WKN'
# R12E many possibilities, including CVC
deliveries.Agency_Group.loc[(deliveries.Agency_Group == 'kcwa') &
                            (deliveries.To_Reach == 'VCA-R12E')] = 'BVA_LWT_TUL_COF_pixley_haciendaDWR_CVC-KCWA_CVC-DLR_CVC-BVA_ARV'
# R13B buena vista, henry miller, or kern water bank in/out
deliveries.Agency_Group.loc[(deliveries.Agency_Group == 'kcwa') &
                            (deliveries.To_Reach == 'VCA-R13B')] = 'BVA_HML_KW'
# R14A West Kern or Wheeler Ridge-Maricopa
deliveries.Agency_Group.loc[(deliveries.Agency_Group == 'kcwa') &
                            (deliveries.To_Reach == 'VCA-R14A')] = 'WKM_WRM'
# R14B always Wheeler Ridge-Maricopa
deliveries.Agency_Group.loc[(deliveries.Agency_Group == 'kcwa') &
                            (deliveries.To_Reach == 'VCA-R14B')] = 'WRM'
# R14C WRM or arvin
deliveries.Agency_Group.loc[(deliveries.Agency_Group == 'kcwa') &
                            (deliveries.To_Reach == 'VCA-R14C')] = 'WRM_ARV'
# R15A WRM
deliveries.Agency_Group.loc[(deliveries.Agency_Group == 'kcwa') &
                            (deliveries.To_Reach == 'VCA-R15A')] = 'WRM'
# R16A Wheeler Ridge-Maricopa or Tehachapi Cummings
deliveries.Agency_Group.loc[(deliveries.Agency_Group == 'kcwa') &
                            (deliveries.To_Reach == 'VCA-R16A')] = 'WRM_THC'
# R31A is start of Coastal Branch - berrenda mesa is only kcwa
deliveries.Agency_Group.loc[(deliveries.Agency_Group == 'kcwa') &
                            (deliveries.To_Reach == 'VCB1-R31A')] = 'BDM'
# R17E is start of East Branch after Edmonston pumping plant - Tejon-Castac has delivery
deliveries.Agency_Group.loc[(deliveries.Agency_Group == 'kcwa') &
                            (deliveries.To_Reach == 'VCA-R17E')] = 'TJC'
# Rest are unknown - don't see any kcwa members in pdfs. Reaches VCA-R3A, VCA-R4, VCB2-R33A.
deliveries.Agency_Group.loc[(deliveries.Agency_Group == 'kcwa')] = 'kcwa_unknown'





### aggregate by agency group & year
deliveries['Year__Agency_Group'] = deliveries.Year.map(str) + '__' + deliveries.Agency_Group
deliveries_aggregate_agency = deliveries.groupby(by = ['Year__Agency_Group']).sum()
deliveries_aggregate_agency.Year = deliveries.groupby(by = ['Year__Agency_Group'])['Year'].first()
deliveries_aggregate_agency['Agency_Group'] = deliveries.groupby(by = ['Year__Agency_Group'])['Agency_Group'].first()

deliveries['Year__WT_Group'] = deliveries.Year.map(str) + '__' + deliveries.WT_Group
deliveries_aggregate_WTgroup = deliveries.groupby(by = ['Year__WT_Group']).sum()
deliveries_aggregate_WTgroup.Year = deliveries.groupby(by = ['Year__WT_Group'])['Year'].first()
deliveries_aggregate_WTgroup['WT_Group'] = deliveries.groupby(by = ['Year__WT_Group'])['WT_Group'].first()


# plot
plt.plot(deliveries_aggregate_agency.loc[deliveries_aggregate_agency.Agency_Group == 'BLR'].Year,
         deliveries_aggregate_agency.loc[deliveries_aggregate_agency.Agency_Group == 'BLR'].Annual)

plt.plot(deliveries_aggregate_WTgroup.loc[deliveries_aggregate_WTgroup.WT_Group == 'Article21'].Year,
         deliveries_aggregate_WTgroup.loc[deliveries_aggregate_WTgroup.WT_Group == 'Article21'].Annual)

