import os
import pandas as pd
from osgeo import ogr
import pandas as pd
pd.set_option('display.max_columns',None)
import matplotlib.pyplot as plt

# Set environment variables for GDAL/PROJ paths
os.environ['PROJ_LIB'] = 'C:\\Users\\Cheng\\anaconda3\\envs\\code\\Library\\share\\proj'
os.environ['GDAL_DATA'] = 'C:\\Users\\Cheng\\anaconda3\\envs\\code\\Library\\share'

# Get the current and parent directories
cur = os.getcwd()
parent_directory = os.path.dirname(cur)


# Define the path to the GDB file
gdb_path = os.path.join(parent_directory , "HFI2021.gdb")
gdb_path=os.path.join("C:\PeatlandProject", "HFI2021.gdb")

# Open the vector dataset
vector_ds = ogr.Open(gdb_path)
if not vector_ds:
    raise FileNotFoundError(f"Could not open {gdb_path}")

#layer = vector_ds.GetLayerByIndex(1)
#print(f"Layer Name: {layer.GetName()}")
#layer_def = layer.GetLayerDefn()
#field_names = [layer_def.GetFieldDefn(j).GetName() for j in range(layer_def.GetFieldCount())]

data = []
field_names=['FEATURE_TY', 'SOURCE', 'YEAR', 'HFI_ID', 'Shape_Length', 'Shape_Area']
# Iterate through each layer and summarize
for i in range(1, 21):
    layer = vector_ds.GetLayerByIndex(i)
    print(f"Layer Name: {layer.GetName()}, index is {i}")
    layer_def = layer.GetLayerDefn()
    #field_names = [layer_def.GetFieldDefn(j).GetName() for j in range(layer_def.GetFieldCount())]
    for feature in layer:
        data.append([feature.GetField(field) for field in field_names])

    # Optionally, save the summary as a CSV file
    # df.to_csv(f"{layer.GetName()}_summary.csv", index=False)

    # Reset the reading position of the layer
df = pd.DataFrame(data, columns=field_names)
df_serialized = df.to_pickle('summary_peatland.pkl')

agg_data = df.groupby(['FEATURE_TY', 'YEAR'])['Shape_Area'].sum().reset_index()

# Plot each FEATURE_TY across years
plt.figure(figsize=(12, 8))
for feature_type in agg_data['FEATURE_TY'].unique():
    subset = agg_data[agg_data['FEATURE_TY'] == feature_type]
    plt.plot(subset['YEAR'], subset['Shape_Area'], marker='o', label=feature_type)

plt.xlabel('Year')
plt.ylabel('Total Shape Area')
plt.title('Total Shape Area by FEATURE_TY Across Years')
plt.legend()
plt.grid(True)
plt.show()