import requests
#import s3fs
import json, copy
import numpy as np
from osgeo import gdal, ogr, osr
import time
from netCDF4 import Dataset, date2index
from datetime import date
from datetime import datetime as dt
import xarray as xr
import sys
import os.path
import subprocess
import netCDF4
import math
import csv
import fsspec
import pandas as pd
import statsmodels.api
import urllib

def drainage_basin_call(region):
    if isinstance(region, np.ndarray) and (np.array([180, 360]) * 2 == region.shape).all:
        mask_local = region
        print('Using user defined mask: 360x720')
        lon = np.arange(0.25, 360, 0.5)
        lat = np.arange(-89.75, 90, 0.5)
    # Checking the size of local vs lon and lat
    if mask_local.shape[0] == len(lon) and mask_local.shape[1] == len(lat):
        mask_local = mask_local.T
    elif mask_local.shape[1] == len(lon) and mask_local.shape[0] == len(lat):
        pass
    else:
        print('Warning: verify orientation of mask - not clear if dim(1) = lat & dim(2) = lon')
    # Earth model switch
    earth_mod = 'ellip'
    if earth_mod == 'ellip':  # Ellipsoidal Earth (radius)
        lon = lon.reshape(-1, 1)  # Make lon a column vector
        lat = lat.reshape(-1, 1)  # Make lat a column vector
        lon_r = lon * (math.pi/180)
        lat_r = lat * (math.pi/180)
        dlon_r = np.abs(lon_r[0]-lon_r[1])
        dlat_r = np.abs(lat_r[0]-lat_r[1])
        R_eq = 6378137; #equatorial radius
        R_po = 6356752; #polar radius
        # Earth radius on ellipsoidal Earth as function of latitude:
        cos_lat = np.cos(lat_r)  # Cosine of lat_r
        sin_lat = np.sin(lat_r)   # Sine of lat_r
        numerator = ((R_eq**2 * cos_lat)**2 + (R_po**2 * sin_lat)**2)
        denominator = ((R_eq * cos_lat)**2 + (R_po * sin_lat)**2)
        R_lat = np.divide(numerator,denominator)**0.5
        Area_temp = R_lat**2
        sin_values = np.sin(lat_r + dlat_r/2) - np.sin(lat_r - dlat_r/2)
        Area = np.multiply(Area_temp,sin_values) * dlon_r
        Area_repeated = np.tile(Area,(1,len(lon_r)))
        mask_A = mask_local * Area_repeated
    area = np.sum(mask_A)
    mask_N = mask_A/area
    return mask_local,mask_A,mask_N

def store_aws_keys(endpoint: str="https://archive.podaac.earthdata.nasa.gov/s3credentials"):    
    with requests.get(endpoint, "w") as r:
        accessKeyId, secretAccessKey, sessionToken, expiration = list(r.json().values())

    creds ={}
    creds['AccessKeyId'] = accessKeyId
    creds['SecretAccessKey'] = secretAccessKey
    creds['SessionToken'] = sessionToken
    creds['expiration'] = expiration
    
    return creds


def grace_connection(ShortName,grace_filename):
    #Source: Jinbo Wang (Email: jinbo.wang@jpl.nasa.gov)
    creds = store_aws_keys()
    #print(creds)
    s3 = s3fs.S3FileSystem(
    key = creds['AccessKeyId'],
    secret = creds['SecretAccessKey'],
    token = creds['SessionToken'],
    client_kwargs = {'region_name':'us-west-2'},
    )
    #print(f"\nThe current session token expires at {creds['expiration']}.\n")

# Ask PODAAC for the collection id using the 'short name'
    response = requests.get(
        url='https://cmr.earthdata.nasa.gov/search/collections.umm_json', 
        params={'provider': "POCLOUD",
                'ShortName': ShortName,
                'page_size': 1}
    )

    ummc = response.json()['items'][0]
    ccid = ummc['meta']['concept-id']
    #print(f'collection id: {ccid}')

    ss="podaac-ops-cumulus-protected/%s/*.nc"%ShortName
    GRACE_s3_files = np.sort(s3.glob(ss))
    full_filename=f'podaac-ops-cumulus-protected/TELLUS_GRAC-GRFO_MASCON_CRI_GRID_RL06.1_V3/{grace_filename}'
    dataset = xr.open_dataset(s3.open(full_filename))
        
    return dataset

def read_grace_dataset(ShortName,grace_filename):
    dataset = grace_connection(ShortName,grace_filename)
    
    return dataset


def read_shapefile_singlelayer(shapefile,xdim,ydim):
    # Source: Jack McNelis (email: jack.mcnelis@jpl.nasa.gov)  
    driver = ogr.GetDriverByName('ESRI Shapefile')
    shp = driver.Open(shapefile, 0)
    lyr = shp.GetLayer(0)
    ssrs = lyr.GetSpatialRef()
    wkt = ssrs.ExportToPrettyWkt()
    lyr.SetAttributeFilter("DN = 1")

    for i, feat in enumerate(lyr):
        if feat.GetField("DN") == '1':
            break

    feat = lyr.GetFeature(i)
        
    print(feat.GetField("DN"))  # Confirm the desired feature was selected before breaking the loop.
    geom = feat.GetGeometryRef()
    geojson = geom.ExportToJson()
    list(json.loads(geojson).keys())
    driver = ogr.GetDriverByName("MEMORY")
    featds = driver.CreateDataSource("MemoryDataset")
    newlyr = featds.CreateLayer("1", ssrs, geom_type=ogr.wkbPolygon)
    lyrid = ogr.FieldDefn("DN", ogr.OFTInteger)
    newlyr.CreateField(lyrid)
    lyrdefn = newlyr.GetLayerDefn()
    newfeat = ogr.Feature(lyrdefn)
    newgeom = ogr.CreateGeometryFromJson(geojson)
    newfeat.SetGeometry(newgeom)
    newfeat.SetField("DN", 1)
    newlyr.CreateFeature(newfeat)
    newfeat = None
    gt = (
    -180.0,                  # 0  X minimum (upper-left corner, the origin),
    360/xdim,                # 1  X resolution,
    0.0,                     # 2  X rotation,
    90.0,                    # 3  Y maximum (upper-left corner, the origin),
    0.0,                     # 4  Y rotation,
    -1*(180/ydim),           # 5  Y resolution
    )   
    print(gt)
    mask = gdal.GetDriverByName('MEM').Create(
    '',                   # No filename required for in-memory dataset.
    xdim, ydim,           # Match the dimensions of the GRACE global grid.
    1,                    # Output mask should contain only one band.
    gdal.GDT_Byte,        # Output type should be byte [0,1].
    )
   
    mask.SetGeoTransform(gt)      # Set the affine transform defined above as the mask's geotransform.

    mask.SetProjection(wkt)       # Set the wkt defn extracted from the shp as the target coordinate system.

    band = mask.GetRasterBand(1)  # Select the first and only band in raster mask.

    band.Fill(0)                  # Fill it with zeros.

    band.SetNoDataValue(0)        # Set its nodata value to zero.

    err = gdal.RasterizeLayer(
    mask,
    [1],                      # Set the target band(s); just the one band mask in this case.
    newlyr,                   # Set the source feature layer to rasterize in band 1.
    burn_values = [1],          # Fill the polygon coverage area with 1s.
    )

    mask.FlushCache()             # "Write" changes to the in-memory dataset.

    marr = mask.GetRasterBand(1).ReadAsArray()
    return marr
    
def read_shapefile_multilayers(shapefile,xdim,ydim,layer_name):
    # Source: Jack McNelis (email: jack.mcnelis@jpl.nasa.gov)     
    driver = ogr.GetDriverByName('ESRI Shapefile')
    shp = driver.Open(shapefile, 0)
    lyr = shp.GetLayer()
    ssrs = lyr.GetSpatialRef()
    wkt = ssrs.ExportToPrettyWkt()
    for i, feat in enumerate(lyr):
        if feat.GetField("WMOBB_NAME") == layer_name:
            break
    feat = lyr.GetFeature(i)     
    #print(i)
    #print(feat.GetField("WMOBB_NAME"))
    #Get the feature's geojson representation:
    geom = feat.GetGeometryRef()
    geojson = geom.ExportToJson()
    list(json.loads(geojson).keys())
    driver = ogr.GetDriverByName("MEMORY")

    featds = driver.CreateDataSource("MemoryDataset")

    newlyr = featds.CreateLayer("COLORADO (also COLORADO RIVER)", ssrs, geom_type=ogr.wkbPolygon)

    lyrid = ogr.FieldDefn("ID", ogr.OFTInteger)

    newlyr.CreateField(lyrid)

    lyrdefn = newlyr.GetLayerDefn()

    newfeat = ogr.Feature(lyrdefn)

    newgeom = ogr.CreateGeometryFromJson(geojson)

    newfeat.SetGeometry(newgeom)

    newfeat.SetField("ID", 1)

    newlyr.CreateFeature(newfeat)

    newfeat = None 
    gt = (
    -180.0,                   # 0  X minimum (upper-left corner, the origin),
    360/xdim,                 # 1  X resolution,
    0.0,                      # 2  X rotation,
    90.0,                     # 3  Y maximum (upper-left corner, the origin),
    0.0,                      # 4  Y rotation,
    -1*(180/ydim),            # 5  Y resolution
    )
    
    #print(gt)
    mask = gdal.GetDriverByName('MEM').Create(
    '',                       # No filename required for in-memory dataset.
    xdim, ydim,               # Match the dimensions of the GRACE global grid.
    1,                        # Output mask should contain only one band.
    gdal.GDT_Byte,            # Output type should be byte [0,1].
    )
    
    mask.SetGeoTransform(gt)      # Set the affine transform defined above as the mask's geotransform.

    mask.SetProjection(wkt)       # Set the wkt defn extracted from the shp as the target coordinate system.

    band = mask.GetRasterBand(1)  # Select the first and only band in raster mask.

    band.Fill(0)                  # Fill it with zeros.

    band.SetNoDataValue(0)        # Set its nodata value to zero.

    err = gdal.RasterizeLayer(
    mask,
    [1],                      # Set the target band(s); just the one band mask in this case.
    newlyr,                   # Set the source feature layer to rasterize in band 1.
    burn_values = [1],          # Fill the polygon coverage area with 1s.
    )
    
    mask.FlushCache()             # "Write" changes to the in-memory dataset.

    marr = mask.GetRasterBand(1).ReadAsArray()
    
    # we need to return a bbox of shape
    env = feat.GetGeometryRef().GetEnvelope()
    bbox = [env[0], env[2], env[1], env[3]]
    return marr,bbox

#compute weighted area for this region_mask
def area(lats):
    # Modules:
    from pyproj import Geod
    # Define WGS84 as CRS:
    geod = Geod(ellps='WGS84')
    dx = 1/4.0 #mascon is half deg res so dx =1/4 
    c_area = lambda lat: geod.polygon_area_perimeter(np.r_[-dx,dx,dx,-dx], lat+np.r_[-dx,-dx,dx,dx])[0]
    out = []
    for lat in lats:
        out.append(c_area(lat))
    return np.array(out)
#source: https://github.com/podaac/the-coding-club/blob/main/notebooks/MEaSUREs-SSH-dask.ipynb

#first circshift/roll the mask for longitudes and then flip it to position 0-359 and S-N to match GRACE grid
#users can also adjust GRACE dataset to mask orientation, for this tutorial we keep datasets in GRACE grid format
def shift_to_GRACE_orientation(shift_lon,flip_lat,data_array,indexes_to_shift,axis_no):
    if shift_lon:
        temp_1a = np.roll(data_array, indexes_to_shift, axis =axis_no)
    else:
        temp_1a = copy.copy(data_array)
    if flip_lat:
        reoriented_grid = np.flipud(temp_1a)
    else:
        reoriented_grid = copy.copy(temp_1a)  
    return reoriented_grid

### Convert timemonth to year fraction
#Function toYearFraction(date) here converts time to year fraction. Since some of the datasets contain time as yearfrac, we convert all datasets time variable to consistent units.
def toYearFraction(date): #source: Internet:
    def sinceEpoch(date): # returns seconds since epoch
        return time.mktime(date.timetuple())
    s = sinceEpoch

    year = date.year
    startOfThisYear = dt(year=year, month=1, day=1)
    startOfNextYear = dt(year=year+1, month=1, day=1)

    yearElapsed = s(date) - s(startOfThisYear)
    yearDuration = s(startOfNextYear) - s(startOfThisYear)
    fraction = yearElapsed/yearDuration

    return date.year + fraction
#https://stackoverflow.com/questions/6451655/how-to-convert-python-datetime-dates-to-decimal-float-years

def seamean_connection(ShortName):
    #Source: Jinbo Wang (Email: jinbo.wang@jpl.nasa.gov)
    creds = store_aws_keys()
#print(creds)
    s3 = s3fs.S3FileSystem(
    key = creds['AccessKeyId'],
    secret = creds['SecretAccessKey'],
    token = creds['SessionToken'],
    client_kwargs = {'region_name':'us-west-2'},
    )
    #print(f"\nThe current session token expires at {creds['expiration']}.\n")

# Ask PODAAC for the collection id using the 'short name'
    response = requests.get(
    url = 'https://cmr.earthdata.nasa.gov/search/collections.umm_json', 
    params = {'provider': "POCLOUD",
            'ShortName': ShortName,
            'page_size': 1}
    )

    ummc = response.json()['items'][0]
    ccid = ummc['meta']['concept-id']
    sea_ss = "podaac-ops-cumulus-protected/%s/*.txt"%ShortName
    sea_level_doclist = np.sort(s3.glob(sea_ss))
    sea_level_doc = sea_level_doclist[-1] #read latest file in the cloud for this dataset using last index of array
    sea_level_doc = "s3://" + sea_level_doc # reading txt file using fsspec and hence adding s3 bucket in path. 
    with fsspec.open(sea_level_doc, mode="rb", anon=False, 
            key=creds["AccessKeyId"], secret=creds["SecretAccessKey"], 
            token=creds["SessionToken"]) as f:
        lines = f.readlines()
        all_data = [line.strip() for line in lines] #read all lines 
    return all_data
    

def read_sea_mean_doc(ShortName,local_seamean_filename):
    if ShortName.lower() == "local":
        #with fsspec.open(local_seamean_filename, mode="rb", anon=False) as f:
        f = open(local_seamean_filename, mode="rb")   
        lines = f.readlines()
        all_data = [line.strip() for line in lines] #read all lines    
    else:
        all_data = seamean_connection(ShortName)
    
    cols_name_identifier = b'HDR column description'
    col_names = []
    linenumber_cols_desc_start = 0
    linenumber_cols_desc_end = 0
    linenumber_hdr_ends = 0
    for i in range(0,len(all_data)):
        current_line = all_data[i]
        if current_line==cols_name_identifier:
            linenumber_cols_desc_start = i+1;#next line contains first col desc
            break

    #first col desc is known. now determine total cols and end line for headers
    for i in range(linenumber_cols_desc_start,len(all_data)):
        current_line = all_data[i]
        if current_line==b'HDR':
            linenumber_cols_desc_end=i-1
            break
        
    for i in range(linenumber_cols_desc_end,len(all_data)):
        current_line = all_data[i]
        if current_line==b'HDR Header_End---------------------------------------':
            linenumber_hdr_ends = i
            break

    # Initialize col numbers that signals 'not found'
    GMSL_col_no = -1
    yearfrac_col_no = -1
    
    data = all_data[linenumber_hdr_ends+1:]
    col_names = all_data[linenumber_cols_desc_start:linenumber_cols_desc_end+1]
    for col_counter in range(0,len(col_names)):
        if ('GMSL (Global Isostatic Adjustment (GIA) applied)' in     str(col_names[col_counter])):
            GMSL_col_no = col_counter
        if ('year+fraction' in str(col_names[col_counter])):
            yearfrac_col_no = col_counter
    if GMSL_col_no == -1 or yearfrac_col_no == -1:
        print("Error: Desired columns not found in header. Check file format.")
        return None, None

    sea_level_data = np.loadtxt(all_data,skiprows=linenumber_hdr_ends+1)
    #print(sea_level_data.shape)
    sea_mean_vals = sea_level_data[:,GMSL_col_no]
    sea_time_vec = sea_level_data[:,yearfrac_col_no]
    return sea_mean_vals,sea_time_vec 

#Read the data, convert to desired units (mm) and convert time variable into yearfrac.
def read_thermosteric_data(ShortName,start_date, end_date,local_steric_filename):
    if ShortName.lower() == "local":
        # reading thermosteric data
        with xr.open_dataset(local_steric_filename) as steric_file_nc:
            monthly_steric_xr = steric_file_nc
    else: #read from s3 bucket    
    #Source: Jinbo Wang (Email: jinbo.wang@jpl.nasa.gov)
        creds = store_aws_keys()
        #print(creds)
        s3 = s3fs.S3FileSystem(
        key = creds['AccessKeyId'],
        secret = creds['SecretAccessKey'],
        token = creds['SessionToken'],
        client_kwargs = {'region_name':'us-west-2'},
        )
        #print(f"\nThe current session token expires at {creds['expiration']}.\n")

    # Ask PODAAC for the collection id using the 'short name'
        response = requests.get(
        url = 'https://cmr.earthdata.nasa.gov/search/collections.umm_json', 
        params = {'provider': "POCLOUD",
                'ShortName': ShortName,
                'page_size': 1}
        )

        ummc = response.json()['items'][0]
        ccid = ummc['meta']['concept-id']
        steric_ss = "podaac-ops-cumulus-protected/%s/*.nc"%ShortName
        thermosteric_s3_files = np.sort(s3.glob(steric_ss))
        steric_filename = thermosteric_s3_files[-1] #read latest file in the cloud for this dataset using last index of array
        # reading thermosteric data 
        with xr.open_dataset(s3.open(steric_filename)) as steric_file_nc:
            monthly_steric_xr = steric_file_nc

    #extract this region from GRACE dataset from desired time period. 
    steric_data = monthly_steric_xr["thermosteric_ts"].sel(
    time = slice(start_date, end_date)).data
    steric_data = steric_data*1000 #convert to mm
    steric_time_xr = monthly_steric_xr["time"].sel(time=slice(start_date,end_date)).data
    steric_time = np.empty(steric_time_xr.shape[0])

    for month in range(steric_time_xr.shape[0]):
        steric_ts = pd.to_datetime(steric_time_xr[month])
        steric_time[month] = toYearFraction(steric_ts)
        
    return steric_data,steric_time

#compute mascon regional uncertainty 
def compute_regional_uncertainty(sig_lwe, mask_A, mscID):
    """
    Calculates the intermediate weighted uncertainty components for a specific basin.

    Args:
        sig_lwe (np.array): 3D uncertainty grid (Time, Lat, Lon)
        mask_A (np.array): 2D Area weights grid (Lat, Lon)
        mscID (np.array): 2D Mascon ID grid (Lat, Lon)

    Returns:
        tuple: (sig_lwe_ma, maA)
            sig_lwe_ma (np.array): 2D array (Time, Unique_Mascons) representing 
                                   area-weighted uncertainty per mascon.
            maA (np.array): 1D array representing the total area contribution 
                            of each unique mascon within the basin.
    """
    # 1. Prepare Masks and Boolean indexing
    ma_t = np.transpose(mask_A)
    mscID_t = np.transpose(mscID)
    bool_mask_t = (ma_t != 0)

    # 2. Check shape of arrays are matching
    assert sig_lwe.ndim == 3, "Uncertainty grid must be 3D"
    assert bool_mask_t.shape == (sig_lwe.shape[2], sig_lwe.shape[1]), "Mask/Data mismatch"

    # 3. Align spatial dimensions and extract masked pixels
    sig_lwe_t = sig_lwe.transpose(0, 2, 1)
    new_sig_lwe_t = sig_lwe_t[:, bool_mask_t]

    mscID_bsn = mscID_t[bool_mask_t]
    ma_bsn = ma_t[bool_mask_t]

    # 4. Identify unique Mascons within the basin
    C, ia, ic = np.unique(mscID_bsn, return_index=True, return_inverse=True)

    # 5. Build membership matrix (Matrix of which pixels belong to which Mascon)
    # Using isin across the unique IDs
    bsn_I = np.empty([len(C), len(mscID_bsn)])
    for k in range(len(C)):
        bsn_I[k, :] = np.isin(mscID_bsn, C[k])

    # 6. Calculate Area-sum for each unique mascon portion inside the basin
    maA = np.dot(bsn_I, ma_bsn)

    # 7. Weight the uncertainty by the Mascon area
    # Tile the areas to match the time dimension
    maA_matrix = np.tile(np.transpose(maA), [new_sig_lwe_t.shape[0], 1])

    # We take the uncertainty at the representative index (ia) and weight it
    sig_lwe_ma = np.multiply(new_sig_lwe_t[:, ia], maA_matrix)

    return sig_lwe_ma, maA

#User defined smooth function for non uniform x
def non_uniform_savgol(x, y, window, polynom):
    """
    Applies a Savitzky-Golay filter to y with non-uniform spacing
    as defined in x

    This is based on https://dsp.stackexchange.com/questions/1676/savitzky-golay-smoothing-filter-for-not-equally-spaced-data
    The borders are interpolated like scipy.signal.savgol_filter would do

    Parameters
    ----------
    x : array_like
        List of floats representing the x values of the data
    y : array_like
        List of floats representing the y values. Must have same length
        as x
    window : int (odd)
        Window length of datapoints. Must be odd and smaller than x
    polynom : int
        The order of polynom used. Must be smaller than the window size

    Returns
    -------
    np.array of float
        The smoothed y values
    """
    if len(x) != len(y):
        raise ValueError('"x" and "y" must be of the same size')

    if len(x) < window:
        raise ValueError('The data size must be larger than the window size')

    if type(window) is not int:
        raise TypeError('"window" must be an integer')

    if window % 2 == 0:
        raise ValueError('The "window" must be an odd integer')

    if type(polynom) is not int:
        raise TypeError('"polynom" must be an integer')

    if polynom >= window:
        raise ValueError('"polynom" must be less than "window"')

    half_window = window // 2
    polynom += 1

    # Initialize variables
    A = np.empty((window, polynom))     # Matrix
    tA = np.empty((polynom, window))    # Transposed matrix
    t = np.empty(window)                # Local x variables
    y_smoothed = np.full(len(y), np.nan)

    # Start smoothing
    for i in range(half_window, len(x) - half_window, 1):
        # Center a window of x values on x[i]
        for j in range(0, window, 1):
            t[j] = x[i + j - half_window] - x[i]

        # Create the initial matrix A and its transposed form tA
        for j in range(0, window, 1):
            r = 1.0
            for k in range(0, polynom, 1):
                A[j, k] = r
                tA[k, j] = r
                r *= t[j]

        # Multiply the two matrices
        tAA = np.matmul(tA, A)

        # Invert the product of the matrices
        tAA = np.linalg.inv(tAA)

        # Calculate the pseudoinverse of the design matrix
        coeffs = np.matmul(tAA, tA)

        # Calculate c0 which is also the y value for y[i]
        y_smoothed[i] = 0
        for j in range(0, window, 1):
            y_smoothed[i] += coeffs[0, j] * y[i + j - half_window]

        # If at the end or beginning, store all coefficients for the polynom
        if i == half_window:
            first_coeffs = np.zeros(polynom)
            for j in range(0, window, 1):
                for k in range(polynom):
                    first_coeffs[k] += coeffs[k, j] * y[j]
        elif i == len(x) - half_window - 1:
            last_coeffs = np.zeros(polynom)
            for j in range(0, window, 1):
                for k in range(polynom):
                    last_coeffs[k] += coeffs[k, j] * y[len(y) - window + j]

    # Interpolate the result at the left border
    for i in range(0, half_window, 1):
        y_smoothed[i] = 0
        x_i = 1
        for j in range(0, polynom, 1):
            y_smoothed[i] += first_coeffs[j] * x_i
            x_i *= x[i] - x[half_window]

    # Interpolate the result at the right border
    for i in range(len(x) - half_window, len(x), 1):
        y_smoothed[i] = 0
        x_i = 1
        for j in range(0, polynom, 1):
            y_smoothed[i] += last_coeffs[j] * x_i
            x_i *= x[i] - x[-half_window - 1]

    return y_smoothed
# Source: answer provided by user name 'Not a programmer' on this link 
# https://dsp.stackexchange.com/questions/1676/savitzky-golay-smoothing-filter-for-not-equally-spaced-data

def read_TN12_url(TN12_url, timeout=30):
    """
    Fetch GRACE TN-12 global mean atmospheric/oceanic mass data and parse into a dictionary.

    The TN-12 document provides global mean corrections for GAD product (atmosphere and 
    ocean de-aliasing) which are essential for restoring the ocean mean in sea level studies.

    Parameters
    ----------
    TN12_url : str
        The direct URL to the TN-12 text document (e.g., from PO.DAAC).
    timeout : int
        Timeout in seconds for the network request (default 30).

    Returns
    -------
    dict
        A dictionary containing parsed numerical arrays for 'year', 'mass_over_ocean_NCARmask', 
        and 'mass_over_ocean_JPLmask'.

    Raises
    ------
    RuntimeError
        If the network request fails or data cannot be parsed.
    """

    try:
        # Download the TN-12 document; since file size is small (~100KB), loading into memory is safe
        temp_url_data = urllib.request.urlopen(TN12_url, timeout=timeout).read()
        temp_url_data=temp_url_data.splitlines()

        TN12_header_last_line=b'HDR Header_End--------------------------------------- '
        linenumber_cols_hdr_end=0
        lineCounter=1
        for current_line in temp_url_data:
            if current_line==TN12_header_last_line:
                linenumber_cols_hdr_end=lineCounter
                break
            lineCounter=lineCounter+1
        #print(linenumber_cols_hdr_end)
        TN12_data=np.loadtxt(temp_url_data,skiprows=linenumber_cols_hdr_end)
        TN12_data = {'year':TN12_data[:,0], 'mass_over_ocean_NCARmask':TN12_data[:,1],'mass_over_ocean_JPLmask':TN12_data[:,2]}
        return TN12_data
    except Exception as e:
        raise RuntimeError(f"Failed to fetch or parse TN-12 data: {e}")
        
