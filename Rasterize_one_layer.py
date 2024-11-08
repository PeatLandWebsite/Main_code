import os
import numpy as np
import pandas as pd
from osgeo import gdal, ogr, osr
import geopandas as gpd
import rasterio
from the.features import rasterize
from shapely.geometry import box, mapping

# Set environment variables for GDAL/PROJ paths
os.environ['PROJ_LIB'] = 'C:\\Users\\Cheng\\anaconda3\\envs\\code\\Library\\share\\proj'
os.environ['GDAL_DATA'] = 'C:\\Users\\Cheng\\anaconda3\\envs\\code\\Library\\share'

# Get the current and parent directories
cur = os.getcwd()
parent_directory = os.path.dirname(cur)

# Define the path to the GDB file
gdb_path = os.path.join("C:\\PeatlandProject", "HFI2021.gdb")

# Open the vector dataset
vector_ds = ogr.Open(gdb_path)
if not vector_ds:
    raise FileNotFoundError(f"Could not open {gdb_path}")

# Get the specific layer by index
layer = vector_ds.GetLayerByIndex(9)
layer_def = layer.GetLayerDefn()
field_names = [layer_def.GetFieldDefn(i).GetName() for i in range(layer_def.GetFieldCount())]
print("Field names:", field_names)

# Create a DataFrame from the layer
data = []
for feature in layer:
    data.append([feature.GetField(field) for field in field_names])

data = pd.DataFrame(data, columns=field_names)
print("Sample data:\n", data.head())

# Read the layer as a GeoDataFrame using geopandas
gdf = gpd.read_file(gdb_path, layer=layer.GetName())

# Get extent and set raster resolution
x_min, x_max, y_min, y_max = layer.GetExtent()
pixel_size = 100  # Pixel size in meters
x_res = int((x_max - x_min) / pixel_size)
y_res = int((y_max - y_min) / pixel_size)

# Create the output multiband raster with 4 bands for attributes
output_raster = "MultiBandLayer.tif"
driver = gdal.GetDriverByName("GTiff")
raster_ds = driver.Create(output_raster, x_res, y_res, 4, gdal.GDT_Float32)  # 4 bands for attributes

# Set the geotransform (spatial extent and resolution)
raster_ds.SetGeoTransform((x_min, pixel_size, 0, y_max, 0, -pixel_size))

# Set the coordinate reference system (CRS)
spatial_ref = layer.GetSpatialRef()
raster_ds.SetProjection(spatial_ref.ExportToWkt())

# Initialize empty arrays to store attribute values for each band
max_area_band = np.zeros((y_res, x_res), dtype=np.float32)
attribute_bands = [np.zeros((y_res, x_res), dtype=np.float32) for _ in range(4)]

# Define raster properties
transform = rasterio.transform.from_origin(x_min, y_max, pixel_size, pixel_size)
out_shape = (y_res, x_res)  # Shape of the raster

# Create a temporary in-memory raster for rasterizing (once, outside the loop)
temp_raster = driver.Create('', x_res, y_res, 1, gdal.GDT_Float32)
temp_raster.SetGeoTransform((x_min, pixel_size, 0, y_max, 0, -pixel_size))
temp_raster.SetProjection(spatial_ref.ExportToWkt())
layer.ResetReading()  # Reset the reading cursor to the beginning

# Iterate through each feature in the GeoDataFrame
for _, feature in gdf.iterrows():
    geom = feature.geometry
    if geom is None:
        continue

    # Rasterize the feature geometry into a mask with coverage
    mask = rasterize(
        [(mapping(geom), 1)],
        out_shape=out_shape,
        transform=transform,
        fill=0,
        dtype=np.float32,
        all_touched=True  # Ensures all touched pixels are considered
    )

    # Iterate over each pixel to calculate partial area
    for row in range(y_res):
        for col in range(x_res):
            if mask[row, col] > 0:  # If the pixel is covered
                # Get pixel bounds
                pixel_bounds = box(x_min + col * pixel_size, y_max - (row + 1) * pixel_size,
                                   x_min + (col + 1) * pixel_size, y_max - row * pixel_size)

                # Calculate the intersection area with the feature geometry
                intersection = geom.intersection(pixel_bounds)
                partial_area = intersection.area  # Calculate the overlapping area

                # Update the attribute band with the partial area
                attribute_bands[0][row, col] += partial_area  # Example for the first attribute band

    # Update attribute bands with the feature's attribute values
    for i, attribute_name in enumerate(["FEATURE_TY", "SOURCE", "YEAR", "HFI_ID"]):  # Replace with actual attribute names
        attribute_value = feature[attribute_name]
        if attribute_value is None:
            continue

        attribute_band = attribute_bands[i]
        # Update the band with the attribute value where the current feature's area is larger
        attribute_band[mask > max_area_band] = attribute_value

    # Update the max area band
    max_area_band = np.maximum(max_area_band, mask)

# Save the attribute bands to a raster file using rasterio
with rasterio.open(
    output_raster, 'w',
    driver='GTiff',
    height=out_shape[0],
    width=out_shape[1],
    count=4,  # Number of attribute bands
    dtype=np.float32,
    crs=gdf.crs,
    transform=transform
) as dst:
    for i, attribute_band in enumerate(attribute_bands, start=1):
        dst.write(attribute_band, i)
        dst.set_band_description(i, ["FEATURE_TY", "SOURCE", "YEAR", "HFI_ID"][i - 1])

print("Rasterization completed with precise feature overlaps.")
