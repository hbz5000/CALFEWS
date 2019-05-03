import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

###############################################################################
### State Water Project #######################################################
###############################################################################

### First read, clean, organizing historical SWP delivery data, to be compared with modeled deliveries
# Read data ~~NOTE: before running this, save xlsx as csv, then manually fix column names by removing lead/trail whitespace, and replacing spaces between words with _
deliveries = pd.read_csv("cord/data/input/SWP_delivery_data_2000_2018.csv")

# Clean white space, etc
deliveries.To_Reach = deliveries.To_Reach.apply(lambda x: x.replace(' ',''))
deliveries.Turnout = deliveries.Turnout.apply(lambda x: x.replace(' ',''))
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
swp_historical = pd.DataFrame(index=range(deliveries.shape[0]*12))
swp_historical['Year'] = 0
swp_historical['Month'] = 0
swp_historical['Day'] = 1
swp_historical['Wateryear'] = 0
swp_historical['Bill_To_Agency_Name'] = ' '
swp_historical['Agency_Name'] = ' '
swp_historical['Water_Type'] = ' '
swp_historical['WT_Group'] = ' '
swp_historical['To_Reach'] = ' '
swp_historical['Turnout'] = ' '
swp_historical['delivery_taf'] = 0.0

dum = np.repeat(np.arange(deliveries.shape[0]), 12)
for n in ['Year','Bill_To_Agency_Name','Agency_Name','Water_Type','WT_Group','To_Reach','Turnout']:
  swp_historical[n] = deliveries.iloc[dum][n].values
swp_historical['Month'] = np.tile(np.arange(1,13), deliveries.shape[0])
swp_historical['Wateryear'] = swp_historical['Year']
swp_historical['Wateryear'].loc[swp_historical['Month'] > 9] = swp_historical['Wateryear'].loc[swp_historical['Month'] > 9] + 1

swp_historical['delivery_taf'].iloc[0:swp_historical.shape[0]:12] = deliveries['JAN'].values / 1000
swp_historical['delivery_taf'].iloc[1:swp_historical.shape[0]:12] = deliveries['FEB'].values / 1000
swp_historical['delivery_taf'].iloc[2:swp_historical.shape[0]:12] = deliveries['MAR'].values / 1000
swp_historical['delivery_taf'].iloc[3:swp_historical.shape[0]:12] = deliveries['APR'].values / 1000
swp_historical['delivery_taf'].iloc[4:swp_historical.shape[0]:12] = deliveries['MAY'].values / 1000
swp_historical['delivery_taf'].iloc[5:swp_historical.shape[0]:12] = deliveries['JUN'].values / 1000
swp_historical['delivery_taf'].iloc[6:swp_historical.shape[0]:12] = deliveries['JUL'].values / 1000
swp_historical['delivery_taf'].iloc[7:swp_historical.shape[0]:12] = deliveries['AUG'].values / 1000
swp_historical['delivery_taf'].iloc[8:swp_historical.shape[0]:12] = deliveries['SEP'].values / 1000
swp_historical['delivery_taf'].iloc[9:swp_historical.shape[0]:12] = deliveries['OCT'].values / 1000
swp_historical['delivery_taf'].iloc[10:swp_historical.shape[0]:12] = deliveries['NOV'].values / 1000
swp_historical['delivery_taf'].iloc[11:swp_historical.shape[0]:12] = deliveries['DEC'].values / 1000

swp_historical['Date'] = pd.to_datetime(swp_historical[['Year','Month','Day']])
del deliveries

# plt.plot_date(swp_historical['Date'], swp_historical['delivery_taf'], marker='o', alpha=0.3)


# aggregate different groups/reaches together for comparison to model output. See "model.py", initialize_water_districts function, for district 3-letter uppercase abbreviations
swp_historical['Agency_Group'] = 'other'
swp_historical.Agency_Group.loc[swp_historical.Agency_Name == 'DUDLEYRIDGEWATERDISTRICT'] = 'DLR'
swp_historical.Agency_Group.loc[swp_historical.Agency_Name == 'TULARELAKEBASINWSD'] = 'TLB'
swp_historical.Agency_Group.loc[swp_historical.Agency_Name == 'WESTLANDSWATERDISTRICT'] = 'WSL'
swp_historical.Agency_Group.loc[swp_historical.Agency_Name == 'MADERAIRRIGATIONDISTRICT'] = 'MAD'

swp_historical.Agency_Group.loc[swp_historical.Agency_Name == 'KERN-TULAREWATERDISTRICT'] = 'KRT'
swp_historical.Agency_Group.loc[swp_historical.Agency_Name == 'LOWERTULERIVER'] = 'LWT'

swp_historical.Agency_Group.loc[swp_historical.Agency_Name == 'KERNCOUNTYWA'] = 'kcwa'
swp_historical.Agency_Group.loc[swp_historical.Agency_Name == 'FRIANTWATERUSERSAUTHORITY'] = 'fwua'

swp_historical.Agency_Group.loc[(swp_historical.Agency_Name == 'BROWNSVALLEYIRRIGATIONDIST') |
                            (swp_historical.Agency_Name == 'BUTTEWATERDISTRICT') |
                            (swp_historical.Agency_Name == 'CITYOFYUBACITY') |
                            (swp_historical.Agency_Name == 'COUNTYOFBUTTE') |
                            (swp_historical.Agency_Name == 'GARDENHIGHWAYMUTUALWATERCOMPANY') |
                            (swp_historical.Agency_Name == 'PLACERCOUNTYWATERAGENCY') |
                            (swp_historical.Agency_Name == 'PLUMASMUTUALWATERCOMPANY') |
                            (swp_historical.Agency_Name == 'RICHVALEIRRIGATIONDISTRICT') |
                            (swp_historical.Agency_Name == 'SOUTHFEATHERWATER&POWERAGENCY') |
                            (swp_historical.Agency_Name == 'SOUTHSUTTERWATERDISTRICT') |
                            (swp_historical.Agency_Name == 'SUTTEREXTENSIONWATERDISTRICT') |
                            (swp_historical.Agency_Name == 'THERMALITOWATERANDSEWERDISTRICT') |
                            (swp_historical.Agency_Name == 'WESTERNCANALWATERDISTRICT')] = 'sacramentoriver'

swp_historical.Agency_Group.loc[(swp_historical.Agency_Name == 'NAPACOUNTYFC&WCD') |
                            (swp_historical.Agency_Name == 'SOLANOCOUNTYWATERAGENCY')] = 'northbay'

swp_historical.Agency_Group.loc[(swp_historical.Agency_Name == 'ALAMEDACOUNTYFC&WCD-ZONE7') |
                            (swp_historical.Agency_Name == 'TRI-VALLEYWATERDISTRICT') |
                            (swp_historical.Agency_Name == 'ALAMEDACOUNTYWD')] = 'southbay'

swp_historical.Agency_Group.loc[(swp_historical.Agency_Name == 'CITYOFTRACY')] = 'delta'

swp_historical.Agency_Group.loc[(swp_historical.Agency_Name == 'DELPUERTOWATERDISTRICT') |
                            (swp_historical.Agency_Name == 'OAKFLATWATERDISTRICT') |
                            (swp_historical.Agency_Name == 'SANLUISWATERDISTRICT') |
                            (swp_historical.Agency_Name == 'SanLuis&DeltaMendotaWaterAuth') |
                            (swp_historical.Agency_Name == 'TRANQUILLITYIRRIGATIONDISTRICT')] = 'deltamendotacanal'

swp_historical.Agency_Group.loc[(swp_historical.Agency_Name == 'PACHECOPASSWATERDISTRICT') |
                            (swp_historical.Agency_Name == 'SANBENITOWATERDISTRICT') |
                            (swp_historical.Agency_Name == 'SANTACLARAVALLEYWD')] = 'pachecotunnel'

swp_historical.Agency_Group.loc[(swp_historical.Agency_Name == 'SANLUISOBISPOCOUNTYFC&WCD') |
                            (swp_historical.Agency_Name == 'SANTABARBARACOUNTYFC&WCD')] = 'centralcoast'

swp_historical.Agency_Group.loc[(swp_historical.Agency_Name == 'HILLSVALLEYIRRIGATIONDISTRICT')] = 'other_maderacanal'

swp_historical.Agency_Group.loc[(swp_historical.Agency_Name == 'CITYOFDOSPALOS') |
                            (swp_historical.Agency_Name == 'MERCEDIRRIGATIONDISTRICT')] = 'other_mercedco'

swp_historical.Agency_Group.loc[(swp_historical.Agency_Name == 'BROADVIEWWATERDISTRICT') |
                            (swp_historical.Agency_Name == 'CITYOFCOALINGA') |
                            (swp_historical.Agency_Name == 'CITYOFHURON') |
                            (swp_historical.Agency_Name == 'COUNTYOFFRESNO') |
                            (swp_historical.Agency_Name == 'PANOCHEWATERDISTRICT')] = 'other_fresnoco'

swp_historical.Agency_Group.loc[(swp_historical.Agency_Name == 'AVENAL,CITYOF') |
                            (swp_historical.Agency_Name == 'AvenalStatePrison') |
                            (swp_historical.Agency_Name == 'COUNTYOFKINGS') |
                            (swp_historical.Agency_Name == 'EMPIREWESTSIDEID')] = 'other_kingsco'

swp_historical.Agency_Group.loc[(swp_historical.Agency_Name == 'COUNTYOFTULARE') |
                            (swp_historical.Agency_Name == 'PIXLEYIRRIGATIONDISTRICT')] = 'other_tulareco'

swp_historical.Agency_Group.loc[(swp_historical.Agency_Name == 'RAGGULCHWATERDISTRICT')] = 'other_kernco'

swp_historical.Agency_Group.loc[(swp_historical.Agency_Name == 'ANTELOPEVALLEY-EASTKERNWA') |
                            (swp_historical.Agency_Name == 'CASTAICLAKEWA') |
                            (swp_historical.Agency_Name == 'COACHELLAVALLEYWD') |
                            (swp_historical.Agency_Name == 'CRESTLINE-LAKEARROWHEADWA') |
                            (swp_historical.Agency_Name == 'DESERTWATERAGENCY') |
                            (swp_historical.Agency_Name == 'LITTLEROCKCREEKID') |
                            (swp_historical.Agency_Name == 'MOJAVEWATERAGENCY') |
                            (swp_historical.Agency_Name == 'PALMDALEWATERDISTRICT') |
                            (swp_historical.Agency_Name == 'SANBERNARDINOVALLEYMWD') |
                            (swp_historical.Agency_Name == 'SANGABRIELVALLEYMWD') |
                            (swp_historical.Agency_Name == 'SANGORGONIOPASSWA') |
                            (swp_historical.Agency_Name == 'THEMETROPOLITANWATERDISTRICTOF') |
                            (swp_historical.Agency_Name == 'VENTURACOUNTYWPD')] = 'socal'

swp_historical.Agency_Group.loc[(swp_historical.Agency_Name == 'CADEPTOFFISHANDGAME') |
                            (swp_historical.Agency_Name == 'CADEPTOFPARKSANDRECREATION') |
                            (swp_historical.Agency_Name == 'CADEPTOFWATERRESOURCES') |
                            (swp_historical.Agency_Name == 'EWA-STATE') |
                            (swp_historical.Agency_Name == 'KERNNATIONALWILDLIFEREFUGE') |
                            (swp_historical.Agency_Name == "SANJOAQUINVALLEYNAT'LCEMETERY") |
                            (swp_historical.Agency_Name == 'USBUREAUOFRECLAMATION')] = 'statefederal'


# now split up KCWA contractors using Reach numbers from Table 22 of State Water Project Operations Data monthly report (Dec 1998 and Jun 2017)
# R8D is either DLR or TLB or County of Kings according to pdf, but only one here says DLR for Bill_To_Agency_Name
swp_historical.Agency_Group.loc[(swp_historical.Agency_Group == 'kcwa') &
                            (swp_historical.To_Reach == 'VCA-R8D')] = 'LHL'
# R9 Lost Hills or Berrenda Mesa
swp_historical.Agency_Group.loc[(swp_historical.Agency_Group == 'kcwa') &
                            (swp_historical.To_Reach == 'VCA-R9')] = 'LHL'
# R10A - divide by turnout (see SWP_turnouts.csv)
swp_historical.Agency_Group.loc[(swp_historical.Agency_Group == 'kcwa') &
                            (swp_historical.To_Reach == 'VCA-R10A') &
                            ((swp_historical.Turnout == 'T219') |
                             (swp_historical.Turnout == 'T220') |
                             (swp_historical.Turnout == 'T221'))] = 'LHL'
swp_historical.Agency_Group.loc[(swp_historical.Agency_Group == 'kcwa') &
                               (swp_historical.To_Reach == 'VCA-R10A') &
                               ((swp_historical.Turnout == 'T395') |
                                (swp_historical.Turnout == 'T225'))] = 'SMI'
swp_historical.Agency_Group.loc[(swp_historical.Agency_Group == 'kcwa') &
                               (swp_historical.To_Reach == 'VCA-R10A') &
                               (swp_historical.Turnout == 'T224')] = 'BLR'
swp_historical.Agency_Group.loc[(swp_historical.Agency_Group == 'kcwa') &
                               (swp_historical.To_Reach == 'VCA-R10A') &
                               (swp_historical.Turnout == 'T228')] = 'BVA_statefederal'
# R11B always Belridge
swp_historical.Agency_Group.loc[(swp_historical.Agency_Group == 'kcwa') &
                            (swp_historical.To_Reach == 'VCA-R11B')] = 'BLR'
# R12D - only turnout can be Belridge or West Kern
swp_historical.Agency_Group.loc[(swp_historical.Agency_Group == 'kcwa') &
                            (swp_historical.To_Reach == 'VCA-R12D')] = 'BLR_WKN'
# R12E - divide by turnout (see SWP_turnouts.csv)
swp_historical.Agency_Group.loc[(swp_historical.Agency_Group == 'kcwa') &
                            (swp_historical.To_Reach == 'VCA-R12E') &
                            ((swp_historical.Turnout == 'T235') |
                             (swp_historical.Turnout == 'T236') |
                             (swp_historical.Turnout == 'T433'))] = 'BVA'
swp_historical.Agency_Group.loc[(swp_historical.Agency_Group == 'kcwa') &
                            (swp_historical.To_Reach == 'VCA-R12E')] = 'CVC-KCWA_CVC-DLR_CVC-BVA_ARV_LWT_TUL_COF_pixley_haciendaDWR'
# R13B - divide by turnout (see SWP_turnouts.csv)
swp_historical.Agency_Group.loc[(swp_historical.Agency_Group == 'kcwa') &
                               (swp_historical.To_Reach == 'VCA-R13B') &
                               ((swp_historical.Turnout == 'T242') |
                                (swp_historical.Turnout == 'T245'))] = 'BVA_HML'
swp_historical.Agency_Group.loc[(swp_historical.Agency_Group == 'kcwa') &
                               (swp_historical.To_Reach == 'VCA-R13B') &
                               (swp_historical.Turnout == 'T244')] = 'KWB'
swp_historical.Agency_Group.loc[(swp_historical.Agency_Group == 'kcwa') &
                               (swp_historical.To_Reach == 'VCA-R13B') &
                               (swp_historical.Turnout == 'T241')] = 'BVA'
# R14A - divide by turnout (see SWP_turnouts.csv)
swp_historical.Agency_Group.loc[(swp_historical.Agency_Group == 'kcwa') &
                            (swp_historical.To_Reach == 'VCA-R14A') &
                            ((swp_historical.Turnout == 'T247') |
                             (swp_historical.Turnout == 'T248') |
                             (swp_historical.Turnout == 'T249'))] = 'WRM'
swp_historical.Agency_Group.loc[(swp_historical.Agency_Group == 'kcwa') &
                            (swp_historical.To_Reach == 'VCA-R14A')] = 'WKN'
# R14B always Wheeler Ridge-Maricopa
swp_historical.Agency_Group.loc[(swp_historical.Agency_Group == 'kcwa') &
                            (swp_historical.To_Reach == 'VCA-R14B')] = 'WRM'
# R14C - divide by turnout (see SWP_turnouts.csv)
swp_historical.Agency_Group.loc[(swp_historical.Agency_Group == 'kcwa') &
                            (swp_historical.To_Reach == 'VCA-R14C') &
                            ((swp_historical.Turnout == 'T253') |
                             (swp_historical.Turnout == 'T254'))] = 'WRM'
swp_historical.Agency_Group.loc[(swp_historical.Agency_Group == 'kcwa') &
                            (swp_historical.To_Reach == 'VCA-R14C') &
                            (swp_historical.Turnout == 'T255')] = 'ARV'
# R15A WRM
swp_historical.Agency_Group.loc[(swp_historical.Agency_Group == 'kcwa') &
                            (swp_historical.To_Reach == 'VCA-R15A')] = 'WRM'

# R16A Wheeler Ridge-Maricopa or Tehachapi Cummings
swp_historical.Agency_Group.loc[(swp_historical.Agency_Group == 'kcwa') &
                            (swp_historical.To_Reach == 'VCA-R16A')] = 'WRM_THC'
# R16A - divide by turnout (see SWP_turnouts.csv)
swp_historical.Agency_Group.loc[(swp_historical.Agency_Group == 'kcwa') &
                            (swp_historical.To_Reach == 'VCA-R16A') &
                            (swp_historical.Turnout == 'T265')] = 'THC'
swp_historical.Agency_Group.loc[(swp_historical.Agency_Group == 'kcwa') &
                            (swp_historical.To_Reach == 'VCA-R16A')] = 'WRM'
# R31A is start of Coastal Branch - berrenda mesa is only kcwa
swp_historical.Agency_Group.loc[(swp_historical.Agency_Group == 'kcwa') &
                            (swp_historical.To_Reach == 'VCB1-R31A')] = 'BDM'
# R17E is start of East Branch after Edmonston pumping plant - Tejon-Castac has delivery
swp_historical.Agency_Group.loc[(swp_historical.Agency_Group == 'kcwa') &
                            (swp_historical.To_Reach == 'VCA-R17E')] = 'TJC'
# Rest are unknown - don't see any kcwa members in pdfs. Reaches VCA-R3A, VCA-R4, VCB2-R33A.
swp_historical.Agency_Group.loc[(swp_historical.Agency_Group == 'kcwa')] = 'kcwa_unknown'



# now aggregate by water types into categories used by ORCA (See SWP_waterTypes_Lookup.csv)
swp_historical['WT_model'] = 'other'
swp_historical['banking_partner'] = 'none'

# TableA delivery
swp_historical.WT_model.loc[(swp_historical.Water_Type == 'TBLA01') |
                        (swp_historical.Water_Type == 'TBLA02') |
                        (swp_historical.Water_Type == 'TBLA07') |
                        (swp_historical.Water_Type == 'TBLA08') |
                        (swp_historical.Water_Type == 'TBLAADV') |
                        (swp_historical.WT_Group == 'TableA')
                        ] = 'tableA_delivery'
# TableA flood (Article 21)
swp_historical.WT_model.loc[swp_historical.WT_Group == 'Article21'] = 'tableA_flood'

# TableA turnback - also set sign -1 for sold water
swp_historical.WT_model.loc[(swp_historical.WT_Group == 'Bought') |
                        (swp_historical.WT_Group == 'Sold-CO') |
                        (swp_historical.WT_Group == 'Sold-TBLA') |
                        (swp_historical.WT_Group == 'TurnbackPools')
                        ] = 'tableA_turnback'

swp_historical.delivery_taf.loc[(swp_historical.WT_Group == 'Sold-CO') | (swp_historical.WT_Group == 'Sold-TBLA')] = \
  -swp_historical.delivery_taf.loc[(swp_historical.WT_Group == 'Sold-CO') | (swp_historical.WT_Group == 'Sold-TBLA')]

# TableA carryover
swp_historical.WT_model.loc[(swp_historical.WT_Group == 'Carryover') |
                        (swp_historical.WT_Group == 'SLRStorageCarryover')
                        ] = 'tableA_carryover'

# cvc delivery
swp_historical.WT_model.loc[(swp_historical.Water_Type == 'CVCSPLY') |
                        (swp_historical.Water_Type == 'JNTPNTCVC') |
                        (swp_historical.Water_Type == 'CVCENT') |
                        (swp_historical.Water_Type == 'CVC-OVER') |
                        (swp_historical.Water_Type == 'CVCPOD') |
                        (swp_historical.Water_Type == 'CVCTRN') |
                        (swp_historical.Water_Type == 'OPERXCH') |
                        ((swp_historical.Water_Type == 'CVPSPLY') &
                         ((swp_historical.Agency_Name == 'KERNCOUNTYWA') |
                          (swp_historical.Agency_Name == 'COUNTYOFFRESNO') |
                          (swp_historical.Agency_Name == 'COUNTYOFTULARE') |
                          (swp_historical.Agency_Name == 'TULARELAKEBASINWSD') |
                          (swp_historical.Agency_Name == 'HILLSVALLEYIRRIGATIONDISTRICT') |
                          (swp_historical.Agency_Name == 'TRI-VALLEYWATERDISTRICT') |
                          (swp_historical.Agency_Name == 'LOWERTULERIVER')))
                        ] = 'cvc_delivery'

# cvc flood
swp_historical.WT_model.loc[swp_historical.WT_Group == 'CVC215'] = 'cvc_flood'

# cvc undelivered
swp_historical.WT_model.loc[swp_historical.WT_Group == 'CVCREMAIN'] = 'cvc_undelivered'

# cvpdelta delivery
swp_historical.WT_model.loc[(swp_historical.Water_Type == 'CVPPOD') |
                        (swp_historical.Water_Type == 'DCVCCN') |
                        (swp_historical.Water_Type == 'JNTPNT') |
                        ((swp_historical.Water_Type == 'CVPSPLY') &
                         ((swp_historical.Agency_Name == 'SANTACLARAVALLEYWD') |
                          (swp_historical.Agency_Name == 'USBUREAUOFRECLAMATION')|
                          (swp_historical.Agency_Name == 'THEMETROPOLITANWATERDISTRICTOF')))
                        ] = 'cvpdelta_delivery'

# banking recovery. Also get banking partner from key.
swp_historical.WT_model.loc[(swp_historical.Water_Type == 'CXAERV') |
                        (swp_historical.Water_Type == 'CXKBRV') |
                        (swp_historical.Water_Type == 'CXSTRV') |
                        (swp_historical.Water_Type == 'CXKDRV') |
                        (swp_historical.WT_Group == 'WaterBankPumpin') |
                        (swp_historical.WT_Group == 'WaterBankRecovery')
                        ] = 'recover_banked'
swp_historical.banking_partner.loc[swp_historical.WT_Group == 'CXAERV'] = 'AEMWD'
swp_historical.banking_partner.loc[swp_historical.WT_Group == 'CXKBRV'] = 'KWB'
swp_historical.banking_partner.loc[swp_historical.WT_Group == 'CXSTRV'] = 'SMI'
swp_historical.banking_partner.loc[swp_historical.WT_Group == 'CXKDRV'] = 'KND'
swp_historical.banking_partner.loc[swp_historical.WT_Group == 'PUMPINAE'] = 'AEMWD'
swp_historical.banking_partner.loc[swp_historical.WT_Group == 'PUMPINKD'] = 'KND'
swp_historical.banking_partner.loc[swp_historical.WT_Group == 'PUMPINKWB'] = 'KWB'
swp_historical.banking_partner.loc[swp_historical.WT_Group == 'PUMPINST'] = 'SMI'
swp_historical.banking_partner.loc[swp_historical.WT_Group == '78RCV'] = 'SOC'
swp_historical.banking_partner.loc[swp_historical.WT_Group == '82RCV'] = 'SOC'
swp_historical.banking_partner.loc[swp_historical.WT_Group == 'KWBRCV'] = 'KWB'
swp_historical.banking_partner.loc[swp_historical.WT_Group == 'STEWA'] = 'SMI'
swp_historical.banking_partner.loc[swp_historical.WT_Group == 'STEWA-X'] = 'SMI'
swp_historical.banking_partner.loc[swp_historical.WT_Group == 'STRCV'] = 'SMI'
swp_historical.banking_partner.loc[swp_historical.WT_Group == 'STRCV-X'] = 'SMI'

# exchanged Table A surface water. Agency gets delivery of water from banking partner, gives parnter paper TBLA credit.
swp_historical.WT_model.loc[(swp_historical.Water_Type == 'TBLAXAE') |
                        (swp_historical.Water_Type == 'TBLAXKD') |
                        (swp_historical.Water_Type == 'TBLAXKWB') |
                        (swp_historical.Water_Type == 'TBLAXST') |
                        (swp_historical.Water_Type == 'TBLAXSPLY')
                        ] = 'exchange_SW'
swp_historical.banking_partner.loc[swp_historical.WT_Group == 'TBLAXAE'] = 'AEMWD'
swp_historical.banking_partner.loc[swp_historical.WT_Group == 'TBLAXKD'] = 'KND'
swp_historical.banking_partner.loc[swp_historical.WT_Group == 'TBLAXKWB'] = 'KWB'
swp_historical.banking_partner.loc[swp_historical.WT_Group == 'TBLAXST'] = 'SMI'

# create indicator variable to decide if should be included in total deliveries count
swp_historical['is_delivery'] = 0
swp_historical['is_delivery'].loc[swp_historical.WT_model == 'tableA_delivery'] = 1
swp_historical['is_delivery'].loc[swp_historical.WT_model == 'tableA_flood'] = 1
swp_historical['is_delivery'].loc[swp_historical.WT_model == 'cvc_delivery'] = 1
swp_historical['is_delivery'].loc[swp_historical.WT_model == 'cvc_flood'] = 1
swp_historical['is_delivery'].loc[swp_historical.WT_model == 'cvpdelta_delivery'] = 1
swp_historical['is_delivery'].loc[swp_historical.WT_model == 'recover_banked'] = 1

swp_historical['Project'] = 'SWP'


# ### plot historical deliveries
# dum =  (swp_historical.To_Reach == 'VCA-R12E') & (swp_historical.delivery_taf > 0)
# dum2 = dum & (swp_historical.WT_model == 'tableA_delivery')
# dum3 = dum & (swp_historical.WT_model == 'tableA_flood')
# dum4 = dum & (swp_historical.WT_model == 'tableA_turnback')
# dum5 = dum & (swp_historical.WT_model == 'tableA_carryover')
# dum6 = dum & (swp_historical.WT_model == 'recover_banked')
# dum7 = dum & (swp_historical.WT_model == 'exchange_SW')
# dum8 = dum & (swp_historical.WT_model == 'other')
#
# plt.plot_date(swp_historical['Date'].loc[dum2], swp_historical['delivery_taf'].loc[dum2], marker='o', alpha=0.3)
# plt.plot_date(swp_historical['Date'].loc[dum3], swp_historical['delivery_taf'].loc[dum3], marker='o', alpha=0.3)
# plt.plot_date(swp_historical['Date'].loc[dum4], swp_historical['delivery_taf'].loc[dum4], marker='o', alpha=0.3)
# plt.plot_date(swp_historical['Date'].loc[dum5], swp_historical['delivery_taf'].loc[dum5], marker='o', alpha=0.3)
# plt.plot_date(swp_historical['Date'].loc[dum6], swp_historical['delivery_taf'].loc[dum6], marker='o', alpha=0.3)
# plt.plot_date(swp_historical['Date'].loc[dum7], swp_historical['delivery_taf'].loc[dum7], marker='o', alpha=0.3)
# plt.plot_date(swp_historical['Date'].loc[dum8], swp_historical['delivery_taf'].loc[dum8], marker='o', alpha=0.3)
# plt.legend(['delivery','flood','turnback','carryover','recovery','exchange_SW', 'other'])

### save
swp_historical.to_csv('cord/data/input/SWP_delivery_cleaned.csv',index=False)




###############################################################################
### Central Valley Project ####################################################
###############################################################################

### Read/clean/organize historical CVP deliveries
# Read data, 1996-2016. **Note: 2011-2016 convert pdfs to csv online, then clean csv in excel to get into readable form.
#  1996-2010 download text tables & clean/convert to csv in excel.
years = np.arange(1996,2017)
tables = [22,23,26]
deliveries = pd.DataFrame({'WaterUser':[],'Canal':[],'Year':[],'Jan':[],'Feb':[],'Mar':[],'Apr':[],'May':[],'Jun':[],
                           'Jul':[],'Aug':[],'Sep':[],'Oct':[],'Nov':[],'Dec':[], 'Notes':[]})

for y in years:
  for t in tables:
    file = 'cord/data/input/cvp_historical/table_' + str(t) + '_' + str(y) + '.csv'
    try:
      deliveries_temp = pd.read_csv(file, skiprows=6)
    except:
      file = 'cord/data/input/cvp_historical/table_' + str(t) + '_' + str(y) + '.xlsx'
      deliveries_temp = pd.read_excel(file, skiprows=6)

    # clean
    try:
      deliveries_temp['WaterUser'] = deliveries_temp['Water User']
      del deliveries_temp['Water User']
    except:
      deliveries_temp['WaterUser'] = deliveries_temp['Water Users']
      del deliveries_temp['Water Users']
    del deliveries_temp['Total']
    deliveries_temp = deliveries_temp.loc[deliveries_temp.WaterUser != 'Total']
    deliveries_temp.Dec = deliveries_temp.Dec.replace(np.nan, '')
    try:
      deliveries_temp = deliveries_temp.loc[deliveries_temp.Dec != '',:]
    except:
      deliveries_temp = deliveries_temp
    deliveries_temp = deliveries_temp.reset_index(drop=True)
    deliveries_temp.Canal = deliveries_temp.Canal.apply(lambda x: x.replace(' ',''))
    deliveries_temp.WaterUser = deliveries_temp.WaterUser.apply(lambda x: x.replace(' ',''))
    deliveries_temp['Year'] = y
    for i in ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']:
      try:
        deliveries_temp[i] = pd.to_numeric(deliveries_temp[i].apply(lambda x: x.replace(',', '')).apply(lambda x: x.replace('NR', '0')).apply(lambda x: x.replace('-1', '0')).apply(lambda x: x.replace(' ', '0')))
      except:
        deliveries_temp[i] = deliveries_temp[i]

    # append to rest of dataset
    deliveries = deliveries.append(deliveries_temp)


# create time series
cvp_historical = pd.DataFrame(index=range(deliveries.shape[0]*12))
cvp_historical['Year'] = 0
cvp_historical['Month'] = 0
cvp_historical['Day'] = 1
cvp_historical['Wateryear'] = 0
cvp_historical['WaterUser'] = ' '
cvp_historical['Canal'] = ' '
cvp_historical['delivery_taf'] = 0.0

dum = np.repeat(np.arange(deliveries.shape[0]), 12)
for n in ['Year','WaterUser','Canal']:
  cvp_historical[n] = deliveries.iloc[dum][n].values
cvp_historical['Month'] = np.tile(np.arange(1,13), deliveries.shape[0])
cvp_historical['Wateryear'] = cvp_historical['Year']
cvp_historical['Wateryear'].loc[cvp_historical['Month'] > 9] = cvp_historical['Wateryear'].loc[cvp_historical['Month'] > 9] + 1

cvp_historical['delivery_taf'].iloc[0:cvp_historical.shape[0]:12] = deliveries['Jan'].values / 1000
cvp_historical['delivery_taf'].iloc[1:cvp_historical.shape[0]:12] = deliveries['Feb'].values / 1000
cvp_historical['delivery_taf'].iloc[2:cvp_historical.shape[0]:12] = deliveries['Mar'].values / 1000
cvp_historical['delivery_taf'].iloc[3:cvp_historical.shape[0]:12] = deliveries['Apr'].values / 1000
cvp_historical['delivery_taf'].iloc[4:cvp_historical.shape[0]:12] = deliveries['May'].values / 1000
cvp_historical['delivery_taf'].iloc[5:cvp_historical.shape[0]:12] = deliveries['Jun'].values / 1000
cvp_historical['delivery_taf'].iloc[6:cvp_historical.shape[0]:12] = deliveries['Jul'].values / 1000
cvp_historical['delivery_taf'].iloc[7:cvp_historical.shape[0]:12] = deliveries['Aug'].values / 1000
cvp_historical['delivery_taf'].iloc[8:cvp_historical.shape[0]:12] = deliveries['Sep'].values / 1000
cvp_historical['delivery_taf'].iloc[9:cvp_historical.shape[0]:12] = deliveries['Oct'].values / 1000
cvp_historical['delivery_taf'].iloc[10:cvp_historical.shape[0]:12] = deliveries['Nov'].values / 1000
cvp_historical['delivery_taf'].iloc[11:cvp_historical.shape[0]:12] = deliveries['Dec'].values / 1000
cvp_historical['delivery_taf'].loc[np.isnan(cvp_historical['delivery_taf'])] = 0
cvp_historical['Canal'].loc[cvp_historical['Canal'] == 'CROSSVALLEYCANAL(SeeNote1below)'] = 'CROSSVALLEYCANAL'
cvp_historical['Canal'].loc[cvp_historical['Canal'] == 'CROSSVALLEYCANAL(SeeNote1below'] = 'CROSSVALLEYCANAL'
cvp_historical['Date'] = pd.to_datetime(cvp_historical[['Year','Month','Day']])
cvp_historical['Project'] = 'CVP'
del deliveries, deliveries_temp, cvp_historical['Day']

# get pump-in rows
cvp_historical['pumpin'] = 'False'
ind = [i for i, v in enumerate(cvp_historical['WaterUser']) if '-In' in v]
cvp_historical.loc[ind,'pumpin'] = True

# plt.plot_date(cvp_historical['Date'], cvp_historical['delivery_taf'], marker='o', alpha=0.3)

### get standardized district names consistent with modeled results
cvp_historical.WaterUser = cvp_historical.WaterUser.apply(lambda x: np.char.lower(x))
cvp_historical['WaterUserCode'] = 'other'
# friant-kern contracts
cvp_historical.WaterUserCode.loc[cvp_historical.Canal=='FRIANT-KERNCANAL'] = 'OFK_non_contract'     # blanket code for 'other friant'
cvp_historical.WaterUserCode.loc[[i for i, v in enumerate(cvp_historical['WaterUser']) if 'arvin' in v]] = 'ARV'
cvp_historical.WaterUserCode.loc[[i for i, v in enumerate(cvp_historical['WaterUser']) if 'delano' in v]] = 'DLE'
cvp_historical.WaterUserCode.loc[[i for i, v in enumerate(cvp_historical['WaterUser']) if 'exeter' in v]] = 'EXE'
cvp_historical.WaterUserCode.loc[[i for i, v in enumerate(cvp_historical['WaterUser']) if 'kern-tulare' in v]] = 'KRT'
cvp_historical.WaterUserCode.loc[[i for i, v in enumerate(cvp_historical['WaterUser']) if 'raggulch' in v]] = 'KRT'
cvp_historical.WaterUserCode.loc[[i for i, v in enumerate(cvp_historical['WaterUser']) if 'lindmore' in v]] = 'LND'
cvp_historical.WaterUserCode.loc[[i for i, v in enumerate(cvp_historical['WaterUser']) if 'lindsay-strath' in v]] = 'LDS'
cvp_historical.WaterUserCode.loc[[i for i, v in enumerate(cvp_historical['WaterUser']) if 'wutchumna' in v]] = 'LDS'
cvp_historical.WaterUserCode.loc[[i for i, v in enumerate(cvp_historical['WaterUser']) if 'lowertule' in v]] = 'LWT'
cvp_historical.WaterUserCode.loc[[i for i, v in enumerate(cvp_historical['WaterUser']) if 'porterville' in v]] = 'PRT'
cvp_historical.WaterUserCode.loc[[i for i, v in enumerate(cvp_historical['WaterUser']) if 'saucelito' in v]] = 'SAU'
cvp_historical.WaterUserCode.loc[[i for i, v in enumerate(cvp_historical['WaterUser']) if 'shafter' in v]] = 'SFW'
cvp_historical.WaterUserCode.loc[[i for i, v in enumerate(cvp_historical['WaterUser']) if 'sanjoaquin' in v]] = 'SSJ'
cvp_historical.WaterUserCode.loc[[i for i, v in enumerate(cvp_historical['WaterUser']) if 'teapot' in v]] = 'TPD'
cvp_historical.WaterUserCode.loc[[i for i, v in enumerate(cvp_historical['WaterUser']) if 'terra' in v]] = 'TBA'
cvp_historical.WaterUserCode.loc[[i for i, v in enumerate(cvp_historical['WaterUser']) if 'tulareid' in v]] = 'TUL'
cvp_historical.WaterUserCode.loc[[i for i, v in enumerate(cvp_historical['WaterUser']) if 'cityoffresno' in v]] = 'COF'
cvp_historical.WaterUserCode.loc[[i for i, v in enumerate(cvp_historical['WaterUser']) if 'fresno,city' in v]] = 'COF'
cvp_historical.WaterUserCode.loc[[i for i, v in enumerate(cvp_historical['WaterUser']) if 'fresnoi' in v]] = 'FRS'
# blanket code for other friant contractors not in our model
cvp_historical.WaterUserCode.loc[[i for i, v in enumerate(cvp_historical['WaterUser']) if 'fresno,co' in v]] = 'OFK'
cvp_historical.WaterUserCode.loc[[i for i, v in enumerate(cvp_historical['WaterUser']) if 'countyoffresno' in v]] = 'OFK'
cvp_historical.WaterUserCode.loc[[i for i, v in enumerate(cvp_historical['WaterUser']) if 'garfield' in v]] = 'OFK'
cvp_historical.WaterUserCode.loc[[i for i, v in enumerate(cvp_historical['WaterUser']) if 'hillsvalley' in v]] = 'OFK'
cvp_historical.WaterUserCode.loc[[i for i, v in enumerate(cvp_historical['WaterUser']) if 'international' in v]] = 'OFK'
cvp_historical.WaterUserCode.loc[[i for i, v in enumerate(cvp_historical['WaterUser']) if 'ivanhoe' in v]] = 'OFK'
cvp_historical.WaterUserCode.loc[[i for i, v in enumerate(cvp_historical['WaterUser']) if 'kawaeahdelta' in v]] = 'OFK'
cvp_historical.WaterUserCode.loc[[i for i, v in enumerate(cvp_historical['WaterUser']) if 'lewiscreek' in v]] = 'OFK'
cvp_historical.WaterUserCode.loc[[i for i, v in enumerate(cvp_historical['WaterUser']) if 'lindsay,city' in v]] = 'OFK'
cvp_historical.WaterUserCode.loc[[i for i, v in enumerate(cvp_historical['WaterUser']) if 'cityoflindsay' in v]] = 'OFK'
cvp_historical.WaterUserCode.loc[[i for i, v in enumerate(cvp_historical['WaterUser']) if 'orangecove,city' in v]] = 'OFK'
cvp_historical.WaterUserCode.loc[[i for i, v in enumerate(cvp_historical['WaterUser']) if 'cityoforangecove' in v]] = 'OFK'
cvp_historical.WaterUserCode.loc[[i for i, v in enumerate(cvp_historical['WaterUser']) if 'orangecovei' in v]] = 'OFK'
cvp_historical.WaterUserCode.loc[[i for i, v in enumerate(cvp_historical['WaterUser']) if 'stonecorral' in v]] = 'OFK'
cvp_historical.WaterUserCode.loc[[i for i, v in enumerate(cvp_historical['WaterUser']) if 'tri-valley' in v]] = 'OFK'
# madera contracts
cvp_historical.WaterUserCode.loc[[i for i, v in enumerate(cvp_historical['WaterUser']) if 'chowchilla' in v]] = 'CWC'
cvp_historical.WaterUserCode.loc[[i for i, v in enumerate(cvp_historical['WaterUser']) if 'maderai' in v]] = 'MAD'
# other districts we model that don't have FKC contracts but seem to get deliveries on friant
cvp_historical.WaterUserCode.loc[[i for i, v in enumerate(cvp_historical['WaterUser']) if 'north-kern' in v]] = 'NKN'
cvp_historical.WaterUserCode.loc[[i for i, v in enumerate(cvp_historical['WaterUser']) if 'kerncountyw' in v]] = 'KCWA'
cvp_historical.WaterUserCode.loc[[i for i, v in enumerate(cvp_historical['WaterUser']) if 'rosedale' in v]] = 'RRB'
cvp_historical.WaterUserCode.loc[[i for i, v in enumerate(cvp_historical['WaterUser']) if 'semitropic' in v]] = 'SMI'
cvp_historical.WaterUserCode.loc[[i for i, v in enumerate(cvp_historical['WaterUser']) if 'kern-delta' in v]] = 'KND'
cvp_historical.WaterUserCode.loc[[i for i, v in enumerate(cvp_historical['WaterUser']) if 'bakersfield' in v]] = 'COB'
cvp_historical.WaterUserCode.loc[[i for i, v in enumerate(cvp_historical['WaterUser']) if 'bakersfiled' in v]] = 'COB'
cvp_historical.WaterUserCode.loc[[i for i, v in enumerate(cvp_historical['WaterUser']) if 'tularelake' in v]] = 'TLB'

### also set contract (as well as possible- just based on whether they are contractor)
cvp_historical['contractor'] = 'other'
cvp_historical.contractor.loc[[i for i,v in enumerate(cvp_historical.WaterUserCode) if v in
                               ['ARV','DLE','EXE','KRT','LND','LDS','LWT','PRT','SAU','SFW','SSJ','TPD','TBA','TUL',
                                'COF','CWC','MAD','OFK']]] = 'friant'



### save
cvp_historical.to_csv('cord/data/input/CVP_delivery_cleaned.csv',index=False)




