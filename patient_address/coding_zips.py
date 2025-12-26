import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import re

def Capitalizing_ALL(df):
    df['FullName'] = (df['FullName']
        .str.upper()
        .str.replace(' ', '', regex=False)                
        .str.replace(r'(G|J)$', '', regex=True) 
        .str.replace(r'(G|J)$', '', regex=True)           
    )
    return df

def clean_patient_name(name):
    if pd.isnull(name):
        return name
    
    name = str(name)
    name = name.strip()
    name = re.sub(r'(\d{1,2}/\d{1,2}(/?\d{2,4})?)$', '', name)
    name = name.replace(' ', ',')
    name = name.upper()
    name = name.replace('"', '')
    name = name.replace("'", "")
    # Fixing if there is now 2x , from the above 
    name = name.replace(",,", ",")
    name = re.sub(r',(LVN|DO|RN|NP|FNP)$', '', name)
    return name

addresses = pd.read_csv("Patient_Address_08_21.csv")
addresses = Capitalizing_ALL(addresses)
addresses['FullName'] = addresses['FullName'].apply(clean_patient_name)

addresses.loc[addresses['FullName'] == "DIAZ,CARLOS", "FullName"] = "DIAZJR,CARLOS"
addresses.loc[addresses['FullName'] == "ESCOBAR,MARIO", "FullName"] = "ESCOBARJR,MARIO"
addresses.loc[addresses['FullName'] == "ALVILLAR,JOHNV", "FullName"] = "ALVILLAR,JOHN"

addresses = addresses[addresses['State'] == 'TX']
addresses['ZipCode'] = addresses["ZipCode"].astype(str).str[:5].str.zfill(5)

zipCounts = addresses['ZipCode'].value_counts().reset_index()
zipCounts.columns = ['ZIP', 'count']

zcta_gdf = gpd.read_file("Patient_Address/tl_2023_us_zcta520/tl_2023_us_zcta520.shp")
states_gdf = gpd.read_file("Patient_Address/tl_2023_us_state.shp")

texas_boundary = states_gdf[states_gdf['STUSPS'] == 'TX']
zcta_gdf = zcta_gdf.to_crs(texas_boundary.crs)
zcta_tx = gpd.overlay(zcta_gdf, texas_boundary, how='intersection')

zcta_tx = zcta_tx.merge(zipCounts, left_on='ZCTA5CE20', right_on='ZIP', how='left')
zcta_tx['count'] = zcta_tx['count'].fillna(0)

fig, ax = plt.subplots(figsize=(10, 10))
zcta_tx.plot(column='count', ax=ax, cmap='OrRd', legend=True,
             edgecolor='black', linewidth=0.2)
ax.set_title("Texas ZIP Code Intensity Map", fontsize=14)
ax.axis('off')
plt.savefig('Zips_By_Intensity.png')


# Trying an interactive map 
import branca.colormap as cm
import folium

# Build color map from min→max count
unique_counts = sorted(zcta_tx['count'].unique())
cmap = cm.StepColormap(
    colors=["#fff5eb", "#fff0e0", "#ffe6cc", "#feddb8", "#fdd3a3",
"#fdc38f", "#fdae6b", "#fd9a56", "#fd8741", "#fd732c",
"#f65d19", "#ef480e", "#e63e0c", "#d8340a", "#c72a08",
"#b62106", "#a01805", "#891004", "#730803", "#5c0000"],
    vmin=min(unique_counts),
    vmax=max(unique_counts),
    index=unique_counts,
    caption='Count per ZIP'
)

m = folium.Map(location=[31, -99], zoom_start=6, tiles="cartodbpositron")

# Add polygons with exact colors per count
folium.GeoJson(
    zcta_tx,
    style_function=lambda feature: {
        'fillColor': cmap(feature['properties']['count']),
        'color': 'black',
        'weight': 0.2,
        'fillOpacity': 0.8,
    },
    tooltip=folium.GeoJsonTooltip(fields=['ZCTA5CE20', 'count'],
                                  aliases=['ZIP:', 'Count:'])
).add_to(m)

cmap.add_to(m)
m.save("texas_zip_map_discrete.html")

## Going to import active census and non active census to them map out their respective distributions
BASE_DIR = "/home/tym/Trinity_Mobile_WC"
ADDR_DIR = f"{BASE_DIR}/Patient_Address"
CSV_DIR = f"{BASE_DIR}/csv_folder"

address_file = f"{ADDR_DIR}/Patient_Address_08_21.csv"
active_file = f"{CSV_DIR}/Patient_Itemized_NonDischarged_20250822.csv"
discharged_file = f"{CSV_DIR}/Patient_Itemized_Discharged_20250822.csv"

addresses = pd.read_csv(address_file)
addresses = pd.read_csv("Patient_Address_08_21.csv")
addresses = Capitalizing_ALL(addresses)
addresses['FullName'] = addresses['FullName'].apply(clean_patient_name)

addresses.loc[addresses['FullName'] == "DIAZ,CARLOS", "FullName"] = "DIAZJR,CARLOS"
addresses.loc[addresses['FullName'] == "ESCOBAR,MARIO", "FullName"] = "ESCOBARJR,MARIO"
addresses.loc[addresses['FullName'] == "ALVILLAR,JOHNV", "FullName"] = "ALVILLAR,JOHN"

addresses = addresses[addresses['State'] == 'TX']
addresses['ZipCode'] = addresses["ZipCode"].astype(str).str[:5].str.zfill(5)

addresses['Patient_Name'] = addresses['FullName']

active_census = pd.read_csv(active_file)
discharged_census = pd.read_csv(discharged_file)

def get_status(name):
    if name in set(active_census['Patient_Name']):
        return "Active"
    elif name in set(discharged_census['Patient_Name']):
        return "Discharged"
    else:
        return "Discharged"

addresses['Status'] = addresses['Patient_Name'].apply(get_status)
addresses.to_csv("Patient_address_Grouping.csv")

zip_counts = addresses.groupby(['ZipCode','Status']).size().reset_index(name='count')
zip_counts = zip_counts.pivot(index='ZipCode', columns='Status', values='count').fillna(0)
zip_counts = zip_counts.reset_index()

zcta_gdf = gpd.read_file("Patient_Address/tl_2023_us_zcta520/tl_2023_us_zcta520.shp")
states_gdf = gpd.read_file("Patient_Address/tl_2023_us_state.shp")

texas_boundary = states_gdf[states_gdf['STUSPS'] == 'TX']
zcta_gdf = zcta_gdf.to_crs(texas_boundary.crs)
zcta_tx = gpd.overlay(zcta_gdf, texas_boundary, how='intersection')

# Merge counts into shapefile
zcta_tx = zcta_tx.merge(zip_counts, left_on='ZCTA5CE20', right_on='ZipCode', how='left')
for col in ['Active','Discharged','Other']:
    if col not in zcta_tx:
        zcta_tx[col] = 0
zcta_tx[['Active','Discharged','Other']] = zcta_tx[['Active','Discharged','Other']].fillna(0)

export_df = zip_counts.copy()
for col in ['Active','Discharged','Other']:
    if col not in export_df:
        export_df[col] = 0
export_df[['Active','Discharged','Other']] = export_df[['Active','Discharged','Other']].fillna(0)

export_df.to_csv("Dum_Patient_Reports.csv", index=False)

fig, ax = plt.subplots(figsize=(10, 10))
zcta_tx.plot(column='Active', ax=ax, cmap='Greens', legend=True,
             edgecolor='black', linewidth=0.2)
ax.set_title("Active Census Patients by ZIP", fontsize=14)
ax.axis('off')
plt.savefig(f"{ADDR_DIR}/Active_Census_Zips.png")

m = folium.Map(location=[31, -99], zoom_start=6, tiles="cartodbpositron")

def style_function(feature):
    active = feature['properties']['Active']
    discharged = feature['properties']['Discharged']
    if active > 0:
        return {'fillColor': 'green', 'color': 'black', 'weight': 0.3, 'fillOpacity': 0.7}
    elif discharged > 0:
        return {'fillColor': 'red', 'color': 'black', 'weight': 0.2, 'fillOpacity': 0.5}
    else:
        return {'fillColor': 'lightgray', 'color': 'black', 'weight': 0.1, 'fillOpacity': 0.2}

folium.GeoJson(
    zcta_tx,
    style_function=style_function,
    tooltip=folium.GeoJsonTooltip(
        fields=['ZCTA5CE20','Active','Discharged'],
        aliases=['ZIP:','Active Patients:','Discharged Patients:'])
).add_to(m)

m.save(f"{ADDR_DIR}/patients_active_vs_discharged.html")