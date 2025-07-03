#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri May 12 14:08:02 2023

@author: vpremier
"""

# from usgsm2m.api import API
# from usgsm2m.usgsm2m import USGSM2M

# from sentinelsat import SentinelAPI, read_geojson, geojson_to_wkt
# from collections import OrderedDict


import subprocess
import requests
import os
import geopandas as gpd
from datetime import datetime as dt
import pandas as pd
from zipfile import ZipFile
from datetime import datetime
from tqdm import tqdm
from shapely.geometry import box

import cgi
import json
import requests
from getpass import getpass
import sys
import time
import argparse
import os
import pandas as pd
import warnings
warnings.filterwarnings("ignore")


# Send http request
def sendRequest(url, data, apiKey = None, exitIfNoResponse = True):
    """
    Send a request to an M2M endpoint and returns the parsed JSON response.

    Parameters:
    endpoint_url (str): The URL of the M2M endpoint
    payload (dict): The payload to be sent with the request

    Returns:
    dict: Parsed JSON response
    """  
    
    json_data = json.dumps(data)
    
    if apiKey == None:
        response = requests.post(url, json_data)
    else:
        headers = {'X-Auth-Token': apiKey}              
        response = requests.post(url, json_data, headers = headers)  
    
    try:
      httpStatusCode = response.status_code 
      if response == None:
          print("No output from service")
          if exitIfNoResponse: sys.exit()
          else: return False
      output = json.loads(response.text)
      if output['errorCode'] != None:
          print(output['errorCode'], "- ", output['errorMessage'])
          if exitIfNoResponse: sys.exit()
          else: return False
      if  httpStatusCode == 404:
          print("404 Not Found")
          if exitIfNoResponse: sys.exit()
          else: return False
      elif httpStatusCode == 401: 
          print("401 Unauthorized")
          if exitIfNoResponse: sys.exit()
          else: return False
      elif httpStatusCode == 400:
          print("Error Code", httpStatusCode)
          if exitIfNoResponse: sys.exit()
          else: return False
    except Exception as e: 
          response.close()
          print(e)
          if exitIfNoResponse: sys.exit()
          else: return False
    response.close()
    
    return output['data']



def downloadfiles(downloadIds):
    downloadIds.append(download['downloadId'])
    print("    DOWNLOADING: " + download['url'])
    downloadResponse = requests.get(download['url'], stream=True)

    # parse the filename from the Content-Disposition header
    content_disposition = cgi.parse_header(downloadResponse.headers['Content-Disposition'])[1]
    filename = os.path.basename(content_disposition['filename'])
    filepath = os.path.join(data_dir, filename)

    # write the file to the destination directory
    with open(filepath, 'wb') as f:
        for data in downloadResponse.iter_content(chunk_size=8192):
            f.write(data)
    #print(f"    DOWNLOADED {filename} ({i+1}/{len(downloadIds)})")
    


def prompt_ERS_login(serviceURL, username, token):
    print("Logging in...\n")

    # Use requests.post() to make the login request
    response = requests.post(f"{serviceUrl}login-token", json={'username': username, 'token': token})

    # Check for successful response
    if response.status_code == 200:  
        apiKey = response.json()['data']
        print('\nLogin Successful, API Key Received!')
        headers = {'X-Auth-Token': apiKey}
        return apiKey
    else:
        print("\nLogin was unsuccessful, please try again or create an account at: https://ers.cr.usgs.gov/register.")
        

def create_search_payload(datasetName, metadataFilter, acquisitionFilter):
    # create search payload from input filters
    search_payload = {
        'maxResults': 10,
        'datasetName' : datasetName,
        'sceneFilter' : {
            'metadataFilter': metadataFilter,
            'acquisitionFilter' : acquisitionFilter,
            'cloudCoverFilter' : {'min' : 0, 'max' : 50},
        }
    }
    return search_payload

def get_matching_landsat(date_start, date_end, username, psw, data_dir, shp = None,
                         max_cc = 90, sat = ['LT05','LE07','LC08','LC09']):
    
    """Returns list of matching Landsat scenes for a selected period and
        for a specific area (defined from a shapefile). The username and
        password of your USGS EROS account are reuired. Please see
        
        https://pypi.org/project/usgsm2m/
        https://m2m.cr.usgs.gov/
        
        It is necessary to request the use of the Machine-to-Machine API.
        The request is done from the USGS account.
    
    Parameters
    ----------
    date_start : str
        starting date
    date_end : str
        ending date
    shp : str 
        path to a shapefile with your area of interest. Any crs is accepted
    username : str
        username of your USCGS account
    psw : str
        password of your USCGS account
    max_cc : int, optional
        maximum cloud coverage. Default is 90%
    sat : list, optional
        list with desired missions. If not specified, all matching missions are selected. 
        Possible options are LT05, LE07, LC08 and LC09
    
    Returns
    -------
    sceneList : list
        list of the matching landsat scenes
    """
    
    
    serviceUrl = "https://m2m.cr.usgs.gov/api/api/json/stable/"
    apiKey = prompt_ERS_login(serviceUrl, 'v.premier', 'hm@tcozYDxATL1iUYE7!xJ8qe4K7Gjt!!pRKLSisJGURFXaa2CqB_VFHvrBpuBSV')    
    
    # Initialize a new API instance and get an access key
    # api = API(username, psw)
     
    if shp is None:  
        boundsdata=box(*[-180,-90,180, 90]).wkt
        lat = 0
        lon = 0
    else:
        #read the shapefile
        gdf = gpd.read_file(shp)
        
        # convert crs (otherwise may result in an error)
        if not gdf.crs == 'EPSG:4326':
            gdf = gdf.to_crs('EPSG:4326')  
            
        # Extract the Bounding Box Coordinates
        bounds = gdf.total_bounds
    
        # get the center of the AOI
        # lat = (bounds[1] + bounds[3])/2
        # lon = (bounds[0] + bounds[2])/2

    
    # Collection 2 Level 1 (Landsat)
    satellite = {'LT05':'landsat_tm_c2_l1',
                  'LE07':'landsat_etm_c2_l1',
                  'LC08':'landsat_ot_c2_l1',
                  'LC09':'landsat_ot_c2_l1'}
    
    # Request
    sceneList = []   
    for key in satellite:
        
        
        if key not in sat:
            continue
        
        # datafilter_payload = {'datasetName': satellite[key]}
        # datafilter_result = sendRequest(serviceUrl + "dataset-filters", datafilter_payload, apiKey)
        # filterId = datafilter_result[5]['id']

        # metadataFilter = {'filterType': 'value',
        #                     'filterId': filterId,
        #                     'value' : '5'}

        acquisitionFilter = {'start' : date_start, 'end' : date_end}
        
        spatialFilter =  {'filterType' : 'mbr',
                           'lowerLeft' : {'latitude' : gdf.bounds.miny[0],\
                                          'longitude' : gdf.bounds.minx[0]},
                          'upperRight' : { 'latitude' : gdf.bounds.maxy[0],\
                                          'longitude' : gdf.bounds.maxx[0]}}
            
            
        scene_search  = {'datasetName': satellite[key],
                            'sceneFilter' : {
                                'spatialFilter': spatialFilter,
                                'cloudCoverFilter' : {'min' : 0, 'max' : max_cc},
                                'acquisitionFilter' : acquisitionFilter,}
                            }

            

            
        scenes  = sendRequest(serviceUrl + "scene-search", scene_search, apiKey)
        
        
        sceneList = []
        entityList = []
        for result in scenes['results']:
            # Add this scene to the list I would like to download
            sceneList.append(result['displayId'])
            entityList.append(result['entityId'])
            


                
        # scenes = api.search(
        #     dataset=satellite[key],
        #     bbox=list(bounds),
        #     start_date=date_start,
        #     end_date=date_end,
        #     max_cloud_cover=max_cc,
        #     max_results=10000)
        
        # append product id to the list
        # for s in scenes:
        #     scene_name = s['landsat_product_id']
            
        #     if scene_name[:4] in sat:
        #         sceneList.append(scene_name)
    
    landsat_sensor = [s.split('_')[0] for s in sceneList]
    landsat_sensor = list(dict.fromkeys(landsat_sensor))  
    
    tileList = [s.split('_')[2] for s in sceneList]
    tileList = list(dict.fromkeys(tileList))  
    
    print('Found %i Landsat scenes from %s to %s with maximum cloud coverage %i%%' 
          % (len(sceneList), date_start, date_end, max_cc))
    
    print('Found %i sensors: %s' 
          % (len(landsat_sensor), ', '.join(map(str, landsat_sensor))))
    
    print('The shapefile intersects %i tiles (xxx path yyy row): %s' 
          % (len(tileList), ', '.join(map(str, tileList))))
    
    
    download_payload = {'datasetName' : satellite[key], 
                    'entityIds' : entityList}

    downloadOptions = sendRequest(serviceUrl + "download-options", download_payload, apiKey)

    pd.json_normalize(downloadOptions)
    
    availableproducts = []
    for product in downloadOptions:
            # Make sure the product is available for this scene
            if product['available'] == True and product['downloadSystem'] != 'folder':
                    availableproducts.append({'entityId' : product['entityId'],
                                       'productId' : product['id']})
                
    requestedDownloadsCount = len(availableproducts)

    # set a label for the download request
    label = "download-sample"
    download_req_payload = {'downloads' : availableproducts,
                                     'label' : label}
    
    requestResults = sendRequest(serviceUrl + "download-request", download_req_payload, apiKey)


    if requestResults['preparingDownloads'] != None and len(requestResults['preparingDownloads']) > 0:
        download_retrieve_payload = {'label' : label}
        
        print("Requesting for additional available download urls...")
        moreDownloadUrls = sendRequest(serviceUrl + "download-retrieve", download_retrieve_payload, apiKey)
    
        downloadIds = []  
    
    
    
        print("\nDownloading from available downloads:")    
        for download in moreDownloadUrls['available']:
            if str(download['downloadId']) in requestResults['newRecords'] or str(download['downloadId']) in requestResults['duplicateProducts']:
                downloadfiles(downloadIds)
    
    
    
    
        print("\nDownloading from requested downloads:")        
        for download in moreDownloadUrls['requested']:
            if str(download['downloadId']) in requestResults['newRecords'] or str(download['downloadId']) in requestResults['duplicateProducts']:
                downloadfiles(downloadIds)               
    
    
    
        # Didn't get all of the reuested downloads, call the download-retrieve method again probably after 30 seconds
        while len(downloadIds) < (requestedDownloadsCount - len(requestResults['failed'])): 
            preparingDownloads = requestedDownloadsCount - len(downloadIds) - len(requestResults['failed'])
            print("    ", preparingDownloads, " downloads are not available. Waiting for 30 seconds...")
            time.sleep(30)
            print("    Trying to retrieve data after waiting for 30 seconds...")
            moreDownloadUrls = sendRequest(serviceUrl + "download-retrieve", download_retrieve_payload, apiKey)
            for download in moreDownloadUrls['available']:                            
                if download['downloadId'] not in downloadIds and (str(download['downloadId']) in requestResults['newRecords'] or str(download['downloadId']) in requestResults['duplicateProducts']):
                    downloadfiles(downloadIds)
    
    
    else:
        print("\nAll downloads are available to download. Retrieving...\n")# Get all available downloads
        i = 0
        for download in requestResults['availableDownloads']:
            
            print("DOWNLOADING: " + download['url'])
            
            downloadResponse = requests.get(download['url'], stream=True)
    
            # parse the filename from the Content-Disposition header
            content_disposition = cgi.parse_header(downloadResponse.headers['Content-Disposition'])[1]
            filename = os.path.basename(content_disposition['filename'])
            filepath = os.path.join(data_dir, filename)
    
            # write the file to the destination directory
            with open(filepath, 'wb') as f:
                for data in downloadResponse.iter_content(chunk_size=8192):
                    f.write(data)
            i+=1
            print(f"DOWNLOADED {filename} ({i}/{len(requestResults['availableDownloads'])})\n")
            


        
    return sceneList



def download_landsat(landsatList, outdir, username, psw,
                     tileList = None, tierList = None):
    
    """Downloads a list of Landsat given as input. Possibility to filter 
        by tile and tier. The same credentials as function 
        get_matching_landsat() are required.
        
    
    Parameters
    ----------
    landsatList : list
        list of landsat scenes
    outdir : str
        path where you want to save the archives
    username : str
        username of your USCGS account
    psw : str
        password of your USCGS account
    tileList : list, optional
        tiles (str) to download    
    sat : list, optional
        tiers (str) to download 
    
    """
    # access 
    ee = USGSM2M(username, psw)
    
    for scene in landsatList:
        # tile number
        tile = os.path.basename(scene).split('_')[2]
 
        #tier 
        tier = scene.split('_')[-1]
          
        if os.path.exists(outdir + scene + '.tar'):          
            print(scene + ' already downloaded')
            
        else:
            
            tile_cond = tileList is None or tile in tileList
            tier_cond = tierList is None or tier in tierList
            
            if tile_cond and tier_cond:
                try:
                    ee.download([scene], output_dir = outdir)
             
                except:
                    print('Error in downloading ' + scene)
                    
                    
                    
def get_matching_s2(date_start, date_end, shp, username, psw,
                  max_cc = 90, tile = None, RON = None, filter_date = True):
    
    """Returns list of matching Sentinel-2 scenes for a selected period and
        for a specific area (defined from a shapefile). The username and
        password of your Copernicus Open Access Hub account are reuired. 
        Please see
        
        https://pypi.org/project/usgsm2m/
        https://m2m.cr.usgs.gov/
        

    
    Parameters
    ----------
    date_start : str
        starting date
    date_end : str
        ending date
    shp : str 
        path to a shapefile with your area of interest. Any crs is accepted
    username : str
        username of your Copernicus account
    psw : str
        password of your Copernicus account
    max_cc : int, optional
        maximum cloud coverage. Default is 90%
    tile : str, optional
        specific tile to be downloaded
    
    Returns
    -------
    products : list
        list of the matching scenes
    """   

    api = SentinelAPI(username, psw)
    
    # search by polygon, time, and SciHub query keywords
    gdf = gpd.read_file(shp)
    
    # convert crs (otherwise may result in an error)
    if not gdf.crs == 'EPSG:4326':
        gdf = gdf.to_crs('EPSG:4326') 
    bounds = gdf.envelope
    boundsdata = bounds[0].wkt
    
    # change format dates
    date_start_dt = dt.strptime(date_start, "%Y-%m-%d")
    date_end_dt = dt.strptime(date_end, "%Y-%m-%d")
    
    
    products = OrderedDict()
    
    query_kwargs = {
            'area':boundsdata,
            'platformname': 'Sentinel-2',
            'producttype': 'S2MSI1C',
            'date': (date_start_dt, date_end_dt),
            'cloudcoverpercentage':(0, max_cc)}
    
    if tile is not None: 
        query_kwargs['tileid'] = tile
    
    if RON is not None: 
        query_kwargs['relativeorbitnumber'] = RON
        
    pp = api.query(**query_kwargs)
    products.update(pp)
     
    tileList = [products[key]['tileid'] for key in products]
    tileList = list(dict.fromkeys(tileList))
    
    if filter_date:
        nameList = [products[key]['filename'] for key in products]
        commonName = [('_').join(f.split('_')[:6]) for f in nameList]
        
        df = pd.DataFrame(columns=['commonName','nameList'])  
        df['commonName'] = commonName
        df['nameList'] = nameList
        df = df.sort_values(by='nameList')
        df_fltd = df.drop_duplicates(subset='commonName', keep='last')
        dropped = pd.concat([df, df_fltd]).drop_duplicates(keep=False)

        products_fltd = products.copy()
        for k in products:
            if products[k]['filename'] in dropped.nameList.values:
                products_fltd.popitem(k)
        
        products = products_fltd
    
    print('Found %i Sentinel-2 scenes from %s to %s with maximum cloud coverage %i%%' 
          % (len(products),date_start, date_end, max_cc))
    
    print('The shapefile intersects %i tiles: %s' 
          % (len(tileList), ', '.join(map(str, tileList))))
    
    
    return products
 
    

def download_s2(s2List, outdir, username, psw, totp):
    """Downloads a list of Sentinel-2 given as input. Credentials 
        from CREODIAS: please check
        
        https://creodias.eu/eo-data-catalogue-api-manual
        
        To make it working, run the following command from a terminal
            KEYCLOAK_TOKEN=$(curl -s --location --request POST 'https://identity.cloudferro.com/auth/realms/dias/protocol/openid-connect/token' \
                --data-urlencode 'grant_type=password' \
                --data-urlencode 'username=<USER>' \
                --data-urlencode 'password=<PASSWORD>' \
                --data-urlencode 'client_id=CLOUDFERRO_PUBLIC'|jq .access_token|tr -d '"')
        
        after replacing with your username and password.
    
        
    
    Parameters
    ----------
    s2List : list
        list of Sentinel-2 scenes (organised as in the output of function
                                   get_matching_s2() )
    outdir : str
        path where you want to save the archives
    username : str
        username of your CREODIAS account
    psw : str
        password of your CREODIAS account
    
    """
    
    cmd_str = ('').join(['''
            curl -s --location \
            --request POST 'https://identity.cloudferro.com/auth/realms/Creodias-new/protocol/openid-connect/token' \
            --data-urlencode 'grant_type=password' \
            --data-urlencode 'username=%s' ''' %username,
            '''--data-urlencode 'password=%s' ''' %psw,
            '''--data-urlencode 'totp=%s' ''' %totp,
            '''--data-urlencode 'client_id=CLOUDFERRO_PUBLIC'|jq .access_token|tr -d '"' '''])
    result=subprocess.run(cmd_str, shell=True, stdout=subprocess.PIPE)
    token = result.stdout.decode('utf-8')[:-1]
           
           
    for scene in s2List:
        
        fileName = s2List[scene]['filename']
        
        # query by name 
        url = ('').join(["https://datahub.creodias.eu/odata/v1/Products?$filter=Name eq ",
                        "'",
                        fileName,
                        "'"])
        
        # A GET request to the API
        response = requests.get(url)
        
        # response
        response_json = response.json()
        
        outname = outdir + os.sep +  fileName.replace('.SAFE','.zip')
        
        if os.path.exists(outname) and os.stat(outname).st_size>0:
            print('%s already downloaded' %fileName.replace('.SAFE','.zip'))
        
        else:
            # bash command for authentication and download
            # cmd_str = ('').join(['''
            #         wget  --header "Authorization: Bearer $(curl -s --location \
            #         --request POST 'https://identity.cloudferro.com/auth/realms/Creodias-new/protocol/openid-connect/token' \
            #         --data-urlencode 'grant_type=password' \
            #         --data-urlencode 'username=%s' ''' %username,
            #         '''--data-urlencode 'password=%s' ''' %psw,
            #         '''--data-urlencode 'totp=%s' ''' %totp,
            #         '''--data-urlencode 'client_id=CLOUDFERRO_PUBLIC'|jq .access_token|tr -d '"')" ''',
            #         " 'http://datahub.creodias.eu/odata/v1/Products(",
            #         response_json['value'][0]['Id'],
            #         ")/$value' -O ",
            #         outname])
            # subprocess.run(cmd_str, shell=True)
                
             cmd_str = ('').join(['''
                     wget  --header "Authorization: Bearer ''',
                     token,
                     '''" 'http://datahub.creodias.eu/odata/v1/Products(''',
                     response_json['value'][0]['Id'],
                     ")/$value' -O ",
                     outname])
             subprocess.run(cmd_str, shell=True)



           
def get_matching_s2_cdse(date_start, date_end, username, psw, shp = None,
                         max_cc = 90, tile = None, filter_date = True):
    
    """Returns list of matching Sentinel-2 scenes for a selected period and
        for a specific area (defined from a shapefile). The username and
        password of your Copernicus Data Space Ecosystem account are required. 
        Please see
        
        https://dataspace.copernicus.eu/
            
        Parameters
        ----------
        date_start : str
            starting date
        date_end : str
            ending date
        shp : str 
            path to a shapefile with your area of interest. Any crs is accepted
        username : str
            username of your CDSE account
        psw : str
            password of your CDSE account
        max_cc : int, optional
            maximum cloud coverage. Default is 90%
        tile : str, optional
            specific tile to be downloaded
        filter_date : bool, optional
            whether to filter double dates, by keeping the last processing time
        
        Returns
        -------
        products : list
            list of the matching scenes
    """   

    # access to the Copernicus Dataspce ecosystem
    data = {
           "client_id": "cdse-public",
           "username": username,
           "password": psw,
           "grant_type": "password",
       }
    try:
        r = requests.post(
            "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token",
            data=data,
        )
        r.raise_for_status()
    except Exception as e:
        raise Exception(
            f"Access token creation failed. Reponse from the server was: {r.json()}"
        )
        
        
    if shp is None:  
        boundsdata=box(*[-180,-90,180, 90]).wkt
    else:
        # search by polygon, time, and CDSE query keywords
        gdf = gpd.read_file(shp)
        
        # convert crs (otherwise may result in an error)
        if not gdf.crs == 'EPSG:4326':
            gdf = gdf.to_crs('EPSG:4326') 
            
        boundsdata=box(*gdf.total_bounds).wkt
    


    data_collection = "S2MSI1C"

    # query
    if tile is None:
        query = ('').join([f"https://catalogue.dataspace.copernicus.eu/odata/v1/Products?$filter=",
                           "Attributes/OData.CSC.StringAttribute/any(att:att/Name eq 'productType'",
                           " and att/OData.CSC.StringAttribute/Value eq '",
                           data_collection,
                           "')",
                           " and Attributes/OData.CSC.DoubleAttribute/any(att:att/Name eq 'cloudCover'",
                           " and att/OData.CSC.DoubleAttribute/Value lt ",
                            str(max_cc),
                            ") and OData.CSC.Intersects(area=geography'SRID=4326;",
                            boundsdata,
                            "') and ContentDate/Start gt ",
                            date_start,
                            "T00:00:00.000Z and ContentDate/Start lt ",
                            date_end,
                            "T00:00:00.000Z&$top=1000"])
    else:     
        query = ('').join([f"https://catalogue.dataspace.copernicus.eu/odata/v1/Products?$filter=",
                           "contains(Name,'",
                           tile,
                           "') and Attributes/OData.CSC.StringAttribute/any(att:att/Name eq 'productType'",
                           " and att/OData.CSC.StringAttribute/Value eq '",
                           data_collection,
                           "')",
                           " and Attributes/OData.CSC.DoubleAttribute/any(att:att/Name eq 'cloudCover'",
                           " and att/OData.CSC.DoubleAttribute/Value lt ",
                            str(max_cc),
                            ") and OData.CSC.Intersects(area=geography'SRID=4326;",
                            boundsdata,
                            "') and ContentDate/Start gt ",
                            date_start,
                            "T00:00:00.000Z and ContentDate/Start lt ",
                            date_end,
                            "T00:00:00.000Z&$top=1000"])

    json = requests.get(query).json()
    
    products = pd.DataFrame.from_dict(json['value'])
    
     
    if filter_date:
        # keep last processing date ( or newest Processing Baseline Nxxxx)
        
        products["commonName"] = [('_').join([f.split('_')[i] for i in[0,1,2,4,5]]) for f in products['Name']]
        

        products = products.sort_values(by='Name')
        products_fltd = products.drop_duplicates(subset='commonName', keep='last')
        
        products = products_fltd
        products_fltd = products_fltd.reset_index(drop=True, inplace=True)
    
    print('Found %i Sentinel-2 scenes from %s to %s with maximum cloud coverage %i%%' 
          % (len(products),date_start, date_end, max_cc))
    
    
    
    return products




def download_s2_cdse(s2List, outdir, username, psw):
    """Downloads a list of Sentinel-2 given as input. Credentials 
        from CDSE: please check
        
        https://dataspace.copernicus.eu/
        https://documentation.dataspace.copernicus.eu/APIs/OData.html
        
    Parameters
    ----------
    s2List : pd.DataFrame
        dataframe with the Sentinel-2 scenes (organised as in the output of function
                                   get_matching_s2_cop() )
    outdir : str
        path where you want to save the archives
    username : str
        username of your CDSE account
    psw : str
        password of your CDSE account
    
    """
    
    
    def get_access_token(username, psw):
        # access token is valid for 10 minutes
        # refresh token is valid for 60 minutes and can be used for generating
        # a new access token without using your credentials
        
        # refresh token (expires in 600s)
        cmd_str = ('').join(['''
                curl --location \
                --location --request POST 'https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token' \
                --data-urlencode 'grant_type=password' \
                --data-urlencode 'username=%s' ''' %username,
                '''--data-urlencode 'password=%s' ''' %psw,
                '''--data-urlencode 'client_id=cdse-public' '''])
        
        result = subprocess.run(cmd_str, shell=True, stdout=subprocess.PIPE)
        token = result.stdout.decode('utf-8')[:-1]
        access_token = token.split('"access_token":"')[1].split('","expires_in"')[0]
        time_token = datetime.now()
        
        return access_token, time_token
    


    def download_file(s2_id, access_token, outname):
        url = ('').join([f"https://zipper.dataspace.copernicus.eu/odata/v1/Products(",
                        s2_id,
                        ")/$value"])
  
        headers = {"Authorization": f"Bearer {access_token}"}
        
        session = requests.Session()
        session.headers.update(headers)
        response = session.get(url, headers=headers, stream=True)
        
        with open(outname, "wb") as file:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    file.write(chunk)
                    
    # fake time token
    time_token = datetime.strptime("1991-06-29", "%Y-%m-%d")
    for i in tqdm(range(0, len(s2List))):
        time_refresh = (datetime.now() - time_token).total_seconds()
        
        if time_refresh >= 600:
            print("Refreshing token")
            access_token, time_token = get_access_token(username, psw)

        fileName = s2List.loc[i]['Name']
        s2_id = s2List.loc[i]['Id']

        
        outname = outdir + os.sep +  fileName.replace('.SAFE','.zip')
        
        if os.path.exists(outname) and os.stat(outname).st_size>0:
            print('%s already downloaded' %fileName.replace('.SAFE','.zip'))
            
            # try:
            #     with ZipFile(outname,'r') as zfile:
            #         zfile.testzip()
            
            # except:
            #     print('%s BadZipFile.. downloading it again' %fileName.replace('.SAFE','.zip'))
            #     download_file(s2_id, access_token, outname)
        
        else:
            print("Downloading %s" %fileName)
            try:
                download_file(s2_id, access_token, outname)
            except:
                print('Error')

           
            
           
            

  
