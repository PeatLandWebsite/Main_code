

import os
os.environ['PROJ_LIB'] = 'C:\\Users\\Cheng\\anaconda3\\envs\\code\\Library\\share\\proj'
os.environ['GDAL_DATA'] = 'C:\\Users\\Cheng\\anaconda3\\envs\code\\Library\\share'

import gdal
from osgeo import gdal, ogr, osr


# Get the current and parent directories
cur = os.getcwd()
parent_directory = os.path.dirname(cur)

# Define the path to the GDB file
gdb_path = os.path.join(parent_directory, "HFI2021.gdb")



# Open the vector dataset
vector_ds = ogr.Open(gdb_path)

# Display all layer names
for i in range(vector_ds.GetLayerCount()):
    layer = vector_ds.GetLayerByIndex(i)
    print(layer.GetName())

# Specify the layer name you want to work with
layer_name = "o01_Reservoirs_HFI_2021"  # Replace with your layer name
layer = vector_ds.GetLayerByName(layer_name)

# Check the Spatial Reference System (SRS)
spatial_ref = layer.GetSpatialRef()
print(spatial_ref.ExportToWkt())

# Get the units of the layer
units = spatial_ref.GetLinearUnitsName()
print(f"Units: {units}")

# Get the extent of the vector layer
x_min, x_max, y_min, y_max = layer.GetExtent()

# Set raster resolution
pixel_size = 100  # Define the pixel size in the appropriate units (meters)
x_res = int((x_max - x_min) / pixel_size)
y_res = int((y_max - y_min) / pixel_size)

# Get the number of attributes in the layer
layer_defn = layer.GetLayerDefn()
num_attributes = layer_defn.GetFieldCount()
print(f"Number of attributes: {num_attributes}")

# Display all attribute names
for i in range(layer_defn.GetFieldCount()):
    field_defn = layer_defn.GetFieldDefn(i)
    print(f"Attribute {i + 1}: {field_defn.GetName()}")

# Create the output multiband raster with 4 bands (for the 4 selected attributes)
output_raster = "output_largest_area_multiband_raster.tif"
driver = gdal.GetDriverByName("GTiff")
raster_ds = driver.Create(output_raster, x_res, y_res, 4, gdal.GDT_Float32)  # 4 bands for attributes

# Set the geotransform (spatial extent and resolution)
raster_ds.SetGeoTransform((x_min, pixel_size, 0, y_max, 0, -pixel_size))

# Set the coordinate reference system (CRS)
raster_ds.SetProjection(spatial_ref.ExportToWkt())

# Initialize empty arrays to store maximum area and corresponding attribute values
max_area_band = np.zeros((y_res, x_res), dtype=np.float32)  # To track max areas
attribute_bands = [np.zeros((y_res, x_res), dtype=np.float32) for _ in range(4)]  # 4 bands for 4 attributes

# Iterate over all features, calculating area and updating the bands
for feature in layer:
    geom = feature.GetGeometryRef()
    area = geom.GetArea()  # Get the feature's area

    # Rasterize the feature's geometry into a temporary single-band raster
    temp_raster = driver.Create('', x_res, y_res, 1, gdal.GDT_Float32)
    temp_raster.SetGeoTransform((x_min, pixel_size, 0, y_max, 0, -pixel_size))
    temp_raster.SetProjection(spatial_ref.ExportToWkt())

    # Burn the feature's area into the temporary raster
    gdal.RasterizeLayer(temp_raster, [1], layer, burn_values=[area])

    # Read the rasterized area into an array
    temp_array = temp_raster.ReadAsArray()

    # Update the attribute bands where the current feature has a larger area
    for i, attribute_name in enumerate(["FEATURE_TY", "SOURCE", "YEAR", "HFI_ID"]):  # Replace with your attribute names
        attribute_value = feature.GetField(attribute_name)  # Get attribute value
        attribute_band = attribute_bands[i]

        # Update the band with the attribute value where the current feature's area is larger
        attribute_band[temp_array > max_area_band] = attribute_value

    # Update the max area band
    max_area_band = np.maximum(max_area_band, temp_array)

# Write the attribute bands to the raster dataset
for i, attribute_band in enumerate(attribute_bands):
    out_band = raster_ds.GetRasterBand(i + 1)  # Bands are 1-indexed in GDAL
    out_band.WriteArray(attribute_band)

# Close the raster dataset
raster_ds = None
vector_ds = None
