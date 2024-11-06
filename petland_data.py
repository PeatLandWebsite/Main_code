

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





# Path to the GDB file
gdb_path = "/Volumes/Z Slim/PeatlandMainDataThinkpad/ABMIwetlandInventory.gdb/ABMIwetlandInventory.gdb"

# List all layers in the GDB file
layers = fiona.listlayers(gdb_path)
print("Available layers:", layers)

# Load a specific layer (replace 'your_layer' with a layer from the printed list)
gdf = gpd.read_file(gdb_path, layer='your_layer')

# Display the first few rows and summary statistics
print(gdf.head())
print(gdf.describe())


# List all layers in the GDB file
layers = gpd.io.file.fiona.listlayers(gdb_path)
print("Available layers:", layers)

# Load a specific layer (replace 'your_layer' with a layer from the printed list)
gdf = gpd.read_file(gdb_path, layer='your_layer')

wetland_classes=set()
all_fields=set()

layer = fiona.open(gdb_path, layer='ABMIwetlandInventory')

num_ids = len(set(feature['id'] for feature in layer))


# Iterate through the features and collect WetlandClass values
for feature in layer:
    wetland_class = feature['properties']['WetlandClass']
    if wetland_class:  # Check if the value exists
        wetland_classes.add(wetland_class)







# Close the layer
layer.close()

