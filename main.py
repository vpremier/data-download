#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jul  9 09:57:13 2025

@author: vpremier
"""

import os
import time
from dotenv import load_dotenv
load_dotenv()

from landsat_query_download import *
from sentinel2_query_download import *
from utils import *

def run_query_download(config_path):
    
    config = load_config(config_path)
    check_config_consistency(config)

    # flags
    landsat_query = config["query_landsat"]
    sentinel2_query = config["query_sentinel2"]
    
    landsat_download = config["download_landsat"]
    sentinel2_download = config["download_sentinel2"]
    
    
    outdir = config["output_directory"]
    
    date_start = config["date_start"]
    date_end = config["date_end"]
    
    shp = config["shapefile"]
    
    max_cc = config["max_cloudcover"]
    
    landsat_satellite = config["landsat_satellite"]
    

    s2_tile_list = config["s2_tile_list"]
    landsat_tile_list = config["landsat_tile_list"]
    
    
    if landsat_query:

        results = query_landsat(date_start, 
                                date_end, 
                                os.getenv("ERS_USERNAME"), 
                                os.getenv("ERS_TOKEN"), 
                                shp = shp, 
                                max_cc=max_cc,
                                sat = landsat_satellite)
        
    if sentinel2_query:

        s2List = query_cdse(date_start, 
                            date_end, 
                            os.getenv("CDSE_USERNAME"), 
                            os.getenv("CDSE_PASSWORD"), 
                            shp=shp,
                            max_cc = max_cc, 
                            tile=s2_tile_list, 
                            filter_date = True) 
    
    if landsat_download:
                
        download_landsat(results, outdir, os.getenv("ERS_USERNAME"), 
                            os.getenv("ERS_TOKEN"), 
                            pathrowList = landsat_tile_list, 
                            tierList = ['T1'])
    
    if sentinel2_download:
        
        download_cdse(s2List, outdir, os.getenv("CDSE_USERNAME"), os.getenv("CDSE_PASSWORD"))
        
        

    # check the config

    

    
    
    
    
if __name__ == "__main__":    
    
    if len(sys.argv) != 2:
        print("Usage: python main.py path_to_config.json")
    else:
        config_path = sys.argv[1]
        start_time = time.time()
    
        run_query_download(config_path)
    
        end_time = time.time()
        elapsed = end_time - start_time
        elapsed_min = int(elapsed // 60)
        elapsed_sec = int(elapsed % 60)
    
        config = load_config(config_path)
        
        print("\nThe download run succefully.")
        print(f"Execution time: {elapsed_min} minutes and {elapsed_sec} seconds")

