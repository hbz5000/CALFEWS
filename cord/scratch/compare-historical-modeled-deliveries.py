import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

### First read, clean, organizing historical SWP delivery data, to be compared with modeled deliveries
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


# create time series
df_historical = pd.DataFrame(index=range(deliveries.shape[0]*12))
df_historical['Year'] = 0
df_historical['Month'] = 0
df_historical['Day'] = 1
df_historical['Wateryear'] = 0
df_historical['Bill_To_Agency_Name'] = ' '
df_historical['Agency_Name'] = ' '
df_historical['Water_Type'] = ' '
df_historical['WT_Group'] = ' '
df_historical['To_Reach'] = ' '
df_historical['delivery_taf'] = 0.0

dum = np.repeat(np.arange(deliveries.shape[0]), 12)
for n in ['Year','Bill_To_Agency_Name','Agency_Name','Water_Type','WT_Group','To_Reach']:
  df_historical[n] = deliveries.iloc[dum][n].values
df_historical['Month'] = np.tile(np.arange(1,13), deliveries.shape[0])
df_historical['Wateryear'] = df_historical['Year']
df_historical['Wateryear'].loc[df_historical['Month'] > 9] = df_historical['Wateryear'].loc[df_historical['Month'] > 9] + 1

df_historical['delivery_taf'].iloc[0:df_historical.shape[0]:12] = deliveries['JAN'].values / 1000
df_historical['delivery_taf'].iloc[1:df_historical.shape[0]:12] = deliveries['FEB'].values / 1000
df_historical['delivery_taf'].iloc[2:df_historical.shape[0]:12] = deliveries['MAR'].values / 1000
df_historical['delivery_taf'].iloc[3:df_historical.shape[0]:12] = deliveries['APR'].values / 1000
df_historical['delivery_taf'].iloc[4:df_historical.shape[0]:12] = deliveries['MAY'].values / 1000
df_historical['delivery_taf'].iloc[5:df_historical.shape[0]:12] = deliveries['JUN'].values / 1000
df_historical['delivery_taf'].iloc[6:df_historical.shape[0]:12] = deliveries['JUL'].values / 1000
df_historical['delivery_taf'].iloc[7:df_historical.shape[0]:12] = deliveries['AUG'].values / 1000
df_historical['delivery_taf'].iloc[8:df_historical.shape[0]:12] = deliveries['SEP'].values / 1000
df_historical['delivery_taf'].iloc[9:df_historical.shape[0]:12] = deliveries['OCT'].values / 1000
df_historical['delivery_taf'].iloc[10:df_historical.shape[0]:12] = deliveries['NOV'].values / 1000
df_historical['delivery_taf'].iloc[11:df_historical.shape[0]:12] = deliveries['DEC'].values / 1000

df_historical['Date'] = pd.to_datetime(df_historical[['Year','Month','Day']])
del deliveries

# plt.plot_date(df_historical['Date'], df_historical['delivery_taf'], marker='o', alpha=0.3)


# aggregate different groups/reaches together for comparison to model output. See "model.py", initialize_water_districts function, for district 3-letter uppercase abbreviations
df_historical['Agency_Group'] = 'other'
df_historical.Agency_Group.loc[df_historical.Agency_Name == 'DUDLEYRIDGEWATERDISTRICT'] = 'DLR'
df_historical.Agency_Group.loc[df_historical.Agency_Name == 'TULARELAKEBASINWSD'] = 'TLB'
df_historical.Agency_Group.loc[df_historical.Agency_Name == 'WESTLANDSWATERDISTRICT'] = 'WSL'
df_historical.Agency_Group.loc[df_historical.Agency_Name == 'MADERAIRRIGATIONDISTRICT'] = 'MAD'

df_historical.Agency_Group.loc[df_historical.Agency_Name == 'KERN-TULAREWATERDISTRICT'] = 'KRT'
df_historical.Agency_Group.loc[df_historical.Agency_Name == 'LOWERTULERIVER'] = 'LWT'

df_historical.Agency_Group.loc[df_historical.Agency_Name == 'KERNCOUNTYWA'] = 'kcwa'
df_historical.Agency_Group.loc[df_historical.Agency_Name == 'FRIANTWATERUSERSAUTHORITY'] = 'fwua'

df_historical.Agency_Group.loc[(df_historical.Agency_Name == 'BROWNSVALLEYIRRIGATIONDIST') |
                            (df_historical.Agency_Name == 'BUTTEWATERDISTRICT') |
                            (df_historical.Agency_Name == 'CITYOFYUBACITY') |
                            (df_historical.Agency_Name == 'COUNTYOFBUTTE') |
                            (df_historical.Agency_Name == 'GARDENHIGHWAYMUTUALWATERCOMPANY') |
                            (df_historical.Agency_Name == 'PLACERCOUNTYWATERAGENCY') |
                            (df_historical.Agency_Name == 'PLUMASMUTUALWATERCOMPANY') |
                            (df_historical.Agency_Name == 'RICHVALEIRRIGATIONDISTRICT') |
                            (df_historical.Agency_Name == 'SOUTHFEATHERWATER&POWERAGENCY') |
                            (df_historical.Agency_Name == 'SOUTHSUTTERWATERDISTRICT') |
                            (df_historical.Agency_Name == 'SUTTEREXTENSIONWATERDISTRICT') |
                            (df_historical.Agency_Name == 'THERMALITOWATERANDSEWERDISTRICT') |
                            (df_historical.Agency_Name == 'WESTERNCANALWATERDISTRICT')] = 'sacramentoriver'

df_historical.Agency_Group.loc[(df_historical.Agency_Name == 'NAPACOUNTYFC&WCD') |
                            (df_historical.Agency_Name == 'SOLANOCOUNTYWATERAGENCY')] = 'northbay'

df_historical.Agency_Group.loc[(df_historical.Agency_Name == 'ALAMEDACOUNTYFC&WCD-ZONE7') |
                            (df_historical.Agency_Name == 'TRI-VALLEYWATERDISTRICT') |
                            (df_historical.Agency_Name == 'ALAMEDACOUNTYWD')] = 'southbay'

df_historical.Agency_Group.loc[(df_historical.Agency_Name == 'CITYOFTRACY')] = 'delta'

df_historical.Agency_Group.loc[(df_historical.Agency_Name == 'DELPUERTOWATERDISTRICT') |
                            (df_historical.Agency_Name == 'OAKFLATWATERDISTRICT') |
                            (df_historical.Agency_Name == 'SANLUISWATERDISTRICT') |
                            (df_historical.Agency_Name == 'SanLuis&DeltaMendotaWaterAuth') |
                            (df_historical.Agency_Name == 'TRANQUILLITYIRRIGATIONDISTRICT')] = 'deltamendotacanal'

df_historical.Agency_Group.loc[(df_historical.Agency_Name == 'PACHECOPASSWATERDISTRICT') |
                            (df_historical.Agency_Name == 'SANBENITOWATERDISTRICT') |
                            (df_historical.Agency_Name == 'SANTACLARAVALLEYWD')] = 'pachecotunnel'

df_historical.Agency_Group.loc[(df_historical.Agency_Name == 'SANLUISOBISPOCOUNTYFC&WCD') |
                            (df_historical.Agency_Name == 'SANTABARBARACOUNTYFC&WCD')] = 'centralcoast'

df_historical.Agency_Group.loc[(df_historical.Agency_Name == 'HILLSVALLEYIRRIGATIONDISTRICT')] = 'other_maderacanal'

df_historical.Agency_Group.loc[(df_historical.Agency_Name == 'CITYOFDOSPALOS') |
                            (df_historical.Agency_Name == 'MERCEDIRRIGATIONDISTRICT')] = 'other_mercedco'

df_historical.Agency_Group.loc[(df_historical.Agency_Name == 'BROADVIEWWATERDISTRICT') |
                            (df_historical.Agency_Name == 'CITYOFCOALINGA') |
                            (df_historical.Agency_Name == 'CITYOFHURON') |
                            (df_historical.Agency_Name == 'COUNTYOFFRESNO') |
                            (df_historical.Agency_Name == 'PANOCHEWATERDISTRICT')] = 'other_fresnoco'

df_historical.Agency_Group.loc[(df_historical.Agency_Name == 'AVENAL,CITYOF') |
                            (df_historical.Agency_Name == 'AvenalStatePrison') |
                            (df_historical.Agency_Name == 'COUNTYOFKINGS') |
                            (df_historical.Agency_Name == 'EMPIREWESTSIDEID')] = 'other_kingsco'

df_historical.Agency_Group.loc[(df_historical.Agency_Name == 'COUNTYOFTULARE') |
                            (df_historical.Agency_Name == 'PIXLEYIRRIGATIONDISTRICT')] = 'other_tulareco'

df_historical.Agency_Group.loc[(df_historical.Agency_Name == 'RAGGULCHWATERDISTRICT')] = 'other_kernco'

df_historical.Agency_Group.loc[(df_historical.Agency_Name == 'ANTELOPEVALLEY-EASTKERNWA') |
                            (df_historical.Agency_Name == 'CASTAICLAKEWA') |
                            (df_historical.Agency_Name == 'COACHELLAVALLEYWD') |
                            (df_historical.Agency_Name == 'CRESTLINE-LAKEARROWHEADWA') |
                            (df_historical.Agency_Name == 'DESERTWATERAGENCY') |
                            (df_historical.Agency_Name == 'LITTLEROCKCREEKID') |
                            (df_historical.Agency_Name == 'MOJAVEWATERAGENCY') |
                            (df_historical.Agency_Name == 'PALMDALEWATERDISTRICT') |
                            (df_historical.Agency_Name == 'SANBERNARDINOVALLEYMWD') |
                            (df_historical.Agency_Name == 'SANGABRIELVALLEYMWD') |
                            (df_historical.Agency_Name == 'SANGORGONIOPASSWA') |
                            (df_historical.Agency_Name == 'THEMETROPOLITANWATERDISTRICTOF') |
                            (df_historical.Agency_Name == 'VENTURACOUNTYWPD')] = 'socal'

df_historical.Agency_Group.loc[(df_historical.Agency_Name == 'CADEPTOFFISHANDGAME') |
                            (df_historical.Agency_Name == 'CADEPTOFPARKSANDRECREATION') |
                            (df_historical.Agency_Name == 'CADEPTOFWATERRESOURCES') |
                            (df_historical.Agency_Name == 'EWA-STATE') |
                            (df_historical.Agency_Name == 'KERNNATIONALWILDLIFEREFUGE') |
                            (df_historical.Agency_Name == "SANJOAQUINVALLEYNAT'LCEMETERY") |
                            (df_historical.Agency_Name == 'USBUREAUOFRECLAMATION')] = 'statefederal'


# now split up KCWA contractors using Reach numbers from Table 22 of State Water Project Operations Data monthly report (Dec 1998 and Jun 2017)
# R8D is either DLR or TLB or County of Kings according to pdf, but only one here says DLR for Bill_To_Agency_Name
df_historical.Agency_Group.loc[(df_historical.Agency_Group == 'kcwa') &
                            (df_historical.To_Reach == 'VCA-R8D')] = 'LHL'
# R9 Lost Hills or Berrenda Mesa
df_historical.Agency_Group.loc[(df_historical.Agency_Group == 'kcwa') &
                            (df_historical.To_Reach == 'VCA-R9')] = 'LHL'
# R10A many possibilities
df_historical.Agency_Group.loc[(df_historical.Agency_Group == 'kcwa') &
                            (df_historical.To_Reach == 'VCA-R10A')] = 'LHL_BLR_BVA_SMI_statefederal'
# R11B always Belridge
df_historical.Agency_Group.loc[(df_historical.Agency_Group == 'kcwa') &
                            (df_historical.To_Reach == 'VCA-R11B')] = 'BLR'
# R12D Belridge or West Kern
df_historical.Agency_Group.loc[(df_historical.Agency_Group == 'kcwa') &
                            (df_historical.To_Reach == 'VCA-R12D')] = 'BLR_WKN'
# R12E many possibilities, including CVC
df_historical.Agency_Group.loc[(df_historical.Agency_Group == 'kcwa') &
                            (df_historical.To_Reach == 'VCA-R12E')] = 'BVA_LWT_TUL_COF_pixley_haciendaDWR_CVC-KCWA_CVC-DLR_CVC-BVA_ARV'
# R13B buena vista, henry miller, or kern water bank in/out
df_historical.Agency_Group.loc[(df_historical.Agency_Group == 'kcwa') &
                            (df_historical.To_Reach == 'VCA-R13B')] = 'BVA_HML_KWB'
# R14A West Kern or Wheeler Ridge-Maricopa
df_historical.Agency_Group.loc[(df_historical.Agency_Group == 'kcwa') &
                            (df_historical.To_Reach == 'VCA-R14A')] = 'WKN_WRM'
# R14B always Wheeler Ridge-Maricopa
df_historical.Agency_Group.loc[(df_historical.Agency_Group == 'kcwa') &
                            (df_historical.To_Reach == 'VCA-R14B')] = 'WRM'
# R14C WRM or arvin
df_historical.Agency_Group.loc[(df_historical.Agency_Group == 'kcwa') &
                            (df_historical.To_Reach == 'VCA-R14C')] = 'WRM_ARV'
# R15A WRM
df_historical.Agency_Group.loc[(df_historical.Agency_Group == 'kcwa') &
                            (df_historical.To_Reach == 'VCA-R15A')] = 'WRM'
# R16A Wheeler Ridge-Maricopa or Tehachapi Cummings
df_historical.Agency_Group.loc[(df_historical.Agency_Group == 'kcwa') &
                            (df_historical.To_Reach == 'VCA-R16A')] = 'WRM_THC'
# R31A is start of Coastal Branch - berrenda mesa is only kcwa
df_historical.Agency_Group.loc[(df_historical.Agency_Group == 'kcwa') &
                            (df_historical.To_Reach == 'VCB1-R31A')] = 'BDM'
# R17E is start of East Branch after Edmonston pumping plant - Tejon-Castac has delivery
df_historical.Agency_Group.loc[(df_historical.Agency_Group == 'kcwa') &
                            (df_historical.To_Reach == 'VCA-R17E')] = 'TJC'
# Rest are unknown - don't see any kcwa members in pdfs. Reaches VCA-R3A, VCA-R4, VCB2-R33A.
df_historical.Agency_Group.loc[(df_historical.Agency_Group == 'kcwa')] = 'kcwa_unknown'





# now aggregate by water types into categories used by ORCA (See SWP_waterTypes_Lookup.csv)
df_historical['WT_model'] = 'other'
df_historical['banking_partner'] = 'none'

# TableA delivery
df_historical.WT_model.loc[(df_historical.Water_Type == 'TBLA01') |
                        (df_historical.Water_Type == 'TBLA02') |
                        (df_historical.Water_Type == 'TBLA07') |
                        (df_historical.Water_Type == 'TBLA08') |
                        (df_historical.Water_Type == 'TBLAADV') |
                        (df_historical.WT_Group == 'TableA')
                        ] = 'tableA_delivery'
# TableA flood (Article 21)
df_historical.WT_model.loc[df_historical.WT_Group == 'Article21'] = 'tableA_flood'

# TableA turnback - also set sign -1 for sold water
df_historical.WT_model.loc[(df_historical.WT_Group == 'Bought') |
                        (df_historical.WT_Group == 'Sold-CO') |
                        (df_historical.WT_Group == 'Sold-TBLA') |
                        (df_historical.WT_Group == 'TurnbackPools')
                        ] = 'tableA_turnback'

df_historical.delivery_taf.loc[(df_historical.WT_Group == 'Sold-CO') | (df_historical.WT_Group == 'Sold-TBLA')] = \
  -df_historical.delivery_taf.loc[(df_historical.WT_Group == 'Sold-CO') | (df_historical.WT_Group == 'Sold-TBLA')]

# TableA carryover
df_historical.WT_model.loc[(df_historical.WT_Group == 'Carryover') |
                        (df_historical.WT_Group == 'SLRStorageCarryover')
                        ] = 'tableA_carryover'

# cvc delivery
df_historical.WT_model.loc[(df_historical.Water_Type == 'CVCSPLY') |
                        (df_historical.Water_Type == 'JNTPNTCVC') |
                        (df_historical.Water_Type == 'CVCENT') |
                        (df_historical.Water_Type == 'CVC-OVER') |
                        (df_historical.Water_Type == 'CVCPOD') |
                        (df_historical.Water_Type == 'CVCTRN') |
                        (df_historical.Water_Type == 'OPERXCH') |
                        ((df_historical.Water_Type == 'CVPSPLY') &
                         ((df_historical.Agency_Name == 'KERNCOUNTYWA') |
                          (df_historical.Agency_Name == 'COUNTYOFFRESNO') |
                          (df_historical.Agency_Name == 'COUNTYOFTULARE') |
                          (df_historical.Agency_Name == 'TULARELAKEBASINWSD') |
                          (df_historical.Agency_Name == 'HILLSVALLEYIRRIGATIONDISTRICT') |
                          (df_historical.Agency_Name == 'TRI-VALLEYWATERDISTRICT') |
                          (df_historical.Agency_Name == 'LOWERTULERIVER')))
                        ] = 'cvc_delivery'

# cvc flood
df_historical.WT_model.loc[df_historical.WT_Group == 'CVC215'] = 'cvc_flood'

# cvc undelivered
df_historical.WT_model.loc[df_historical.WT_Group == 'CVCREMAIN'] = 'cvc_undelivered'

# cvpdelta delivery
df_historical.WT_model.loc[(df_historical.Water_Type == 'CVPPOD') |
                        (df_historical.Water_Type == 'DCVCCN') |
                        (df_historical.Water_Type == 'JNTPNT') |
                        ((df_historical.Water_Type == 'CVPSPLY') &
                         ((df_historical.Agency_Name == 'SANTACLARAVALLEYWD') |
                          (df_historical.Agency_Name == 'USBUREAUOFRECLAMATION')|
                          (df_historical.Agency_Name == 'THEMETROPOLITANWATERDISTRICTOF')))
                        ] = 'cvpdelta_delivery'

# banking recovery. Also get banking partner from key.
df_historical.WT_model.loc[(df_historical.Water_Type == 'CXAERV') |
                        (df_historical.Water_Type == 'CXKBRV') |
                        (df_historical.Water_Type == 'CXSTRV') |
                        (df_historical.Water_Type == 'CXKDRV') |
                        (df_historical.WT_Group == 'WaterBankPumpin') |
                        (df_historical.WT_Group == 'WaterBankRecovery')
                        ] = 'recover_banked'
df_historical.banking_partner.loc[df_historical.WT_Group == 'CXAERV'] = 'AEMWD'
df_historical.banking_partner.loc[df_historical.WT_Group == 'CXKBRV'] = 'KWB'
df_historical.banking_partner.loc[df_historical.WT_Group == 'CXSTRV'] = 'SMI'
df_historical.banking_partner.loc[df_historical.WT_Group == 'CXKDRV'] = 'KND'
df_historical.banking_partner.loc[df_historical.WT_Group == 'PUMPINAE'] = 'AEMWD'
df_historical.banking_partner.loc[df_historical.WT_Group == 'PUMPINKD'] = 'KND'
df_historical.banking_partner.loc[df_historical.WT_Group == 'PUMPINKWB'] = 'KWB'
df_historical.banking_partner.loc[df_historical.WT_Group == 'PUMPINST'] = 'SMI'
df_historical.banking_partner.loc[df_historical.WT_Group == '78RCV'] = 'SOC'
df_historical.banking_partner.loc[df_historical.WT_Group == '82RCV'] = 'SOC'
df_historical.banking_partner.loc[df_historical.WT_Group == 'KWBRCV'] = 'KWB'
df_historical.banking_partner.loc[df_historical.WT_Group == 'STEWA'] = 'SMI'
df_historical.banking_partner.loc[df_historical.WT_Group == 'STEWA-X'] = 'SMI'
df_historical.banking_partner.loc[df_historical.WT_Group == 'STRCV'] = 'SMI'
df_historical.banking_partner.loc[df_historical.WT_Group == 'STRCV-X'] = 'SMI'

# exchanged Table A surface water. Agency gets delivery of water from banking partner, gives parnter paper TBLA credit.
df_historical.WT_model.loc[(df_historical.Water_Type == 'TBLAXAE') |
                        (df_historical.Water_Type == 'TBLAXKD') |
                        (df_historical.Water_Type == 'TBLAXKWB') |
                        (df_historical.Water_Type == 'TBLAXST') |
                        (df_historical.Water_Type == 'TBLAXSPLY')
                        ] = 'exchange_SW'
df_historical.banking_partner.loc[df_historical.WT_Group == 'TBLAXAE'] = 'AEMWD'
df_historical.banking_partner.loc[df_historical.WT_Group == 'TBLAXKD'] = 'KND'
df_historical.banking_partner.loc[df_historical.WT_Group == 'TBLAXKWB'] = 'KWB'
df_historical.banking_partner.loc[df_historical.WT_Group == 'TBLAXST'] = 'SMI'

# create indicator variable to decide if should be included in total deliveries count
df_historical['is_delivery'] = 0
df_historical['is_delivery'].loc[df_historical.WT_model == 'tableA_delivery'] = 1
df_historical['is_delivery'].loc[df_historical.WT_model == 'tableA_flood'] = 1
df_historical['is_delivery'].loc[df_historical.WT_model == 'cvc_delivery'] = 1
df_historical['is_delivery'].loc[df_historical.WT_model == 'cvc_flood'] = 1
df_historical['is_delivery'].loc[df_historical.WT_model == 'cvpdelta_delivery'] = 1
df_historical['is_delivery'].loc[df_historical.WT_model == 'recover_banked'] = 1






#
# ### plot historical deliveries
# dum =  (df_historical.To_Reach == 'VCA-R12E') & (df_historical.delivery_taf > 0)
# dum2 = dum & (df_historical.WT_model == 'tableA_delivery')
# dum3 = dum & (df_historical.WT_model == 'tableA_flood')
# dum4 = dum & (df_historical.WT_model == 'tableA_turnback')
# dum5 = dum & (df_historical.WT_model == 'tableA_carryover')
# dum6 = dum & (df_historical.WT_model == 'recover_banked')
# dum7 = dum & (df_historical.WT_model == 'exchange_SW')
# dum8 = dum & (df_historical.WT_model == 'other')
#
# plt.plot_date(df_historical['Date'].loc[dum2], df_historical['delivery_taf'].loc[dum2], marker='o', alpha=0.3)
# plt.plot_date(df_historical['Date'].loc[dum3], df_historical['delivery_taf'].loc[dum3], marker='o', alpha=0.3)
# plt.plot_date(df_historical['Date'].loc[dum4], df_historical['delivery_taf'].loc[dum4], marker='o', alpha=0.3)
# plt.plot_date(df_historical['Date'].loc[dum5], df_historical['delivery_taf'].loc[dum5], marker='o', alpha=0.3)
# plt.plot_date(df_historical['Date'].loc[dum6], df_historical['delivery_taf'].loc[dum6], marker='o', alpha=0.3)
# plt.plot_date(df_historical['Date'].loc[dum7], df_historical['delivery_taf'].loc[dum7], marker='o', alpha=0.3)
# plt.plot_date(df_historical['Date'].loc[dum8], df_historical['delivery_taf'].loc[dum8], marker='o', alpha=0.3)
# plt.legend(['delivery','flood','turnback','carryover','recovery','exchange_SW', 'other'])



# aggregate by Year-Month-Agency_Group-WT_model
df_historical['Year__Month__Agency_Group__WT_model'] = df_historical.Year.map(str) + '__' + df_historical.Month.map(str) + '__' + df_historical.Agency_Group + '__' + df_historical.WT_model
df_historical_aggregate = df_historical.groupby(by = ['Year__Month__Agency_Group__WT_model']).sum()
df_historical_aggregate['Year'] = df_historical.groupby(by = ['Year__Month__Agency_Group__WT_model'])['Year'].first()
df_historical_aggregate['Month'] = df_historical.groupby(by = ['Year__Month__Agency_Group__WT_model'])['Month'].first()
df_historical_aggregate['Day'] = 1
df_historical_aggregate['Wateryear'] = df_historical.groupby(by = ['Year__Month__Agency_Group__WT_model'])['Wateryear'].first()
df_historical_aggregate['Agency_Group'] = df_historical.groupby(by = ['Year__Month__Agency_Group__WT_model'])['Agency_Group'].first()
df_historical_aggregate['WT_model'] = df_historical.groupby(by = ['Year__Month__Agency_Group__WT_model'])['WT_model'].first()
df_historical_aggregate['Date'] = pd.to_datetime(df_historical_aggregate[['Year','Month','Day']])
df_historical_aggregate = df_historical_aggregate.sort_values(by=['Date'])

# aggregate by Year-Month-Agency_Group, only for is_delivery==1 (should be approximately total deliveries, but not sure about 'other' water types)
df_historical_deliveries = df_historical.loc[df_historical.is_delivery == 1]
df_historical_deliveries['Year__Month__Agency_Group'] = df_historical_deliveries.Year.map(str) + '__' + df_historical_deliveries.Month.map(str) + '__' + df_historical_deliveries.Agency_Group
df_historical_deliveries_aggregate = df_historical_deliveries.groupby(by = ['Year__Month__Agency_Group']).sum()
df_historical_deliveries_aggregate['Year'] = df_historical_deliveries.groupby(by = ['Year__Month__Agency_Group'])['Year'].first()
df_historical_deliveries_aggregate['Month'] = df_historical_deliveries.groupby(by = ['Year__Month__Agency_Group'])['Month'].first()
df_historical_deliveries_aggregate['Day'] = 1
df_historical_deliveries_aggregate['Wateryear'] = df_historical_deliveries.groupby(by = ['Year__Month__Agency_Group'])['Wateryear'].first()
df_historical_deliveries_aggregate['Agency_Group'] = df_historical_deliveries.groupby(by = ['Year__Month__Agency_Group'])['Agency_Group'].first()
df_historical_deliveries_aggregate['Date'] = pd.to_datetime(df_historical_deliveries_aggregate[['Year','Month','Day']])
df_historical_deliveries_aggregate = df_historical_deliveries_aggregate.sort_values(by=['Date'])







### Now read in modeled daily district delivery data
df_modeled = pd.read_csv('cord/data/results/district_results_full_validation.csv', index_col=0, parse_dates=True)

# aggregate monthly sum
df_modeled = df_modeled.resample('M').last()
df_modeled['Year__'] = df_modeled.index.year
df_modeled['Month__'] = df_modeled.index.month
df_modeled['Wateryear__'] = df_modeled.Year__
df_modeled.Wateryear__.loc[df_modeled.Month__ > 9] = df_modeled.Wateryear__.loc[df_modeled.Month__ > 9] + 1

# get district and water delivery type
districts_modeled = df_modeled.columns.map(lambda x: x.split('_')[0])
WT_modeled = df_modeled.columns.map(lambda x: x.split('_',1)[1])
# source_modeled = df_modeled.columns.map(lambda x: x.split('_')[-1])
# source_modeled[source_modeled in ['recharged', 'GW', 'banked', 'SW', 'inleiu', 'leiupumping', 'trades']] = 'none'
# source_modeled[tuple(x in ['Year', 'Month', 'Wateryear'] for x in source_modeled)] = 'NA'
df_modeled['Year'] = df_modeled['Year__']
df_modeled['Month'] = df_modeled['Month__']
df_modeled['Wateryear'] = df_modeled['Wateryear__']
del df_modeled['Year__'], df_modeled['Month__'], df_modeled['Wateryear__']

# deliveries are cumulative over water year, so difference to get monthly deliveries
# df_modeled['Date'] = df_modeled.index
# df_modeled.index = range(df_modeled.shape[0])
ind = np.where(WT_modeled == 'tableA_delivery')[0]
for i in ind:
  for wy in range(min(df_modeled.Wateryear), max(df_modeled.Wateryear)+1):
    startDay = np.where(df_modeled.Wateryear == wy)[0][0]
    df_modeled.iloc[(startDay+1):(startDay+12), i] = np.diff(df_modeled.iloc[(startDay):(startDay+12), i])




### plot historical & modeled deliveries

# ### plot historical aggregate deliveries
# dum =  (df_historical_aggregate.Agency_Group == 'DLR')
# dum2 = dum & (df_historical_aggregate.WT_model == 'tableA_delivery')
# # dum3 = dum & (df_historical.WT_model == 'tableA_flood')
# # dum4 = dum & (df_historical.WT_model == 'tableA_turnback')
# # dum5 = dum & (df_historical.WT_model == 'tableA_carryover')
# # dum6 = dum & (df_historical.WT_model == 'recover_banked')
# # dum7 = dum & (df_historical.WT_model == 'exchange_SW')
# # dum8 = dum & (df_historical.WT_model == 'other')
#
# plt.plot_date(df_historical_aggregate['Date'].loc[dum2], df_historical_aggregate['delivery_taf'].loc[dum2],fmt='-')
# # plt.plot_date(df_historical['Date'].loc[dum3], df_historical['delivery_taf'].loc[dum3], marker='o', alpha=0.3)
# # plt.plot_date(df_historical['Date'].loc[dum4], df_historical['delivery_taf'].loc[dum4], marker='o', alpha=0.3)
# # plt.plot_date(df_historical['Date'].loc[dum5], df_historical['delivery_taf'].loc[dum5], marker='o', alpha=0.3)
# # plt.plot_date(df_historical['Date'].loc[dum6], df_historical['delivery_taf'].loc[dum6], marker='o', alpha=0.3)
# # plt.plot_date(df_historical['Date'].loc[dum7], df_historical['delivery_taf'].loc[dum7], marker='o', alpha=0.3)
# # plt.plot_date(df_historical['Date'].loc[dum8], df_historical['delivery_taf'].loc[dum8], marker='o', alpha=0.3)
# # plt.legend(['delivery','flood','turnback','carryover','recovery','exchange_SW', 'other'])

### plot historical aggregate deliveries
dum =  (df_historical_deliveries_aggregate.Agency_Group == 'DLR')
plt.plot_date(df_historical_deliveries_aggregate['Date'].loc[dum], df_historical_deliveries_aggregate['delivery_taf'].loc[dum],fmt='-')


ind = (districts_modeled == 'DLR')&(WT_modeled == 'tableA_delivery')
plt.plot(df_modeled.loc[:, ind])


