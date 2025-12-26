import pandas as pd
import datetime
import re
from request_Script import main
import os
from pathlib import Path
import numpy as np

# Creates the timestamp for current days information
timestamp = datetime.datetime.now().strftime("%Y%m%d")

current_TimeStamp = main()

combined_boards = {}
Path_csv = Path('csv_folder')

# Boards of interest are 8585885825 which is Billing, 8586310441 which is the Census Board, 9023723118 which is Scheduling - Texas, 9023703555 is Incoming Referrals - Texas

board_name = {
    '8585885825': 'Billing',
    '8586310441': 'Active Census',
    '9023723118': 'Scheduling - Texas',
    '9023703555': 'Incoming Referrals - Texas',
    '9893934656': 'Discharged Census'
}

for board_id, patient_data in current_TimeStamp:
    board_id_str = str(board_id)
    
    if board_id_str not in board_name:
        print(f"Unknown board ID {board_id}, skipping...")
        continue
    board_group = board_name[board_id_str]

    df = pd.read_csv(Path_csv/ patient_data)
    combined_boards[board_group] = df

    df.to_csv(Path_csv/ f"{board_id}.csv", index=False)

def Capitalizing_ALL(df):
    df['Item Name'] = (df['Item Name']
        .str.upper()
        .str.replace(' ', '', regex=False)              
        .str.replace(r'(,)?JR$', '', regex=True)        
        .str.replace(r'(G|J)$', '', regex=True) 
        .str.replace(r'(G|J)$', '', regex=True)           
    )
    df = df.rename(columns={'Item Name': 'Patient_Name'})
    return df

def clean_patient_name(name):
    if pd.isnull(name):
        return name
    
    name = str(name)
    name = re.sub(r'^JR[\s,]*', '', name)
    name = name.strip()
    name = re.sub(r'(\d{1,2}/\d{1,2}(/?\d{2,4})?)$', '', name)
    name = name.replace(' ', ',')
    name = name.upper()
    name = name.replace('"', '')
    name = name.replace("'", "")
    # Fixing if there is now 2x , from the above 
    name = name.replace(",,", ",")
    name = re.sub(r',(LVN|DO|RN|NP|FNP)$', '', name)

    if str(name).strip().upper() == 'FRASER,-,SHANNA,RENEE,FRASER':
        return 'SHANNA,FRASER'

    if str(name).strip().upper() == 'GUIDRY,BETHANY':
        return 'BETHANY,GUIDRY'
    
    if str(name).strip().upper() == 'LOPEZ,BRIA':
        return 'BRIA,LOPEZ'
    
    if str(name).strip().upper() == 'BECKEY,-,ARIEL,BECKEY':
        return 'ARIEL,BECKEY'
    
    if str(name).strip().upper() == 'BECKEY,ARIEL':
        return 'ARIEL,BECKEY'
    
    if str(name).strip().upper() == 'TREVINO,PEARL':
        return 'PEARL,TREVINO'
    
    if str(name).strip().upper() == 'PALMER,BRANDON':
        return 'BRANDON,PALMER'
   
    if str(name).strip().upper() == 'ARIEL,BECKEY,BRIA,LOPEZ':
        return 'BRIA,LOPEZ'
    
    if str(name).strip().upper() == 'VILLARREAL,VANESSA':
        return 'VANESSA,VILLARREAL'
    
    if str(name).strip().upper() == 'MARTINEZ,SURELIS':
        return 'SURELIS,MARTINEZ'
    
    return name

# In its current form the billing data == patient data
patient_data = pd.read_csv(Path_csv/ '8585885825.csv')
Census_Active = pd.read_csv(Path_csv/ '8586310441.csv')
Scheduling_Texas_data = pd.read_csv(Path_csv/ '9023723118.csv')
Incoming_Referrals_Texas_data = pd.read_csv(Path_csv/ '9023703555.csv')
Discharged_Census = pd.read_csv(Path_csv/ '9893934656.csv')

Census_data = pd.concat([Census_Active, Discharged_Census])

patient_data = Capitalizing_ALL(patient_data)
Census_data = Capitalizing_ALL(Census_data)
Scheduling_Texas_data = Capitalizing_ALL(Scheduling_Texas_data)
Incoming_Referrals_Texas_data = Capitalizing_ALL(Incoming_Referrals_Texas_data)

def master_set_fcn(patient_data , Census_data, Scheduling_Texas_data, Incoming_Referrals_Texas_data):
    patient_data['color_mkngbtn2'] = patient_data['color_mkngbtn2'].fillna('Not_Processed_Yet')
    left_half_df = Census_data.merge(patient_data, on='Patient_Name', how='left')
    adding_Scheduling_df = left_half_df.merge(Scheduling_Texas_data, on='Patient_Name', how='left')
    Incoming_Referrals_Texas_data = Incoming_Referrals_Texas_data.rename(columns={
        'Item ID': 'Item ID_ref'})
    master_set = adding_Scheduling_df.merge(
        Incoming_Referrals_Texas_data,
        on='Patient_Name',
        how='left'
    )

    # Creating Dummy for division of TrinityMWC
    master_set['conserv_dum'] = (master_set['dropdown_mkrxh1cs'] == 'Active Conservative Patient').astype(int)
    master_set['grafting_dum'] = master_set['dropdown_mkrxh1cs'].isin([
    'Preparing for Skins Subs',
    'Actively Receiving Skin Subs']).astype(int)

    # Adding in dummy for wellmed 
    master_set['Wellmed_dum'] = master_set['dropdown_mkm1tc0g'].str.contains('Wellmed', na=False).astype(int)
    master_set['date4_y'] = pd.to_datetime(master_set['date4_y'], errors='coerce')

    # Trimming to only have wellmed patients then sorting by date (trimming to have only most recent date)
    Wellmed_patients = master_set[master_set['Wellmed_dum'] == 1]
    Wellmed_patients = Wellmed_patients.sort_values(['Patient_Name', 'date4_y'], ascending=[True, False])
    Wellmed_patients = Wellmed_patients.drop_duplicates('Patient_Name', keep='first')

    Wellmed_patients = Wellmed_patients[['Patient_Name','dropdown_mkrxh1cs', 'date4_y']]
    Wellmed_patients = Wellmed_patients.sort_values(['dropdown_mkrxh1cs'], ascending=[False])
    Wellmed_patients.to_csv(Path_csv/ f'Wellmed_patients{timestamp}.csv', index = False)
    
    conditions = [
        master_set['dropdown_mkm1tc0g'].str.contains('Wellmed', na=False, case=False),
        master_set['dropdown_mkm1tc0g'].str.contains(r'\bUHC\b', na=False, case=False),
        master_set['dropdown_mkm1tc0g'].str.contains(r'\bCigna\b', na=False, case=False),
        master_set['dropdown_mkm1tc0g'].str.contains(r'\bBCBS\b', na=False, case=False),
        master_set['dropdown_mkm1tc0g'].str.contains(r'\bHumana\b', na=False, case=False),
        master_set['dropdown_mkm1tc0g'].str.contains(r'\bAetna\b', na=False, case=False),
        master_set['dropdown_mkm1tc0g'].str.contains(r'\bMolina\b', na=False, case=False),
        master_set['dropdown_mkm1tc0g'].str.contains(r'\bMedicare\b', na=False, case=False),
        master_set['dropdown_mkm1tc0g'].str.contains('Devoted', na=False, case=False),
        master_set['dropdown_mkm1tc0g'].str.contains('Humana - Managed by Conviva', na=False, case=False)
        ]

    choices = ['Wellmed', 'UHC', 'Cigna', 'BCBS', 'Humana', 'Aetna', 'Molina', 'Medicare', 'Devoted', 'Humana - managed Conviva']

    master_set['payer_group'] = np.select(conditions, choices, default='Other')

    # Billing Groups processing (making Not Processed and Note Corrected but not Billed)
    
    master_set.loc[(master_set['date_mkrwcv4w'].notna()) & 
        (master_set['color_mkngbtn2'] == 'No Note on File'), 
       'color_mkngbtn2'] = 'Note Corrected but not Billed'
    
    # Removing Merge Errors that create interactions without a date of appointment given 
    master_set = master_set[master_set['date4_y'] != ' '] 

    # Hard Coding the Addresses that cant be found in Map API we are using (These are within 2 miles from patient house)
    address_corrections = {
    "13738 Coyote Hollow, San Antonio, TX, USA": "13185 Talley Road, San Antonio, TX 78253",
    "4823 Scott Carpenter Drive, San Antonio, TX, USA": "4907 Seguin Rd, San Antonio, TX 78219",
    "542 Northeast Interstate 410 Loop, San Antonio, TX, USA": "542 Northeast Loop 410, San Antonio, TX, USA",
    "505 County Road 429 A, Uvalde, TX, USA": "Deer Valley Ranch Road, Uvalde County, TX",
    "6931 Spring Garden Dr, San Antonio, TX, USA": "6931 Spring Garden Street, San Antonio, TX, USA",
    "6931 Spring Garden Dr, San Antonio, TX, USA": "Spring Mont Street, Bexar, Tx",
    "1225 N CENTER ST PO BOX 381, SABINAL, TX 78881-0381": "100 North Center Street, Sabinal, Uvalde County, Tx, 78881",
    "PO BOX 693, LA PRYOR, TX 78872-0693": "237 US-57, La Pryor, TX 78872",
    "9543 Huntress Ln, San Antonio, TX, USA": "25615 Boerne Stage Road , 78255",
    "273 COUNTY ROAD 110, UVALDE, TX 78801-1130": "R 110 , Uvalde County, TX",
    "1767 State Hwy 46, New Braunfels, TX, USA": "1687 State Highway 46 South, New Braunfels, TX",
    "5414 MIDCROWN DR APT 3, SAN ANTONIO, TX 78218-6073": "Quick Wok Chinese Food, Eisenhauer Road, San Antonio, Bexar County, TX",
    "420 Windy Hill, Seguin, TX, USA": "Windy Hill, Guadalupe, Tx",
    "60 Butterfly Ln, Poteet, TX, USA": "Butterfly Lane, Atascosa County, Tx",
    "500 TOMAR DR APT 18B, SAN ANTONIO, TX 78227-3209": "2811 Southwest Loop 410, San Antonio, Tx",
    "1269 W Main St apt 4, Uvalde, TX 78801, USA": "Monterrey Street, Uvalde Tx",
    "3281 LONG PRAIRE RD UNIT 231, FLOWER MOUND, TX 75028-2728": "3281 Sagebrush Drive, Flower Mound, Denton County, Tx",
    "3242 BULL CREEK RD ARBOUR BLDNG, AUSTIN, TX 78731": "4100 Jackson Ave, Austin, TX 78731",
    "2581 Canyon Heights, Spring Branch, TX, USA": "Mount Moriah, Cross Canyon Ranch, Comal County, TX",
    "121 AVE M 107, SAN ANTONIO, TX 78212-1939": "Kenwood North Apartments, 1211 Avenue M, San Antonio, Tx",
    "4100 Jackson Ave apt 134, Austin, TX 78731, USA": "4100 Jackson Ave, Austin, TX 78731",
    "110 Lemonwood Drive, San Antonio, TX, USA": "Covenant Presbyterian Church, Roleto Drive, Castle Hills, Bexar County, Tx",
    "9003 VISTA WEST DR APT 310, SAN ANTONIO, TX 78245-0030": "9003 Vista West Drive, San Antonio, Tx",
    "1007 Avenue South, Hondo, TX, USA": "9th Street, Hondo, Medina County, Tx",
    "701 Co Rd 544, Hondo, TX, USA": "County Road 544, Medina County, Tx",
    "3896 Elaine Circle, Eagle Pass, TX, USA": "Elaine Circle, Deer Run Number 3 Colonia, Maverick County, Tx",
    "4409 GAINES RANCH LOOP APT 521, AUSTIN, TX 78735-6520": "4409 Gaines Ranch Loop, Austin, TX 78735",
    "3007 SE MILITARY DR APT 1802, SAN ANTONIO, TX 78223-4156": "3039 SE Military Dr, San Antonio, TX 78223",
    "229 East Co Road 5718, Natalia, TX, USA": "County Road 5718 East, Medina County, Tx",
    "7547 Rustic Trail, San Antonio, TX, USA": "Rustic Trail, Bexar County, TX, USA",
    "5139 BAUM ST APT 1119, SAN ANTONIO, TX 78233-6502": "Streeter Street, Bexar County, Tx",
    "127 S HOOK ST, LAKE DALLAS, TX 75065-3207": "Chasewood Circle, Hickory Creek, Denton County, Tx",
    "1215 FAIR AVE APT 701, SAN ANTONIO, TX 78223-1465": "1215 FAIR AVE, SAN ANTONIO, TX 78223-1465",
    "630 Solo Street, San Antonio, TX, USA": "Lone Circle, Bexar County, Tx",
    "3500 ORKNEY LOT 26B, SAN ANTONIO, TX 78223-4021": "3500 Orkney , San Antonio, TX 78223",
    "2803 FREDERICKSBURG RD 5105, SAN ANTONIO, TX 78201-4727": "2900 Fredericksburg Road, San Antonio, Tx",
    "200 West Rodriguez Street, Del Rio, TX, USA": "301 Waters Avenue, Del Rio, Tx",
    "470 Crestfield Drive, San Antonio, TX, USA": "Crestfield Street, Bexar County, Tx",
    "15927 Buchel, LaCoste, TX, USA": "Heidelberg Drive, La Coste, Medina County, Tx",
    "219 RIGSBY AVE UNIT 1, SAN ANTONIO, TX 78210-3084": "219 RIGSBY AVE, SAN ANTONIO, TX 78210-3084",
    "587 Byrd Farm Rd, Crystal City, TX, USA": "Byrd Farm Road, Las Colonias, Zavala County, Tx",
    "3803 BARRINGTON ST APT 6A, SAN ANTONIO, TX 78217-4102": "3803 BARRINGTON ST, SAN ANTONIO, TX 78217-4102",
    "7460 KITTY HAWK RD LOT 12, CONVERSE, TX 78109-2456": "7460 KITTY HAWK RD, CONVERSE, TX 78109-2456",
    "437 Sagecrest Drive, San Antonio, TX, USA": "144 Grand Oak Drive, Hollywood Park, Tx",
    "2330 AUSTIN HWY APT 110, SAN ANTONIO, TX 78218-1903": "2330 AUSTIN HWY, SAN ANTONIO, TX 78218-1903",
    "1934 RUTLAND DR UNIT 429, AUSTIN, TX 78758-5418": "1934 RUTLAND DR, AUSTIN, TX 78758-5418",
    "9706 SELBOURNE LN, SAN ANTONIO, TX 78251-4737": "Selborn Lane, Westover Forest, San Antonio, Bexar County, Tx",
    "3735 E COMMERCE ST APT A2, SAN ANTONIO, TX 78219-3812": "3735 E COMMERCE ST, SAN ANTONIO, TX 78219-3812",
    "3907 Mist Flower Drive, Converse, TX, USA": "3907 MistFlower Dr, Bexar County, Tx",
    "1122 S LAREDO ST APT 1010, SAN ANTONIO, TX 78204-3214": "1122 S LAREDO ST, SAN ANTONIO, TX 78204-3214",
    "11641 Anselmo, San Antonio, TX, USA": "Anselmo, Davis Ranch, Bexar County",
    "20500 HUEBNER RD APT 221, SAN ANTONIO, TX 78258-3951": "20500 HUEBNER RD, SAN ANTONIO, TX 78258-3951",
    "428 SGT. Joey Alvarez Ln, Uvalde, TX, USA": "West Modesta Street, Uvalde, Uvalde County, Tx"
    }

    master_set['location_mkv56zmh'] = master_set['location_mkv56zmh'].replace(address_corrections)

    master_set.to_csv(Path_csv/ 'master_set.csv', index=False)
    return master_set

def Patient_Itemized(master_set, timestamp):
    # Setting up local variables for both the cleaning of Patient name and the codes that hold billing information in the master
    master_set['Patient_Name'] = master_set['Patient_Name'].apply(clean_patient_name)
    Charge_codes = ['numeric_mkng945v', 'numeric_mkng1ekp', 'numeric_mkngdap1', 'numeric_mkngbb06',
                'numeric_mknghpcs', 'numeric_mkng9d2s', 'numeric_mkng6bmr', 'numeric_mkqnk160', 'numeric_mkqn9t3r']

    master_set['Total_Billed'] = master_set[Charge_codes].sum(axis=1)
    # Forcing in Approved Perez Number
    overrides = {
            ("PEREZ,ROSALINDA", "2025-05-07"): 470688.80
        }

    master_set['date4_y'] = pd.to_datetime(master_set['date4_y'])

    for (patient, date), new_val in overrides.items():
        mask = (master_set['Patient_Name'] == patient) & (master_set['date4_y'] == pd.to_datetime(date))
        master_set.loc[mask, 'Total_Billed'] = new_val

    latest_status = master_set.sort_values('date4_y', ascending=False).drop_duplicates('Patient_Name')[
        ['Patient_Name', 'dropdown_mkrxh1cs']].set_index('Patient_Name')

    Group_counts = master_set.groupby(['Patient_Name', 'color_mkngbtn2']).size().unstack(fill_value=0)

    billed_sums = master_set.groupby('Patient_Name')['Total_Billed'].sum().to_frame(name='Total_Billed')

    Group_counts = master_set.groupby(['Patient_Name', 'color_mkngbtn2']).size().unstack(fill_value=0)
    billed_sums = master_set.groupby('Patient_Name')['Total_Billed'].sum().to_frame(name='Total_Billed')

    marketer_sum = master_set.groupby('Patient_Name')['multiple_person_mkqagt70'].first().to_frame(name='multiple_person_mkqagt70')
    payer_group_first = master_set.groupby('Patient_Name')['payer_group'].first().to_frame()
    patient_address = master_set.groupby('Patient_Name')['location_mkv56zmh'].first().to_frame()

    marketers_dist = marketer_sum.merge(payer_group_first, left_index=True, right_index=True)
    marketers_dist = marketers_dist.merge(patient_address, left_index = True, right_index = True)

    first_dates = master_set.groupby('Patient_Name')['date4_y'].min()
    last_dates = master_set.groupby('Patient_Name')['date4_y'].max()
    date_diffs = (last_dates - first_dates).dt.days.fillna(0).astype(int).to_frame(name='Days_On_Service')

    collapsed_Patient_Name = Group_counts.merge(billed_sums, left_index=True, right_index=True, how="outer")
    collapsed_Patient_Name = collapsed_Patient_Name.merge(marketers_dist, left_index=True, right_index=True, how="outer")
    collapsed_Patient_Name = collapsed_Patient_Name.merge(latest_status, left_index=True, right_index=True, how="outer")
    collapsed_Patient_Name = collapsed_Patient_Name.merge(date_diffs, left_index=True, right_index=True, how="outer")

    collapsed_Patient_Name['Total_Billed'] = collapsed_Patient_Name['Total_Billed'].fillna(0)
    collapsed_Patient_Name['Days_On_Service'] = collapsed_Patient_Name['Days_On_Service'].fillna(0)


    cols = ['Total_Billed', 'dropdown_mkrxh1cs', 'Days_On_Service' , 'multiple_person_mkqagt70', 'payer_group' , 'location_mkv56zmh'] + [col for col in collapsed_Patient_Name.columns if col not in ['Total_Billed', 'dropdown_mkrxh1cs', 'Days_On_Service' , 'multiple_person_mkqagt70', 'payer_group']]
    collapsed_Patient_Name = collapsed_Patient_Name[cols]

    collapsed_Patient_Name = collapsed_Patient_Name.sort_values(by='Total_Billed', ascending=False)

    collapsed_Patient_Name.to_csv(Path_csv/ f"Patient_Itemized_{timestamp}.csv", index=True)


    discharged_patients = collapsed_Patient_Name[collapsed_Patient_Name['dropdown_mkrxh1cs'] == 'Discharged From Pratice']
    discharged_patients.to_csv(Path_csv / f"Patient_Itemized_Discharged_{timestamp}.csv", index=True)

    non_discharged_patients = collapsed_Patient_Name[collapsed_Patient_Name['dropdown_mkrxh1cs'] != 'Discharged From Pratice']
    non_discharged_patients.to_csv(Path_csv / f"Patient_Itemized_NonDischarged_{timestamp}.csv", index=True)

    collapsed_Patient_Name = collapsed_Patient_Name.drop(columns=['dropdown_mkrxh1cs'])

    # Making subset for patients that have an outstanding note 
    Patient_NoNote = collapsed_Patient_Name[collapsed_Patient_Name['No Note on File'] != 0]
    Patient_NoNote = Patient_NoNote.sort_values(by='No Note on File', ascending=False)
    Patient_NoNote.to_csv(Path_csv/ f"Patient_No_Note_{timestamp}.csv", index=True)

    return collapsed_Patient_Name

def Provider_Itemized(master_set, timestamp):
    Charge_codes = ['numeric_mkng945v', 'numeric_mkng1ekp', 'numeric_mkngdap1', 'numeric_mkngbb06',
                'numeric_mknghpcs', 'numeric_mkng9d2s', 'numeric_mkng6bmr', 'numeric_mkqnk160', 'numeric_mkqn9t3r']

    master_set = master_set.rename(columns={'dropdown_mkngnttn': 'Provider_Name'})
    master_set['Provider_Name'] = master_set['Provider_Name'].astype(str)
    master_set['Provider_Name'] = master_set['Provider_Name'].apply(clean_patient_name)
    master_set['Total_Billed'] = master_set[Charge_codes].sum(axis=1)

    Group_counts = master_set.groupby(['Provider_Name', 'color_mkngbtn2']).size().unstack(fill_value=0)

    billed_sums = master_set.groupby('Provider_Name')['Total_Billed'].sum().to_frame(name='Total_Billed')
    collapsed_Provider_Name = Group_counts.merge(billed_sums, left_index=True, right_index=True)

    # Reorders the df to have total billed after the patient name
    cols = ['Total_Billed'] + [col for col in collapsed_Provider_Name.columns if col != 'Total_Billed']
    collapsed_Provider_Name = collapsed_Provider_Name[cols]

    # Sorts in a desc order based on Total Billed
    collapsed_Provider_Name = collapsed_Provider_Name.sort_values(by='Total_Billed', ascending=False)

    collapsed_Provider_Name.to_csv(Path_csv/ f"Provider_Itemized_{timestamp}.csv", index=True)

    Provider_NoNote = collapsed_Provider_Name[collapsed_Provider_Name['No Note on File'] != 0]
    Provider_NoNote = Provider_NoNote.sort_values(by='No Note on File', ascending=False)
    Provider_NoNote.to_csv(Path_csv/ f"Provider_No_Note_{timestamp}.csv", index=True)

def Marketer_Itemized(collapsed_Patient_Name, master_set, timestamp):
    collapsed_Patient_Name['multiple_person_mkqagt70'] = collapsed_Patient_Name['multiple_person_mkqagt70'].fillna('NA')
    # This is wound size numeric_mknjsfxc
    Incoming_Referrals_Texas = collapsed_Patient_Name.rename(columns={'multiple_person_mkqagt70': 'Marketer_Name'})
    Incoming_Referrals_Texas.to_csv(Path_csv/ f"remove_{timestamp}.csv", index=True)

    #Pulls Wound size back in
    WoundxPatient = master_set[['Patient_Name', 'numeric_mknjsfxc', 'dropdown_mkrxh1cs']].drop_duplicates()
    Incoming_Referrals_Texas = Incoming_Referrals_Texas.merge(WoundxPatient, on = 'Patient_Name', how = 'left')
    Incoming_Referrals_Texas = Incoming_Referrals_Texas.rename(columns={'numeric_mknjsfxc': 'Wound_size_cm'})

    # Collapses back down to just the number of patients by each marketer
    Incoming_Referrals_Texas = Incoming_Referrals_Texas.reset_index()
    Marketer_Sums = Incoming_Referrals_Texas.groupby('Marketer_Name').agg(
    Total_Wound_Size_cm = ('Wound_size_cm', 'sum'),
    Patient_Count = ('Patient_Name', 'nunique')
)
    
    Marketer_Sums.to_csv(Path_csv/ f"Marketer_Sums_{timestamp}.csv", index=True)
    Incoming_Referrals_Texas_Active = Incoming_Referrals_Texas[
    Incoming_Referrals_Texas['dropdown_mkrxh1cs'] != 'Discharged From Pratice']

    Marketer_Sums_Current = Incoming_Referrals_Texas_Active.groupby('Marketer_Name').agg(
    Total_Wound_Size_cm = ('Wound_size_cm', 'sum'),
    Patient_Count = ('Patient_Name', 'nunique')
    )
    
    Marketer_Sums_Current.to_csv(Path_csv/ f"Marketer_Sums_ActivePatients_{timestamp}.csv", index=True)

    Incoming_Referrals_Texas_PendingSkin = Incoming_Referrals_Texas[
    Incoming_Referrals_Texas['dropdown_mkrxh1cs'] == 'Preparing for Skins Subs'
    ]
    Marketer_Sums_PendingSkin = Incoming_Referrals_Texas_PendingSkin.groupby('Marketer_Name').agg(
    Total_Wound_Size_cm = ('Wound_size_cm', 'sum'),
    Patient_Count = ('Patient_Name', 'nunique')
    )
    Marketer_Sums_PendingSkin.to_csv(Path_csv/ f'Marketer_Sums_PendingSkin_{timestamp}.csv', index = True)
    return Incoming_Referrals_Texas

def Bridging_Marketer_Patient(Incoming_Referrals_Texas, collapsed_Patient_Name, timestamp):  
    # Merges the Marketer info from Referrals into the billing set of patient data
    Incoming_trimmed = Incoming_Referrals_Texas[['Patient_Name', 'Marketer_Name']].drop_duplicates()
    Bridge_Marketer = collapsed_Patient_Name.merge(Incoming_trimmed, on = 'Patient_Name', how = 'left')

    Bridge_Marketer.to_csv(Path_csv/ f"Bridged_collapsed_Patient_{timestamp}.csv", index=True)
    Marketer_Billed = Bridge_Marketer.groupby('Marketer_Name')['Total_Billed'].count().to_frame(name='Total_Billed_Marketer')
    return Bridge_Marketer

def Census_Board_Import(Census_data, Referrals_Billing, timestamp):

    Bridge_Census = Census_data.merge(Referrals_Billing, on = 'Patient_Name', how = 'left')
    Bridge_Census['Marketer_Name'] = Bridge_Census['Marketer_Name'].fillna('NA')
    Marketer_WoundSize = (
        Bridge_Census
        .groupby(['Marketer_Name', 'dropdown_mkrxh1cs'])
        .agg(
            Total_WoundArea=('numeric_mknjsfxc', 'sum'),
            Number_of_Patients=('Patient_Name', 'count'),  
            Total_Billed=('Total_Billed', 'sum')
        )
        .reset_index()
        .rename(columns={'dropdown_mkrxh1cs': 'Census_Board_Group'})
    )

    Marketer_WoundSize = Marketer_WoundSize.rename(columns={'dropdown_mkrxh1cs': 'Census_Board_Group'})
    Marketer_WoundSize.to_csv(Path_csv/ f"Total_Billed_Marketer_{timestamp}.csv", index=False)

def final_folder_cleaning(timestamp):
    folder_path = "/home/tym/Trinity_Mobile_WC/csv_folder"
    exceptions = {f"Patient_Itemized_NonDischarged_{timestamp}.csv",f"Patient_Itemized_Discharged_{timestamp}.csv", f"Patient_Itemized_{timestamp}.csv", f"Marketer_Sums_{timestamp}.csv", f"Patient_Itemized_{timestamp}.csv", f'Wellmed_patients{timestamp}.csv', f'Marketer_Sums_PendingSkin_{timestamp}.csv', f"Marketer_Sums_ActivePatients_{timestamp}.csv", f"Provider_Itemized_{timestamp}.csv", 
    f"Overall_{timestamp}.csv", f"Total_Billed_Marketer_{timestamp}.csv", 'removeme.csv', 'master_set.csv'}

    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        
        if filename.endswith(".csv") and filename not in exceptions:
            try:
                os.remove(file_path)
                print(f"Deleted: {filename}")
            except Exception as e:
                print(f"Failed to delete {filename}: {e}")
    
    wipe_secondary_csv_folder()

def wipe_secondary_csv_folder():
    folder_path = Path("/home/tym/Trinity_Mobile_WC")
    for file in folder_path.glob("*.csv"):
        file.unlink()

def __main__():
    master_set = master_set_fcn(patient_data , Census_data, Scheduling_Texas_data, Incoming_Referrals_Texas_data)
    Provider_Itemized(master_set, timestamp)
    collapsed_Patient_Name = Patient_Itemized(master_set, timestamp)
    Incoming_Referrals_Texas = Marketer_Itemized(collapsed_Patient_Name, master_set, timestamp)
    Bridging_Marketer_Patient(Incoming_Referrals_Texas, collapsed_Patient_Name, timestamp)
    Referrals_Billing = Bridging_Marketer_Patient(Incoming_Referrals_Texas, collapsed_Patient_Name, timestamp)
    Census_Board_Import(Census_data, Referrals_Billing, timestamp)
    final_folder_cleaning(timestamp)
    

if __name__ == "__main__":
    __main__()

