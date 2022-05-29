import sys, os
import zipfile
from osgeo import gdal
import matplotlib.pyplot as plt
import geopandas as gpd
import glob
import rasterio
import rasterio.mask
from rasterio.plot import show
from unidecode import unidecode
import geojson

#append path of chrs_persiann module
sys.path.append(os.path.abspath(os.path.join('chrs_persiann_util', 'chrs_persiann')))

#module to download PERSIANN data
from chrs import CHRS 

#Edit here the parameters to download PERSIANN data:
startdate = '2020060100' #'yyyymmddHH' format
enddate = '2020063100' #'yyyymmddHH' format
file_format = 'Tif'
timestep = 'monthly' #options: 1hrly, 3hrly, 6hrly, daily, monthly (default), yearly
compression = 'zip'
download_path = os.path.abspath(os.path.join('output'))

#set parameters
params = {
    'start': startdate,
    'end': enddate,
    'mailid': 'test@gmail.com',
    'download_path': download_path,
    'file_format': file_format,
    'timestep': timestep,
    'compression': compression
}

#download PERSIANN data
dl = CHRS()
dl.get_persiann(**params)

#function to retrieve path of tif file inside zip folder
def get_rasterpath():
    """Runs get raster path

    Args:

    Returns:
        the path where raster was saved
    """
    #retrieve last modified file in the folder
    list_of_files = glob.glob('output/*')
    zip_file = max(list_of_files, key=os.path.getmtime)
    print(zip_file)
    #unzip zip file and get first tif file
    z = zipfile.ZipFile(zip_file)
    z.filelist
    rasterfile = z.filelist[0].filename
    raster_path = f'{zip_file}/{rasterfile}'
    return raster_path

#extract selected basin
def get_basin(input_shp, clip_basin):
    """Function to extract selected basin
    Args:
        input_shp (shp): polygon os the basins
        clip_basin (str): name of the basin to be extracted
    Returns:
        extracted basin
    """
    gdf = gpd.read_file(input_shp, encoding="utf8")
    basin = gdf[gdf['DMA_NM']== clip_basin]
    return basin

#Get the coordinates of the geometry to be read by rasterio
def getFeatures(gdf):
    """Function to parse features from GeoDataFrame in such a manner that rasterio wants them"""
    import json
    return [json.loads(gdf.to_json())['features'][0]['geometry']]

#save the clipped raster to disk with
def save_clip(output_clip, out_meta):
    """Function to save the clipped raster and remove if the file already existis

    Args:
        output_clip (str): path to the output clipped raster to be saved 
        out_meta (str): 
    Returns:
        extracted basin
    """
    #if file exist, remove it
    if os.path.exists(output_clip):
        os.remove(output_clip)
    else:
        with rasterio.open(output_clip, "w", **out_meta) as dest:
            dest.write(out_image)

def RemoveZipFiles ():
    """Function to remove the zip files inside output folder
    """
    filesToBeRemoved = []
    filesToBeRemoved.extend(glob.glob("output/*.zip"))
    if len(filesToBeRemoved) > 5:
        for listedFile in filesToBeRemoved:
            os.remove(listedFile)

#retrieve raster path
raster_path = get_rasterpath()
print (raster_path)

#open raster in rasterio read mode
raster_globe = rasterio.open(f'/vsizip/{raster_path}')

#input and output paths
bh_brasil = 'input/bh_brasil.geojson'
output_path = 'output/clip'

#print all hydrological basins of Brazil
with open(bh_brasil, encoding="utf8") as f:
    gj = geojson.load(f)
for i in gj['features']:
    print(i['properties']['DMA_NM'])

#edit here the basin to be clipped:
clip_basin = 'PARANÁ'

#extract the selected basin
selected_basin = get_basin(bh_brasil, clip_basin)

#Get the geometry coordinates of the selected basin.
coords = getFeatures(selected_basin)

#clip the raster with the selected basin
with raster_globe as src:
    out_image, out_transform = rasterio.mask.mask(dataset = src, shapes = coords, crop=True)
    out_meta = src.meta
    
#update the metadata
out_meta.update({
    "driver": "GTiff",
    "height": out_image.shape[1],
    "width": out_image.shape[2],
    "transform": out_transform
    })

#create outputfile with basin name
output_clip = os.path.join(output_path + '_' + unidecode(clip_basin.lower()) + '_' + os.path.basename(raster_path))
print('path of output file:'+ output_clip)

#save the clipped raster in disk        
save_clip(output_clip, out_meta)

#Remove zip files if there are more than 5
RemoveZipFiles()