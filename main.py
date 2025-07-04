#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Feb 10 14:14:03 2023

@author: vpremier
"""

from utils import (query_landsat, download_landsat,
                   query_cdse, download_cdse)
import os

from dotenv import load_dotenv
load_dotenv()


# dates for the query/download
date_start = '2005-06-01'
date_end = '2005-06-02'


tile = '200034'

# shapefile wth the AOI
shp = r'/mnt/CEPH_PROJECTS/OEMC/CODE/cdse_download/SierraNevada/SierraNevada.shp'

# directory where you want to download your data
outdir = r'/mnt/CEPH_PROJECTS/PROSNOW/MRI_Andes/Landsat_raw/Landsat-9/' + tile

"""
Landsat download
"""

results = query_landsat(date_start, 
                        date_end, 
                        os.getenv("ERS_USERNAME"), 
                        os.getenv("ERS_TOKEN"), 
                        shp = shp, 
                        max_cc=50)


# download_landsat(results, outdir, os.getenv("ERS_USERNAME"), 
#                     os.getenv("ERS_TOKEN"), pathrowList = ['200034'], tierList = ['T1'])



"""
Sentinel-2 download
"""

# it is possible to query also other collection (default is S2MSI1C)
s2List = query_cdse(date_start, 
                              date_end, 
                              os.getenv("CDSE_USERNAME"), 
                              os.getenv("CDSE_PASSWORD"), 
                              shp=shp,
                              max_cc = 90, 
                              tile=tile, 
                              filter_date = False) 

# download_cdse(s2List, outdir, os.getenv("CDSE_USERNAME"), os.getenv("CDSE_PASSWORD"))



    


