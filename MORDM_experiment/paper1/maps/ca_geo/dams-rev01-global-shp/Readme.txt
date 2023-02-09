Global Reservoirs and Dams (GRanD) version 1.01 Dataset

DESCRIPTION
This archive contains the GRanD v1.01 dataset, created by Lehner et al. (2011). Documentation for data is available at this web site:

http://sedac.ciesin.columbia.edu/pfs/grand.html

Updates and corrections may still be made. If you should discover any problems or errors, please inform us by sending an email describing the issue to: ciesin.info@ciesin.columbia.edu

The archive contains the global data set for either the dams or reservoirs, which are delivered as separate products, in ESRI Shape File format.  To access the Shape Files the contents of the zipfiles must be extracted into a single folder. 

DOWNLOADING DATA
The data can be downloaded via the World Wide Web at http://sedac.ciesin.columbia.edu/pfs/grand.html.

Downloaded files need to be uncompressed using either WinZip (Windows file compression utility) or similar applications before they could be accessed by your GIS software package. Users should expect an increase in the size of downloaded data after decompression. 

Note that users should consult the Technical Documentation for use restrictions and information on the data set. The following fields are found in the Dams data set; users of the reservoirs data set are encouraged to download the dams layer since these fields are not included in the reservoir shape file:

Grand_id:  Unique ID for each point representing a dam and its associated reservoir; the point location is an approximation of the dam location 
Res_name:  Name of reservoir or lake (i.e. impounded water body) 
Dam_name: Name of dam structure 
Alt_name: Alternative name of reservoir or dam (different spelling, different language, secondary name) 
River: Name of impounded river 
Alt_river: Alternative name of impounded river (different spelling, different language, secondary name) 
Main_basin: Name of main basin 
Sub_basin: Name of sub-basin 
Near_city: Name of nearest city 
Alt_city: Alternative name of nearest city (different spelling, different language, secondary name) 
Admin_unit: Name of administrative unit 
Sec_admin: Secondary administrative unit (indicating dams or reservoirs that lie within or are associated with multiple administrative units) 
Country: Name of country 
Sec_cntry: Secondary country (indicating international dams or reservoirs that lie within or are associated with multiple countries) 
Year: Year (not further specified: year of construction; year of completion; year of commissioning; year of refurbishment/update; etc.) 
Alt_year: Alternative year (not further specified: may indicate a multi-year construction phase, an update, or a secondary dam construction) 
Dam_hgt_m: Height of dam in meters 
Alt_hgt_m: Alternative height of dam (may indicate update or secondary dam construction) 
Dam_len_m: Length of dam in meters 
Alt_len_m: Alternative length of dam (may indicate update or secondary dam construction) 
Area_skm: Representative surface area of reservoir in square kilometers; consolidated from other ‘Area’ columns in the following order of priority: ‘Area_poly’ over ‘Area_rep’ over ‘Area_max’ over ‘Area_min’; exceptions apply if value in ‘Area_poly’ column seems unreliable or rounded (see also technical documentation)
Area_poly: Surface area of associated reservoir polygon in square kilometers 
Area_rep: Most reliable reported surface area of reservoir in square kilometers 
Area_max: Maximum value of other reported surface areas in square kilometers 
Area_min: Minimum value of other reported surface areas in square kilometers 


TO USE THE DATA
To access the files content of the zip file must be uncompressed in a single folder. The data are stored in geographic coordinates of decimal degrees based on the World Geodetic System spheroid of 1984 (WGS84).

To view these data in ArcMap, simply unzip to an accessible directory and open the Shape File.

USE CONSTRAINTS
The Global Water Systems Partnership (GWSP) holds the copyright of this dataset. Users are prohibited from any commercial use, sale or free redistribution without explicit written permission from the author. Users should acknowledge the authors as the source and SEDAC as the distributor in the creation of any reports, publications, new datasets, derived products, or services resulting from the use of this dataset (see suggested ciation below). CIESIN also requests reprints of any publications and notification of any redistributing efforts.

DATA ERRORS, CORRECTIONS AND QUALITY ASSESSMENT
CIESIN follows procedures designed to ensure that data disseminated by CIESIN are of reasonable quality. If, despite these procedures, users encounter apparent errors or misstatements in the data, they should contact us at http://www.ciesin.columbia.edu. 

NO WARRANTY OR LIABILITY
CIESIN and the creators provide these data without any warranty of any kind whatsoever either express or implied. Neither CIESIN nor the creators shall be liable for incidental, consequential, or special damages arising out of the use of any data downloaded.

ACKNOWLEDGMENT AND CITATION
The recommended citation for this data is:
Lehner, B., Reidy Liermann, C., Revenga, C., Vörösmarty, C., Fekete, B., Crouzet, P., Döll, P., Endejan, M., Frenken, K., Magome, J., Nilsson, C., Robertson, J., Rödel, R., Sindorf, N., Wisser, D. (2011): High-resolution mapping of the world’s reservoirs and dams for sustainable river-flow management. Frontiers in Ecology and the Environment. Downloaded from the NASA Socioeconomic Data and Applications Center (SEDAC) at http://sedac.ciesin.columbia.edu/pfs/grand.html


May 26, 2011