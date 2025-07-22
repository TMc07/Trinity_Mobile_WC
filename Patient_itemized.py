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
    '8586310441': 'Census',
    '9023723118': 'Scheduling - Texas',
    '9023703555': 'Incoming Referrals - Texas'
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
Census_data = pd.read_csv(Path_csv/ '8586310441.csv')
Scheduling_Texas_data = pd.read_csv(Path_csv/ '9023723118.csv')
Incoming_Referrals_Texas_data = pd.read_csv(Path_csv/ '9023703555.csv')

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

    unique_provider = master_set['dropdown_mkm1tc0g'].unique()
    print(unique_provider)

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

    master_set.to_csv(Path_csv/ 'master_set.csv', index=False)
    return master_set

def Patient_Itemized(master_set, timestamp):
    # Setting up local variables for both the cleaning of Patient name and the codes that hold billing information in the master
    master_set['Patient_Name'] = master_set['Patient_Name'].apply(clean_patient_name)
    Charge_codes = ['numeric_mkng945v', 'numeric_mkng1ekp', 'numeric_mkngdap1', 'numeric_mkngbb06',
                'numeric_mknghpcs', 'numeric_mkng9d2s', 'numeric_mkng6bmr', 'numeric_mkqnk160', 'numeric_mkqn9t3r']

    master_set['Total_Billed'] = master_set[Charge_codes].sum(axis=1)

    latest_status = master_set.sort_values('date4_y', ascending=False).drop_duplicates('Patient_Name')[
        ['Patient_Name', 'dropdown_mkrxh1cs']].set_index('Patient_Name')

    Group_counts = master_set.groupby(['Patient_Name', 'color_mkngbtn2']).size().unstack(fill_value=0)

    billed_sums = master_set.groupby('Patient_Name')['Total_Billed'].sum().to_frame(name='Total_Billed')

    Group_counts = master_set.groupby(['Patient_Name', 'color_mkngbtn2']).size().unstack(fill_value=0)
    billed_sums = master_set.groupby('Patient_Name')['Total_Billed'].sum().to_frame(name='Total_Billed')

    marketer_sum = master_set.groupby('Patient_Name')['multiple_person_mkqagt70'].first().to_frame(name='multiple_person_mkqagt70')
    payer_group_first = master_set.groupby('Patient_Name')['payer_group'].first().to_frame()
    marketers_dist = marketer_sum.merge(payer_group_first, left_index=True, right_index=True)

    first_dates = master_set.groupby('Patient_Name')['date4_y'].min()
    last_dates = master_set.groupby('Patient_Name')['date4_y'].max()
    date_diffs = (last_dates - first_dates).dt.days.fillna(0).astype(int).to_frame(name='Days_On_Service')

    collapsed_Patient_Name = Group_counts.merge(billed_sums, left_index=True, right_index=True)
    collapsed_Patient_Name = collapsed_Patient_Name.merge(marketers_dist, left_index=True, right_index=True)
    collapsed_Patient_Name = collapsed_Patient_Name.merge(latest_status, left_index=True, right_index=True)
    collapsed_Patient_Name = collapsed_Patient_Name.merge(date_diffs, left_index=True, right_index=True)


    cols = ['Total_Billed', 'dropdown_mkrxh1cs', 'Days_On_Service' , 'multiple_person_mkqagt70', 'payer_group'] + [col for col in collapsed_Patient_Name.columns if col not in ['Total_Billed', 'dropdown_mkrxh1cs', 'Days_On_Service' , 'multiple_person_mkqagt70', 'payer_group']]
    collapsed_Patient_Name = collapsed_Patient_Name[cols]

    collapsed_Patient_Name = collapsed_Patient_Name.sort_values(by='Total_Billed', ascending=False)

    collapsed_Patient_Name.to_csv(Path_csv/ f"Patient_Itemized_{timestamp}.csv", index=True)
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
    exceptions = {f"Marketer_Sums_{timestamp}.csv", f"Patient_Itemized_{timestamp}.csv", f'Wellmed_patients{timestamp}.csv', f'Marketer_Sums_PendingSkin_{timestamp}.csv', f"Marketer_Sums_ActivePatients_{timestamp}.csv", f"Provider_Itemized_{timestamp}.csv", 
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

