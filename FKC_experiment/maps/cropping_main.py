from osgeo import gdal
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from shapely.geometry import Point, Polygon, LineString
import geopandas as gpd
import fiona
from matplotlib.colors import ListedColormap
import matplotlib.pylab as pl
import rasterio
import rasterio.plot
import pyproj
import os 
from adding_comtrs_functions import add_comtrs_pre_1990
from adding_comtrs_functions import add_comtrs_1990_2004
from adding_comtrs_functions import add_comtrs_2005_2016
from fix_pur_data_step1 import replace_bad_characters
from compile_normalize_data_by_comtrs import compile_data_by_comtrs
from compile_normalize_data_by_comtrs import normalize_data
from crop import Crop

def find_crop_keys():
  b = 1
  if b == 1:   
    crop_keys = {}
    crop_keys['990'] = 'field_misc'
    crop_keys['3101'] = 'alfalfa'
    crop_keys['3110'] = 'alfalfa'
    crop_keys['4101'] = 'almond'
    crop_keys['5401'] = 'vegetable_small'
    crop_keys['2201'] = 'apple'
    crop_keys['2301'] = 'deciduous_misc'
    crop_keys['1231'] = 'vegetable_small'
    crop_keys['1232'] = 'vegetable_small'
    crop_keys['2401'] = 'avocado'
    crop_keys['2411'] = 'subtropical_misc'
    crop_keys['3301'] = 'grain'
    crop_keys['1331'] = 'vegetable_small'
    crop_keys['1330'] = 'vegetable_small'
    crop_keys['1335'] = 'vegetable_small'
    crop_keys['1336'] = 'vegetable_small'
    crop_keys['1337'] = 'vegetable_small'
    crop_keys['1111'] = 'vegetable_small'
    crop_keys['2502'] = 'strawberry'
    crop_keys['3102'] = 'safflower'
    crop_keys['2504'] = 'strawberry'
    crop_keys['2505'] = 'strawberry'
    crop_keys['2506'] = 'strawberry'
    crop_keys['1221'] = 'vegetable_small'
    crop_keys['1222'] = 'vegetable_small'
    crop_keys['8000'] = 'idle'
    crop_keys['7600'] = 'onion'
    crop_keys['1223'] = 'field_misc'
    crop_keys['1253'] = 'field_misc'
    crop_keys['1254'] = 'deciduous_misc'
    crop_keys['1218'] = 'vegetable_small'
    crop_keys['1112'] = 'vegetable_small'
    crop_keys['4201'] = 'subtropical_misc'
    crop_keys['6101'] = 'pasture'
    crop_keys['1224'] = 'vegetable_small'
    crop_keys['1235'] = 'field_misc'
    crop_keys['1233'] = 'vegetable_small'
    crop_keys['1217'] = 'vegetable_small'
    crop_keys['1346'] = 'deciduous_misc'
    crop_keys['1255'] = 'subtropical_misc'
    crop_keys['2302'] = 'deciduous_misc'
    crop_keys['4102'] = 'deciduous_misc'
    crop_keys['6201'] = 'pasture'
    crop_keys['5205'] = 'field_misc'
    crop_keys['1251'] = 'vegetable_small'
    crop_keys['1252'] = 'field_misc'
    crop_keys['1256'] = 'field_misc'
    crop_keys['2100'] = 'citrus'
    crop_keys['2105'] = 'citrus'
    crop_keys['6'] = 'idle'
    crop_keys['991'] = 'idle'
    crop_keys['3103'] = 'field_misc'
    crop_keys['2412'] = 'subtropical_misc'
    crop_keys['1257'] = 'field_misc'
    crop_keys['1220'] = 'vegetable_small'
    crop_keys['1236'] = 'vegetable_small'
    crop_keys['1225'] = 'vegetable_small'
    crop_keys['7301'] = 'nursery'
    crop_keys['3302'] = 'corn'
    crop_keys['3201'] = 'cotton'
    crop_keys['7'] = 'idle'
    crop_keys['975'] = 'idle'
    crop_keys['945'] = 'idle'
    crop_keys['4204'] = 'cotton'
    crop_keys['2507'] = 'strawberry'
    crop_keys['1313'] = 'cucumber'
    crop_keys['1127'] = 'vegetable_small'
    crop_keys['1237'] = 'field_misc'
    crop_keys['2402'] = 'deciduous_misc'
    crop_keys['7200'] = 'deciduous_misc'
    crop_keys['5402'] = 'field_misc'
    crop_keys['6300'] = 'pasture'
    crop_keys['9301'] = 'deciduous_misc'
    crop_keys['6202'] = 'pond'        
    crop_keys['1341'] = 'vegetable_small'
    crop_keys['6204'] = 'pasture'
    crop_keys['1219'] = 'vegetable_small'
    crop_keys['1238'] = 'vegetable_small'
    crop_keys['7300'] = 'nursery'
    crop_keys['7302'] = 'nursery'
    crop_keys['9101'] = 'idle'
    crop_keys['1'] = 'idle'
    crop_keys['970'] = 'idle'
    crop_keys['3200'] = 'cotton'
    crop_keys['2415'] = 'subtropical_misc'
    crop_keys['2403'] = 'deciduous_misc'
    crop_keys['3204'] = 'field_misc'
    crop_keys['8'] = 'idle'
    crop_keys['955'] = 'idle'
    crop_keys['7500'] = 'field_misc'
    crop_keys['8100'] = 'idle'
    crop_keys['8102'] = 'idle'
    crop_keys['3100'] = 'field_misc'
    crop_keys['7700'] = 'idle'
    crop_keys['2000'] = 'strawberry'
    crop_keys['1258'] = 'field_misc'
    crop_keys['1239'] = 'vegetable_small'
    crop_keys['1240'] = 'vegetable_small'
    crop_keys['1121'] = 'field_misc'
    crop_keys['5102'] = 'field_misc'
    crop_keys['2508'] = 'strawberry'
    crop_keys['3300'] = 'grain'
    crop_keys['8001'] = 'idle'
    crop_keys['2503'] = 'grape'
    crop_keys['2101'] = 'citrus'
    crop_keys['3000'] = 'grass'
    crop_keys['8002'] = 'idle'
    crop_keys['9208'] = 'idle'
    crop_keys['9207'] = 'idle'
    crop_keys['3202'] = 'field_misc'
    crop_keys['5501'] = 'idle'
    crop_keys['5301'] = 'grain'
    crop_keys['6102'] = 'pasture'
    crop_keys['5101'] = 'field_misc'
    crop_keys['9209'] = 'idle'
    crop_keys['9210'] = 'idle'
    crop_keys['9201'] = 'idle'
    crop_keys['9'] = 'idle'
    crop_keys['960'] = 'idle'
    crop_keys['1128'] = 'field_misc'
    crop_keys['1226'] = 'field_misc'
    crop_keys['2404'] = 'deciduous_misc'
    crop_keys['1228'] = 'field_misc'
    crop_keys['2108'] = 'citrus'
    crop_keys['1122'] = 'field_misc'
    crop_keys['3109'] = 'field_misc'
    crop_keys['2102'] = 'citrus'
    crop_keys['1212'] = 'field_misc'
    crop_keys['1213'] = 'field_misc'
    crop_keys['1241'] = 'field_misc'
    crop_keys['2106'] = 'citrus'
    crop_keys['6100'] = 'pasture'
    crop_keys['8003'] = 'pasture'
    crop_keys['6109'] = 'pasture'
    crop_keys['6000'] = 'pasture'
    crop_keys['9205'] = 'idle'
    crop_keys['9206'] = 'idle'
    crop_keys['5103'] = 'field_misc'
    crop_keys['2107'] = 'citrus'
    crop_keys['2413'] = 'subtropical_misc'
    crop_keys['1311'] = 'melon'
    crop_keys['1310'] = 'melon'
    crop_keys['5201'] = 'field_misc'
    crop_keys['9999'] = 'idle'
    crop_keys['9000'] = 'idle'
    crop_keys['9300'] = 'idle'
    crop_keys['1259'] = 'field_misc'
    crop_keys['9302'] = 'field_misc'
    crop_keys['1227'] = 'field_misc'
    crop_keys['1242'] = 'field_misc'
    crop_keys['2303'] = 'deciduous_misc'
    crop_keys['9200'] = 'idle'
    crop_keys['4100'] = 'deciduous_misc'
    crop_keys['4000'] = 'deciduous_misc'
    crop_keys['4109'] = 'deciduous_misc'
    crop_keys['3303'] = 'grain'
    crop_keys['4200'] = 'field_misc'
    crop_keys['1332'] = 'field_misc'
    crop_keys['2405'] = 'subtropical_misc'
    crop_keys['1123'] = 'onion'
    crop_keys['1125'] = 'onion'
    crop_keys['1126'] = 'onion'
    crop_keys['9100'] = 'idle'
    crop_keys['2103'] = 'citrus'
    crop_keys['9102'] = 'idle'
    crop_keys['1229'] = 'vegetable_small'
    crop_keys['7000'] = 'idle'
    crop_keys['400'] = 'idle'
    crop_keys['2414'] = 'subtropical_misc'
    crop_keys['1214'] = 'field_misc'
    crop_keys['5104'] = 'field_misc'
    crop_keys['1113'] = 'field_misc'
    crop_keys['3104'] = 'pasture'
    crop_keys['2304'] = 'deciduous_misc'
    crop_keys['2202'] = 'deciduous_misc'
    crop_keys['1333'] = 'field_misc'
    crop_keys['4103'] = 'deciduous_misc'
    crop_keys['1342'] = 'pepper'
    crop_keys['1343'] = 'pepper'
    crop_keys['2408'] = 'deciduous_misc'
    crop_keys['5302'] = 'pepper'
    crop_keys['2409'] = 'subtropical_misc'
    crop_keys['4104'] = 'pistachio'
    crop_keys['2305'] = 'deciduous_misc'
    crop_keys['2200'] = 'deciduous_misc'
    crop_keys['2406'] = 'deciduous_misc'
    crop_keys['1124'] = 'potatoe'
    crop_keys['6200'] = 'idle'
    crop_keys['8004'] = 'idle'
    crop_keys['2306'] = 'deciduous_misc'
    crop_keys['1322'] = 'squash'
    crop_keys['2203'] = 'deciduous_misc'
    crop_keys['1114'] = 'field_misc'
    crop_keys['3203'] = 'field_misc'
    crop_keys['1243'] = 'field_misc'
    crop_keys['10'] = 'idle'
    crop_keys['965'] = 'idle'
    crop_keys['980'] = 'idle'
    crop_keys['9202'] = 'idle'
    crop_keys['9203'] = 'idle'
    crop_keys['8101'] = 'idle'
    crop_keys['1234'] = 'field_misc'
    crop_keys['3304'] = 'rice'
    crop_keys['7501'] = 'field_misc'
    crop_keys['1119'] = 'vegetable_small'
    crop_keys['3305'] = 'grain'
    crop_keys['3105'] = 'grain'
    crop_keys['4202'] = 'safflower'
    crop_keys['5202'] = 'field_misc'
    crop_keys['1244'] = 'vegetable_small'
    crop_keys['1115'] = 'field_misc'
    crop_keys['1245'] = 'vegetable_small'
    crop_keys['11'] = 'idle'
    crop_keys['993'] = 'idle'
    crop_keys['5403'] = 'field_misc'
    crop_keys['6103'] = 'pasture'
    crop_keys['1260'] = 'field_misc'
    crop_keys['7400'] = 'idle'
    crop_keys['2500'] = 'strawberry'
    crop_keys['9103'] = 'idle'
    crop_keys['3306'] = 'field_misc'
    crop_keys['1334'] = 'field_misc'
    crop_keys['5000'] = 'field_misc'
    crop_keys['5300'] = 'field_misc'
    crop_keys['5200'] = 'field_misc'
    crop_keys['5100'] = 'field_misc'
    crop_keys['5400'] = 'field_misc'
    crop_keys['1215'] = 'field_misc'
    crop_keys['1321'] = 'squash'
    crop_keys['1320'] = 'squash'
    crop_keys['1323'] = 'squash'
    crop_keys['1324'] = 'squash'
    crop_keys['1246'] = 'field_misc'
    crop_keys['2'] = 'idle'
    crop_keys['940'] = 'idle'
    crop_keys['2300'] = 'deciduous_misc'
    crop_keys['8005'] = 'idle'
    crop_keys['2501'] = 'strawberry'
    crop_keys['773'] = 'idle'
    crop_keys['9204'] = 'idle'
    crop_keys['2407'] = 'subtropical_misc'
    crop_keys['3106'] = 'grass'
    crop_keys['1116'] = 'vegetable_small'
    crop_keys['2410'] = 'field_misc'
    crop_keys['4203'] = 'field_misc'
    crop_keys['5203'] = 'field_misc'
    crop_keys['1117'] = 'potatoe'
    crop_keys['9211'] = 'idle'
    crop_keys['6104'] = 'idle'
    crop_keys['1216'] = 'vegetable_small'
    crop_keys['2104'] = 'subtropical_misc'
    crop_keys['1247'] = 'field_misc'
    crop_keys['5204'] = 'field_misc'
    crop_keys['9303'] = 'field_misc'
    crop_keys['1345'] = 'tomato'
    crop_keys['1344'] = 'tomato'
    crop_keys['3309'] = 'grain'
    crop_keys['2400'] = 'subtropical_misc'
    crop_keys['7100'] = 'grass'
    crop_keys['6203'] = 'idle'
    crop_keys['1118'] = 'field_misc'
    crop_keys['1248'] = 'field_misc'
    crop_keys['3'] = 'idle'
    crop_keys['985'] = 'idle'
    crop_keys['4'] = 'idle'
    crop_keys['881'] = 'idle'
    crop_keys['1000'] = 'vegetable_small'
    crop_keys['1300'] = 'vegetable_small'
    crop_keys['1340'] = 'vegetable_small'
    crop_keys['1210'] = 'vegetable_small'
    crop_keys['1200'] = 'vegetable_small'
    crop_keys['1110'] = 'vegetable_small'
    crop_keys['1100'] = 'vegetable_small'
    crop_keys['4500'] = 'vegetable_small'
    crop_keys['1230'] = 'vegetable_small'
    crop_keys['1120'] = 'vegetable_small'
    crop_keys['1261'] = 'vegetable_small'
    crop_keys['3107'] = 'field_misc'
    crop_keys['4105'] = 'walnut'
    crop_keys['9104'] = 'idle'
    crop_keys['5'] = 'idle'
    crop_keys['950'] = 'idle'
    crop_keys['1249'] = 'field_misc'
    crop_keys['1312'] = 'melon'
    crop_keys['3307'] = 'grain'
    crop_keys['3308'] = 'rice'
    crop_keys['1250'] = 'squash'
    crop_keys['1325'] = 'field_misc'
    crop_keys['999'] = 'idle'
    crop_keys['999999'] = 'idle'
    crop_keys['99999'] = 'idle'
    ####POST 1990
    crop_keys['-1'] = 'idle'
    crop_keys['10'] = 'idle'
    crop_keys['30'] = 'idle'
    crop_keys['40'] = 'idle'
    crop_keys['50'] = 'idle'
    crop_keys['60'] = 'idle'
    crop_keys['80'] = 'idle'
    crop_keys['90'] = 'idle'
    crop_keys['91'] = 'idle'
    crop_keys['99'] = 'idle'
    crop_keys['100'] = 'idle'
    crop_keys['151'] = 'idle'
    crop_keys['152'] = 'idle'
    crop_keys['153'] = 'idle'
    crop_keys['154'] = 'idle'
    crop_keys['155'] = 'idle'
    crop_keys['156'] = 'idle'
    crop_keys['1000'] = 'strawberry'
    crop_keys['1002'] = 'strawberry'
    crop_keys['1003'] = 'strawberry'
    crop_keys['1004'] = 'strawberry'
    crop_keys['1005'] = 'strawberry'
    crop_keys['1006'] = 'strawberry'
    crop_keys['1009'] = 'strawberry'
    crop_keys['1010'] = 'strawberry'
    crop_keys['1013'] = 'strawberry'
    crop_keys['1016'] = 'strawberry'
    crop_keys['1023'] = 'strawberry'
    crop_keys['2000'] = 'citrus'
    crop_keys['2002'] = 'citrus'
    crop_keys['2003'] = 'citrus'
    crop_keys['2004'] = 'citrus'
    crop_keys['2005'] = 'citrus'
    crop_keys['2006'] = 'citrus'
    crop_keys['2007'] = 'citrus'
    crop_keys['2008'] = 'citrus'
    crop_keys['3000'] = 'deciduous_misc'
    crop_keys['3001'] = 'almond'
    crop_keys['3003'] = 'deciduous_misc'
    crop_keys['3004'] = 'deciduous_misc'
    crop_keys['3008'] = 'deciduous_misc'
    crop_keys['3009'] = 'walnut'
    crop_keys['3011'] = 'pistachio'
    crop_keys['4000'] = 'deciduous_misc'
    crop_keys['4001'] = 'apple'
    crop_keys['4003'] = 'deciduous_misc'
    crop_keys['4004'] = 'deciduous_misc'
    crop_keys['5000'] = 'deciduous_misc'
    crop_keys['5001'] = 'apple'
    crop_keys['5002'] = 'deciduous_misc'
    crop_keys['5003'] = 'deciduous_misc'
    crop_keys['5004'] = 'peach'
    crop_keys['5005'] = 'deciduous_misc'
    crop_keys['5006'] = 'deciduous_misc'
    crop_keys['6000'] = 'subtropical_misc'
    crop_keys['6002'] = 'subtropical_misc'
    crop_keys['6004'] = 'subtropical_misc'
    crop_keys['6005'] = 'subtropical_misc'
    crop_keys['6007'] = 'subtropical_misc'
    crop_keys['6010'] = 'subtropical_misc'
    crop_keys['6012'] = 'subtropical_misc'
    crop_keys['6013'] = 'subtropical_misc'
    crop_keys['6015'] = 'subtropical_misc'
    crop_keys['6018'] = 'subtropical_misc'
    crop_keys['6028'] = 'subtropical_misc'
    crop_keys['6030'] = 'subtropical_misc'
    crop_keys['7000'] = 'field_misc'
    crop_keys['8000'] = 'field_misc'
    crop_keys['8004'] = 'field_misc'
    crop_keys['8006'] = 'field_misc'
    crop_keys['8015'] = 'field_misc'
    crop_keys['8019'] = 'field_misc'
    crop_keys['8020'] = 'field_misc'
    crop_keys['8035'] = 'field_misc'
    crop_keys['8041'] = 'field_misc'
    crop_keys['8050'] = 'pepper'
    crop_keys['10000'] = 'squash'
    crop_keys['10002'] = 'melon'
    crop_keys['10008'] = 'melon'
    crop_keys['10010'] = 'cucumber'
    crop_keys['10011'] = 'squash'
    crop_keys['10012'] = 'squash'
    crop_keys['10013'] = 'squash'
    crop_keys['10014'] = 'squash'
    crop_keys['10015'] = 'squash'
    crop_keys['10018'] = 'vegetable_small'
    crop_keys['10030'] = 'squash'
    crop_keys['11000'] = 'vegetable_small'
    crop_keys['11001'] = 'vegetable_small'
    crop_keys['11003'] = 'pepper'
    crop_keys['11004'] = 'tomato'
    crop_keys['11005'] = 'tomato'
    crop_keys['11008'] = 'tomato'
    crop_keys['13000'] = 'vegetable_small'
    crop_keys['13004'] = 'vegetable_small'
    crop_keys['13005'] = 'vegetable_small'
    crop_keys['13006'] = 'vegetable_small'
    crop_keys['13007'] = 'vegetable_small'
    crop_keys['13008'] = 'vegetable_small'
    crop_keys['13009'] = 'vegetable_small'
    crop_keys['13010'] = 'vegetable_small'
    crop_keys['13011'] = 'vegetable_small'
    crop_keys['13012'] = 'vegetable_small'
    crop_keys['13014'] = 'vegetable_small'
    crop_keys['13015'] = 'vegetable_small'
    crop_keys['13018'] = 'vegetable_small'
    crop_keys['13021'] = 'vegetable_small'
    crop_keys['13022'] = 'vegetable_small'
    crop_keys['13023'] = 'vegetable_small'
    crop_keys['13024'] = 'vegetable_small'
    crop_keys['13025'] = 'vegetable_small'
    crop_keys['13027'] = 'vegetable_small'
    crop_keys['13031'] = 'vegetable_small'
    crop_keys['13032'] = 'vegetable_small'
    crop_keys['13043'] = 'vegetable_small'
    crop_keys['13045'] = 'vegetable_small'
    crop_keys['13046'] = 'vegetable_small'
    crop_keys['13048'] = 'vegetable_small'
    crop_keys['13051'] = 'vegetable_small'
    crop_keys['13052'] = 'vegetable_small'
    crop_keys['13055'] = 'vegetable_small'
    crop_keys['13056'] = 'vegetable_small'
    crop_keys['13501'] = 'vegetable_small'
    crop_keys['13502'] = 'vegetable_small'
    crop_keys['13504'] = 'vegetable_small'
    crop_keys['13505'] = 'vegetable_small'
    crop_keys['13509'] = 'vegetable_small'
    crop_keys['13903'] = 'vegetable_small'
    crop_keys['13999'] = 'vegetable_small'
    crop_keys['14004'] = 'vegetable_small'
    crop_keys['14005'] = 'field_misc'
    crop_keys['14007'] = 'field_misc'
    crop_keys['14010'] = 'field_misc'
    crop_keys['14011'] = 'onion'
    crop_keys['14012'] = 'field_misc'
    crop_keys['14013'] = 'potatoe'
    crop_keys['14014'] = 'field_misc'
    crop_keys['14015'] = 'field_misc'
    crop_keys['14017'] = 'onion'
    crop_keys['14018'] = 'potatoe'
    crop_keys['14021'] = 'potatoe'
    crop_keys['14023'] = 'potatoe'
    crop_keys['14024'] = 'potatoe'
    crop_keys['14025'] = 'potatoe'
    crop_keys['15001'] = 'field_misc'
    crop_keys['15003'] = 'field_misc'
    crop_keys['15010'] = 'grain'
    crop_keys['15013'] = 'field_misc'
    crop_keys['15015'] = 'field_misc'
    crop_keys['15021'] = 'field_misc'
    crop_keys['15029'] = 'field_misc'
    crop_keys['15032'] = 'field_misc'
    crop_keys['16002'] = 'vegetable_small'
    crop_keys['16003'] = 'field_misc'
    crop_keys['16004'] = 'onion'
    crop_keys['21000'] = 'field_misc'
    crop_keys['21003'] = 'field_misc'
    crop_keys['21005'] = 'field_misc'
    crop_keys['22000'] = 'field_misc'
    crop_keys['22004'] = 'field_misc'
    crop_keys['22005'] = 'corn'
    crop_keys['22006'] = 'grain'
    crop_keys['22007'] = 'grain'
    crop_keys['22008'] = 'grain'
    crop_keys['22011'] = 'grain'
    crop_keys['22017'] = 'grain'
    crop_keys['22035'] = 'grain'
    crop_keys['23000'] = 'field_misc'
    crop_keys['23001'] = 'alfalfa'
    crop_keys['23003'] = 'alfalfa'
    crop_keys['23005'] = 'cotton'
    crop_keys['23008'] = 'field_misc'
    crop_keys['23009'] = 'field_misc'
    crop_keys['23010'] = 'field_misc'
    crop_keys['23011'] = 'field_misc'
    crop_keys['23025'] = 'field_misc'
    crop_keys['23036'] = 'field_misc'
    crop_keys['23501'] = 'field_misc'
    crop_keys['24000'] = 'grain'
    crop_keys['24013'] = 'grain'
    crop_keys['25003'] = 'field_misc'
    crop_keys['25501'] = 'field_misc'
    crop_keys['26003'] = 'field_misc'
    crop_keys['27000'] = 'field_misc'
    crop_keys['27001'] = 'field_misc'
    crop_keys['27003'] = 'field_misc'
    crop_keys['27010'] = 'field_misc'
    crop_keys['27018'] = 'subtropical_misc'
    crop_keys['28000'] = 'avocado'
    crop_keys['28001'] = 'field_misc'
    crop_keys['28004'] = 'subtropical_misc'
    crop_keys['28008'] = 'field_misc'
    crop_keys['28009'] = 'field_misc'
    crop_keys['28011'] = 'field_misc'
    crop_keys['28012'] = 'field_misc'
    crop_keys['28014'] = 'subtropical_misc'
    crop_keys['28018'] = 'field_misc'
    crop_keys['28020'] = 'field_misc'
    crop_keys['28023'] = 'field_misc'
    crop_keys['28024'] = 'vegetable_small'
    crop_keys['28025'] = 'deciduous_misc'
    crop_keys['28034'] = 'field_misc'
    crop_keys['28035'] = 'pasture'
    crop_keys['28036'] = 'deciduous_misc'
    crop_keys['28040'] = 'field_misc'
    crop_keys['28045'] = 'pasture'
    crop_keys['28047'] = 'field_misc'
    crop_keys['28051'] = 'field_misc'
    crop_keys['28061'] = 'field_misc'
    crop_keys['28064'] = 'grain'
    crop_keys['28066'] = 'grass'
    crop_keys['28072'] = 'rice'
    crop_keys['28078'] = 'grain'
    crop_keys['28504'] = 'field_misc'
    crop_keys['28509'] = 'idle'
    crop_keys['29103'] = 'grain'
    crop_keys['29109'] = 'field_misc'
    crop_keys['29111'] = 'field_misc'
    crop_keys['29113'] = 'field_misc'
    crop_keys['29119'] = 'corn'
    crop_keys['29121'] = 'cotton'
    crop_keys['29122'] = 'melon'
    crop_keys['29123'] = 'field_misc'
    crop_keys['29125'] = 'field_misc'
    crop_keys['29126'] = 'field_misc'
    crop_keys['29127'] = 'field_misc'
    crop_keys['29129'] = 'field_misc'
    crop_keys['29131'] = 'field_misc'
    crop_keys['29133'] = 'field_misc'
    crop_keys['29135'] = 'field_misc'
    crop_keys['29136'] = 'tomato'
    crop_keys['29137'] = 'field_misc'
    crop_keys['29139'] = 'grain'
    crop_keys['29141'] = 'grape'
    crop_keys['29143'] = 'grape'
    crop_keys['30000'] = 'idle'
    crop_keys['30005'] = 'nursery'
    crop_keys['30006'] = 'idle'
    crop_keys['30008'] = 'idle'
    crop_keys['40008'] = 'idle'
    crop_keys['43026'] = 'deciduous_misc'
    crop_keys['46000'] = 'idle'
    crop_keys['46502'] = 'idle'
    crop_keys['52000'] = 'idle'
    crop_keys['52003'] = 'idle'
    crop_keys['52013'] = 'idle'
    crop_keys['52018'] = 'idle'
    crop_keys['55000'] = 'idle'
    crop_keys['55001'] = 'idle'
    crop_keys['55002'] = 'idle'
    crop_keys['55008'] = 'idle'
    crop_keys['55501'] = 'idle'
    crop_keys['56005'] = 'idle'
    crop_keys['60000'] = 'idle'
    crop_keys['61001'] = 'idle'
    crop_keys['61005'] = 'idle'
    crop_keys['61006'] = 'idle'
    crop_keys['61007'] = 'idle'
    crop_keys['61008'] = 'idle'
    crop_keys['63000'] = 'idle'
    crop_keys['64500'] = 'idle'
    crop_keys['65000'] = 'idle'
    crop_keys['65011'] = 'idle'
    crop_keys['65015'] = 'idle'
    crop_keys['65019'] = 'idle'
    crop_keys['65021'] = 'idle'
    crop_keys['65503'] = 'idle'
    crop_keys['66000'] = 'idle'
    crop_keys['67000'] = 'idle'
    crop_keys['67001'] = 'idle'
    crop_keys['67002'] = 'idle'
    crop_keys['67003'] = 'idle'
    crop_keys['67009'] = 'idle'
    crop_keys['68002'] = 'idle'
    crop_keys['68009'] = 'idle'
    crop_keys['69000'] = 'idle'
    crop_keys['71000'] = 'idle'
    crop_keys['72000'] = 'idle'
    crop_keys['74000'] = 'idle'
    crop_keys['77000'] = 'idle'
    crop_keys['89000'] = 'idle'
    crop_keys['99999'] = 'idle'
    crop_keys['9999991'] = 'idle'
    crop_keys['9999992'] = 'idle'
    crop_keys['9999993'] = 'idle'
    crop_keys['9999994'] = 'idle'
    crop_keys['9999995'] = 'idle'
    crop_keys['9999996'] = 'idle'
    crop_keys['9999997'] = 'idle'
    crop_keys['9999998'] = 'idle'
    crop_keys['9999999'] = 'idle'
	

    crop_key_list = ['alfalfa', 'almond', 'apple', 'avocado', 'citrus', 'corn', 'cotton', 'cucumber', 'deciduous_misc', 'field_misc', 'grain', 'grape', 'grass', 'idle', 'melon', 'nursery', 'onion', 'pasture', 'peach', 'pepper', 'pistachio', 'pond', 'potatoe', 'rice', 'safflower', 'squash', 'strawberry', 'subtropical_misc', 'tomato', 'vegetable_small', 'walnut']
    crop_group_keys = {}
    crop_group_keys['alfalfa'] = 1
    crop_group_keys['almond'] = 4
    crop_group_keys['apple'] = 4
    crop_group_keys['avocado'] = 4
    crop_group_keys['citrus'] = 4
    crop_group_keys['corn'] = 1
    crop_group_keys['cotton'] = 1
    crop_group_keys['cucumber'] = 2
    crop_group_keys['deciduous_misc'] = 4
    crop_group_keys['field_misc'] = 1
    crop_group_keys['grain'] = 1
    crop_group_keys['grape'] = 3
    crop_group_keys['grass'] = 0
    crop_group_keys['idle'] = 0
    crop_group_keys['melon'] = 2
    crop_group_keys['nursery'] = 4
    crop_group_keys['onion'] = 2
    crop_group_keys['pasture'] = 0
    crop_group_keys['peach'] = 4
    crop_group_keys['pepper'] = 1
    crop_group_keys['pistachio'] = 4
    crop_group_keys['pond'] = 0
    crop_group_keys['potatoe'] = 1
    crop_group_keys['rice'] = 1
    crop_group_keys['safflower'] = 2
    crop_group_keys['squash'] = 2
    crop_group_keys['strawberry'] = 2
    crop_group_keys['subtropical_misc'] = 4
    crop_group_keys['tomato'] = 2
    crop_group_keys['vegetable_small'] = 2
    crop_group_keys['walnut'] = 4

    irrdemand = {}
    irrdemand_tot = Crop('zone15')
    for x in crop_key_list:
      irrdemand[x] = np.sum(irrdemand_tot.etM[x]['AN'])
	
  return crop_keys, crop_key_list, irrdemand, crop_group_keys

def find_cropping(year, shapefile_name, acreage_files):
  sections = gpd.read_file(shapefile_name)
  counter = 0
  crop_keys, crop_key_list, irrdemand, crop_group_keys = find_crop_keys()
  crop_type_list = {}
#for df_row, year in enumerate(range(1997,2017)):    # editted here to include up to 2016 
  year_string = str(year) 
  year_two_digits = year_string[-2:]
  year_date_time = pd.to_datetime(year, format='%Y')
  dataframe_columns = []
  dataframe_columns.append('CO_MTRS')
  for x in crop_key_list:
    dataframe_columns.append(x)
  dataframe_columns.append('WATERUSE')
  comtrs_with_crop_name = pd.DataFrame(columns = dataframe_columns)
  print(comtrs_with_crop_name)
  # directory=os.path.join('calPIP_PUR_crop_acreages_july26', year_two_digits + 'files' )
  # directory=os.path.join('/Users/nataliemall/Box Sync/herman_research_box/tulare_git_repo/pur_data_raw/data_with_comtrs/')
  for county in np.arange(1,59):
    print(year, end = " ")
    print(county)	
#    replace_bad_characters(year, county)
#    if year < 2005:
#      add_comtrs_1990_2004(year, county)  
#    else:
#      add_comtrs_2005_2016(year, county)
#    compile_data_by_comtrs(year)
#    normalize_data(year, county)
	  
      
    comtrs_compiled_data = pd.read_csv(os.path.join(acreage_files, (year_two_digits + 'files'), ('all_data_normalized_year' + year_two_digits + '_by_COMTRS_' + str(county).zfill(2)+ '.csv' )), sep = '\t')
    comtrs_compiled_data= comtrs_compiled_data.rename(columns={"comtrs": "CO_MTRS"})
    county_comtrs = pd.DataFrame()
    for x in crop_key_list:
      county_comtrs[x] = np.zeros(len(comtrs_compiled_data['CO_MTRS']))
    county_comtrs['WATERUSE'] = np.zeros(len(comtrs_compiled_data['CO_MTRS']))
    county_comtrs['CROPGROUP'] = np.zeros(len(comtrs_compiled_data['CO_MTRS']))
    crop_type_list[str(year)] = []
    max_acres = np.zeros(len(comtrs_compiled_data['CO_MTRS']))
    crop_type_max = np.zeros(len(comtrs_compiled_data['CO_MTRS']))
    for x in comtrs_compiled_data:
      if x == 'CO_MTRS':
        county_comtrs['CO_MTRS'] = comtrs_compiled_data[x]
      if x in crop_keys:
        crop_type = crop_keys[x]
        county_comtrs[crop_type] += comtrs_compiled_data[x]
        crop_type_list[str(year)].append(crop_type)
        county_comtrs['WATERUSE'] += irrdemand[crop_type]*comtrs_compiled_data[x]/(12.0*640.0)
        for xx in range(0, len(comtrs_compiled_data['CO_MTRS'])):
          if comtrs_compiled_data[x][xx] > max_acres[xx]:
            max_acres[xx] = comtrs_compiled_data[x][xx] * 1.0
            crop_type_max[xx] = int(crop_group_keys[crop_type])
    county_comtrs['CROPGROUP'] = crop_type_max

    comtrs_with_crop_name = pd.concat([comtrs_with_crop_name, county_comtrs], axis = 0, ignore_index = True)
    print(comtrs_with_crop_name)
  crop_sections = sections.merge(comtrs_with_crop_name, on = 'CO_MTRS', how = 'left')
  header_list = []
  for x in crop_key_list:
    header_list.append(x)
    crop_sections = crop_sections[crop_sections[x].notna()]
  header_list.append('CO_MTRS')
  header_list.append('WATERUSE')
  header_list.append('CROPGROUP')
  header_list.append('geometry')
  crop_sections = crop_sections[header_list]
  crop_sections = crop_sections.to_crs(epsg = 4326)    
  crop_sections = crop_sections.reset_index()
  print(crop_sections)
  crop_sections = crop_sections[np.logical_not(crop_sections.duplicated(subset = 'CO_MTRS', keep = 'first'))]
  print(crop_sections)
  return crop_sections
  #try:
    #crop_data_in_irrigation_district = comtrs_compiled_data.loc[(comtrs_compiled_data["comtrs"].isin(comtrs_in_irrigation_dist.co_mtrs)) ]
  #except:
    #crop_data_in_irrigation_district = comtrs_compiled_data.loc[(comtrs_compiled_data["comtrs"].isin(comtrs_in_irrigation_dist.CO_MTRS)) ]
        
  #crop_data_in_irrigation_district = crop_data_in_irrigation_district.rename(columns = {"level_0": "comtrs"}) 
  #crop_data_in_irrigation_district = crop_data_in_irrigation_district.set_index('comtrs')
