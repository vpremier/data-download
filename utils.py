#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri May 12 14:08:02 2023

@author: vpremier
"""

import json



def load_config(config_path):
    with open(config_path, 'r') as f:
        config = json.load(f)
    return config





      

def check_config_consistency(config):
    """
    Validate required config fields for preprocessing.
    """


     
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
     
    
    # check landsat_satellite is a list with LT05, LE07, LC08 and LC09
    

    
    # Check outdir they exist in config and are strings
    
    # check that are boolean
    landsat_query
    sentinel2_query
    landsat_download
    sentinel2_download
    
    #check that are string date_start date_end and that date_end is after date_start
    
    #check max_cc is int between 0 and 100
    
    #checks2_tile_list and landsat_tile_list are lists
   

    










          
            

  
