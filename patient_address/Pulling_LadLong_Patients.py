import pandas as pd
import geopandas as gpd
import requests
import time
from shapely.geometry import Point
import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent

# Creates the timestamp for current days information
timestamp = datetime.datetime.now().strftime("%Y%m%d")

csv_path = ROOT_DIR / "Trinity_Mobile_WC" / "csv_folder" / f"Patient_Itemized_{timestamp}.csv"


# Sets the Username for this API key 
USER_AGENT = "Address_MarketSet_1.0"



# Sets a loop from openstreetmap to sent my address and get the lad and long 
def geocode_address(address):
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        'q': address,
        'format': 'json',
        'addressdetails': 1
    }
    headers = {
        'User-Agent': USER_AGENT
    }
    try:
        response = requests.get(url, params=params, headers=headers)
        time.sleep(1)  # Sets a time delay to prevent overusing 
        response.raise_for_status()  
        data = response.json()
        if data:
            location = data[0]
            return location['lat'], location['lon']
        else:
            return None, None
    except requests.RequestException as e:
        print(f"Error during geocoding request: {e}")
        return None, None

# Getting the Fips Codes
def get_fips_codes(counties_within_radius):
    return counties_within_radius['GEOID'].tolist() 


# Uses the csv I have built to send to the API
def process_addresses_from_csv(input_csv, output_csv, gdf_counties):
    df_addresses = pd.read_csv(input_csv)
    
    results = []

    for index, row in df_addresses.iterrows():
        address = row['location_mkv56zmh']
        
        print(f"Processing address: {address}")

        lat, lon = geocode_address(address)
        if lat is not None and lon is not None:
            results.append({
                'Address': address,
                'latitude': lat,
                'longitude': lon,
            })
        else:
            print(f"Could not geocode address: {address}")
            results.append({
                'Original Address': address,
                'Address': address,
                'latitude': None,
                'longitude': None,
            })

    df_results = pd.DataFrame(results)
    df_results.to_csv(output_csv, index=False)
    print(f"Results saved to {output_csv}")


# Imports county boundires for Geocoding
gdf_counties = gpd.read_file('Patient_Address/cb_2018_us_county_500k/cb_2018_us_county_500k.shp')

# Initialized the first method that calles out to all depend methods
process_addresses_from_csv( ROOT_DIR / "csv_folder" / f"Patient_Itemized_{timestamp}.csv", 'addresses_LatLong_FIPS.csv', gdf_counties)