#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Feb 10 14:14:03 2023

@author: vpremier
"""

from utils import (get_matching_landsat, download_landsat,
                   get_matching_s2_cdse, download_s2_cdse)
import os
# ee = EarthExplorer('v.premier', 'landsat_290691')
date_start = '2015-06-01'
date_end = '2015-06-30'
tile = '232084'

# shapefile wth the AOI
# shp = r'/mnt/CEPH_PROJECTS/PROSNOW/MRI_Andes/Dati/Shapefiles/AOI/AOI.shp'
# outdir = r'/mnt/CEPH_PROJECTS/PROSNOW/raw_data/' + tile
shp = r'/mnt/CEPH_PROJECTS/OEMC/CODE/cdse_download/SierraNevada/SierraNevada.shp'
# shp = r'/mnt/CEPH_PROJECTS/SNOWCOP/AOI/basins/AOI_v0.shp'

outdir = r'/mnt/CEPH_PROJECTS/PROSNOW/MRI_Andes/Landsat_raw/Landsat-9/' + tile

"""
Landsat download
"""

# username and password
username = 'v.premier'
psw = 'landsat_290691'

landsatList = get_matching_landsat(date_start, date_end, username, psw, 
                                    shp = shp, max_cc=50, sat=['LC09'])


# for l in landsatList:
#     if os.path.exists(outdir + os.sep + l + '.tar'):
#         print (l + 'already downloaded')
#     else:
#         download_landsat([l], outdir, username, psw, tileList=[tile], tierList = ['T1'])

ss

"""
Sentinel-2 download
"""



# Copernicus Database Ecosystem
username = "valentina.premier@eurac.edu"
psw = "Openeo_290691"
s2List = get_matching_s2_cdse(date_start, date_end, username, psw, shp=shp)
                              # ,
                              # max_cc = 90, tile=tile, filter_date = False) 

# download_s2_cdse(s2List, outdir, username, psw)



    


