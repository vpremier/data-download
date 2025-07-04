#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri May 12 14:08:02 2023

@author: vpremier
"""

import subprocess
import requests
import os
import geopandas as gpd
import pandas as pd
from datetime import datetime
from tqdm import tqdm
from shapely.geometry import box
import cgi
import json
import sys
import time
import warnings

warnings.filterwarnings("ignore")


def sendRequest(url, data, apiKey = None, exitIfNoResponse = True):
    """
    Send a request to an M2M endpoint and returns the parsed JSON response.
    This function is taken from 
    https://m2m.cr.usgs.gov/api/docs/example/download_data-py
    https://code.usgs.gov/eros-user-services/machine_to_machine/m2m_querying_metadatafilters
    
    
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



def prompt_ERS_login(serviceURL, username, token):
    """
    Log in to the EROS Registration Service (ERS)
    https://ers.cr.usgs.gov/
    
    This function is adapted from 
    https://code.usgs.gov/eros-user-services/machine_to_machine/m2m_landsat_9_search_download
    
    
    Parameters:
    serviceURL (str): The URL of the M2M endpoint
    username (str): Your username
    token (str): Your token. For generating it see: https://www.usgs.gov/media/files/m2m-application-token-documentation
    
    """  
    
    print("Logging in...\n")

    # Use requests.post() to make the login request
    response = requests.post(f"{serviceURL}login-token", json={'username': username, 'token': token})

    # Check for successful response
    if response.status_code == 200:  
        apiKey = response.json()['data']
        print('\nLogin Successful, API Key Received!')
        headers = {'X-Auth-Token': apiKey}
        return apiKey
    else:
        print("\nLogin was unsuccessful, please try again or create an account at: https://ers.cr.usgs.gov/register.")
        
        
        
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
    





def query_landsat(date_start, date_end, username, token, shp = None,
                         max_cc = 90, sat = ['LT05','LE07','LC08','LC09']):
    
    """Returns list of matching Landsat scenes for a selected period and
        for a specific area (defined from a shapefile). The username and
        password of your USGS EROS account are required. Please see
        
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
    token : str
        token from your USCGS account (see: https://www.usgs.gov/media/files/m2m-application-token-documentation)
    max_cc : int, optional
        maximum cloud coverage. Default is 90%
    sat : list, optional
        list with desired missions. If not specified, all matching missions are selected. 
        Possible options are LT05, LE07, LC08 and LC09
    
    Returns
    -------
    results : pd.DataFrame that contains:
            - displayId
            - entityId
    """
    
    
    serviceUrl = "https://m2m.cr.usgs.gov/api/api/json/stable/"
    
    # log in
    apiKey = prompt_ERS_login(serviceUrl, username, token)    
    

    # Collection 2 Level 1 (Landsat): Dataset Alias for each satellite
    satellite = {'LT05':'landsat_tm_c2_l1',
                 'LE07':'landsat_etm_c2_l1',
                 'LC08':'landsat_ot_c2_l1',
                 'LC09':'landsat_ot_c2_l1'}
     
    if shp is None:          
        # Bounding Box Coordinates
        lat_min = -90
        lon_min = -180
        lat_max = 180
        lon_max = 90
        
    else:
        #read the shapefile
        gdf = gpd.read_file(shp)
        
        # convert crs (otherwise may result in an error)
        if not gdf.crs == 'EPSG:4326':
            gdf = gdf.to_crs('EPSG:4326')  
        
        # Bounding Box Coordinates
        lat_min = gdf.bounds.miny[0]
        lon_min = gdf.bounds.minx[0]
        lat_max = gdf.bounds.maxy[0]
        lon_max = gdf.bounds.maxx[0]
        

    # Request
    results = []
    for key in satellite:
        
        if key not in sat:
            continue
        
        # filter by date
        acquisitionFilter = {'start' : date_start, 'end' : date_end}
        
        # filter spatially
        spatialFilter =  {'filterType' : 'mbr',
                           'lowerLeft' : {'latitude' : lat_min,\
                                          'longitude' : lon_min},
                          'upperRight' : { 'latitude' : lat_max,\
                                          'longitude' : lon_max}}
            
            
        scene_search  = {'datasetName': satellite[key],
                         'maxResults':10000, # default is 100
                            'sceneFilter' : {
                                'spatialFilter': spatialFilter,
                                'cloudCoverFilter' : {'min' : 0, 'max' : max_cc},
                                'acquisitionFilter' : acquisitionFilter,}
                            }

        # send request
        scenes  = sendRequest(serviceUrl + "scene-search", scene_search, apiKey)
        

        for result in scenes['results']:
            # Add this scene to the list I would like to download
            results.append({
                'displayId': result['displayId'],
                'entityId': result['entityId']
            })
        
    
    landsat_sensor = [r['displayId'].split('_')[0] for r in results]
    landsat_sensor = list(dict.fromkeys(landsat_sensor))  
    
    tileList = [r['displayId'].split('_')[2] for r in results]
    tileList = list(dict.fromkeys(tileList))  
    
    print('Found %i Landsat scenes from %s to %s with maximum cloud coverage %i%%' 
          % (len(results), date_start, date_end, max_cc))
    
    print('Found %i sensors: %s' 
          % (len(landsat_sensor), ', '.join(map(str, landsat_sensor))))
    
    print('The shapefile intersects %i tiles (xxx path yyy row): %s' 
          % (len(tileList), ', '.join(map(str, tileList))))
    

    return pd.DataFrame(results)



def download_landsat(results, outdir, username, token,
                     pathrowList = None, tierList = None):
    
    """Downloads a list of Landsat given as input. Possibility to filter 
        by tile and tier. The same credentials as function 
        get_matching_landsat() are required.
        
    
    Parameters
    ----------
    results : pd.DataFrame
        contains the list of landsat scenes to be downloaded. It is returned as
        output by the function query_landsat
    outdir : str
        path where you want to save the archives
    username : str
        username of your USCGS account
    token : str
        token from your USCGS account (see: https://www.usgs.gov/media/files/m2m-application-token-documentation)
    pathrow : list, optional
        path/row (str) to download    
    sat : list, optional
        tiers (str) to download 
    
    """
    serviceUrl = "https://m2m.cr.usgs.gov/api/api/json/stable/"
    
    # log in
    apiKey = prompt_ERS_login(serviceUrl, username, token)    
    
    
    satellite = {'LT05':'landsat_tm_c2_l1',
                 'LE07':'landsat_etm_c2_l1',
                 'LC08':'landsat_ot_c2_l1',
                 'LC09':'landsat_ot_c2_l1'}
    
    # the download needs to be done for each satellite separately
    results['satellite'] = results['displayId'].str.split('_').str[0]
    results['pathrow'] = results['displayId'].str.split('_').str[2]
    results['tier'] = results['displayId'].str.split('_').str[-1]


    results['already_downloaded'] = results['displayId'].apply(
        lambda scene: os.path.exists(os.path.join(outdir, scene + '.tar'))
    )

    filtered = results[~results['already_downloaded']].copy()



    if pathrowList:
        filtered = filtered[filtered['pathrow'].isin(pathrowList)]
    
    if tierList:
        filtered = filtered[filtered['tier'].isin(tierList)]

    print(f"Already downloaded: {results['already_downloaded'].sum()} scenes")
    print(f"To download: {len(filtered)} scenes")
                    
    
    for sat_id, group_df in filtered.groupby('satellite'):

        download_payload = {'datasetName': satellite[sat_id],
                            'entityIds' : [r for r in group_df['entityId']]}

        downloadOptions = sendRequest(serviceUrl + "download-options", 
                                      download_payload, 
                                      apiKey)
    
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
                filepath = os.path.join(outdir, filename)
        
                # write the file to the destination directory
                with open(filepath, 'wb') as f:
                    for data in downloadResponse.iter_content(chunk_size=8192):
                        f.write(data)
                i+=1
                print(f"DOWNLOADED {filename} ({i}/{len(requestResults['availableDownloads'])})\n")
                
                    
                    



def query_cdse(date_start, date_end, username, psw, 
                         data_collection = "S2MSI1C", shp = None,
                         max_cc = 90, tile = None, filter_date = True):
    
    """Returns list of matching Sentinel-2 scenes for a selected period and
        for a specific area (defined from a shapefile). The username and
        password of your Copernicus Data Space Ecosystem account are required. 
        Please see
        
        https://dataspace.copernicus.eu/
        https://documentation.dataspace.copernicus.eu/APIs/On-Demand%20Production%20API.html
            
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
        data_collection : str
            default is "S2MSI1C" that refers to the Sentinel-2 L1C data
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
    
    # Define supported data collections
    allowed_collections = ["S2MSI1C", "SY_2_SYN___", "LANDSAT-5", "LANDSAT-7", "LANDSAT-8-ESA"]
    
    if data_collection not in allowed_collections:
        print(f"Allowed data collections: {allowed_collections}")
        print(f"You provided: '{data_collection}'")
        raise ValueError(f"Invalid data_collection: '{data_collection}'. Please use one of the allowed options.")

    else:
        print(f"Using data collection: '{data_collection}'")
        print(f"Allowed data collections: {allowed_collections}")
    

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
    



    # query for SENTINEL-2 or SENTINEL-3 data
    if data_collection == 'S2MSI1C' or data_collection=='SY_2_SYN___':
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
        if tile:   
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
            
            
    elif data_collection in ["LANDSAT-5","LANDSAT-7","LANDSAT-8-ESA"]:
        query = ('').join([
            f"https://catalogue.dataspace.copernicus.eu/odata/v1/Products?$filter=",
            "Collection/Name eq '", data_collection, "'",
            " and Attributes/OData.CSC.DoubleAttribute/any(att:att/Name eq 'cloudCover'",
            " and att/OData.CSC.DoubleAttribute/Value lt ", str(max_cc), ")",
            " and OData.CSC.Intersects(area=geography'SRID=4326;", boundsdata, "')",
            " and ContentDate/Start gt ", date_start, "T00:00:00.000Z",
            " and ContentDate/Start lt ", date_end, "T00:00:00.000Z",
            "&$top=1000"
        ])

        

    json = requests.get(query).json()
    
    products = pd.DataFrame.from_dict(json['value'])
    
     
    if filter_date and not products.empty:
        # keep last processing date ( or newest Processing Baseline Nxxxx)
        
        products["commonName"] = [('_').join([f.split('_')[i] for i in[0,1,2,4,5]]) for f in products['Name']]
        

        products = products.sort_values(by='Name')
        products_fltd = products.drop_duplicates(subset='commonName', keep='last')
        
        products = products_fltd
        products_fltd = products_fltd.reset_index(drop=True, inplace=True)
    
    print('Found %i %s scenes from %s to %s with maximum cloud coverage %i%%' 
          % (len(products),data_collection, date_start, date_end, max_cc))
    
    
    
    return products






def download_cdse(s2List, outdir, username, psw):
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

           
            
           
            

  
