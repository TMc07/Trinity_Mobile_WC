import pandas as pd
import datetime
import re
from request_Script import main
import os

# Creates the timestamp for current days information
timestamp = datetime.datetime.now().strftime("%Y%m%d")

current_TimeStamp = main()

combined_boards = {}

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

    df = pd.read_csv(patient_data)
    combined_boards[board_group] = df

    df.to_csv(f"{board_id}.csv", index=False)
    print(f"Saved cleaned CSV for board '{board_id}' as {board_id}.csv")

# In its current form the billing data == patient data
patient_data = pd.read_csv('8585885825.csv')
Census_data = pd.read_csv('8586310441.csv')
Scheduling_Texas_data = pd.read_csv('9023723118.csv')
Incoming_Referrals_Texas_data = pd.read_csv('9023703555.csv')

def clean_patient_name(name): 
    if pd.isnull(name):
        return name
    
    name = name.strip()

    cleaned = re.sub(r'\s+\d{1,2}/\d{1,2}(/?\d{2,4})?$', '', name)
    return cleaned

patient_data['Item Name'] = patient_data['Item Name'].apply(clean_patient_name)

def Patient_Itemized(patient_data, timestamp):
    Charge_codes = ['numeric_mkng945v', 'numeric_mkng1ekp', 'numeric_mkngdap1', 'numeric_mkngbb06',
                'numeric_mknghpcs', 'numeric_mkng9d2s', 'numeric_mkng6bmr', 'numeric_mkqnk160', 'numeric_mkqn9t3r']

    patient_data = patient_data.rename(columns={'Item Name': 'Patient_Name'})

    patient_data['Total_Billed'] = patient_data[Charge_codes].sum(axis=1)

    Group_counts = patient_data.groupby(['Patient_Name', 'color_mkngbtn2']).size().unstack(fill_value=0)

    billed_sums = patient_data.groupby('Patient_Name')['Total_Billed'].sum().to_frame(name='Total_Billed')

    collapsed_Patient_Name = Group_counts.merge(billed_sums, left_index=True, right_index=True)

    cols = ['Total_Billed'] + [col for col in collapsed_Patient_Name.columns if col != 'Total_Billed']
    collapsed_Patient_Name = collapsed_Patient_Name[cols]

    collapsed_Patient_Name = collapsed_Patient_Name.sort_values(by='Total_Billed', ascending=False)

    collapsed_Patient_Name.to_csv(f"Patient_Itemized_{timestamp}.csv", index=True)

    # Making subset for patients that have an outstanding note 
    Patient_NoNote = collapsed_Patient_Name[collapsed_Patient_Name['No Note on File'] != 0]
    Patient_NoNote = Patient_NoNote.sort_values(by='No Note on File', ascending=False)
    Patient_NoNote.to_csv(f"Patient_No_Note_{timestamp}.csv", index=True)
    return collapsed_Patient_Name

def Provider_Itemized(patient_data, timestamp):
    Charge_codes = ['numeric_mkng945v', 'numeric_mkng1ekp', 'numeric_mkngdap1', 'numeric_mkngbb06',
                'numeric_mknghpcs', 'numeric_mkng9d2s', 'numeric_mkng6bmr', 'numeric_mkqnk160', 'numeric_mkqn9t3r']

    patient_data = patient_data.rename(columns={'dropdown_mkngnttn': 'Provider_Name'})

    patient_data['Total_Billed'] = patient_data[Charge_codes].sum(axis=1)

    Group_counts = patient_data.groupby(['Provider_Name', 'color_mkngbtn2']).size().unstack(fill_value=0)

    billed_sums = patient_data.groupby('Provider_Name')['Total_Billed'].sum().to_frame(name='Total_Billed')


    collapsed_Provider_Name = Group_counts.merge(billed_sums, left_index=True, right_index=True)

    # Reorders the df to have total billed after the patient name
    cols = ['Total_Billed'] + [col for col in collapsed_Provider_Name.columns if col != 'Total_Billed']
    collapsed_Provider_Name = collapsed_Provider_Name[cols]

    # Sorts in a desc order based on Total Billed
    collapsed_Provider_Name = collapsed_Provider_Name.sort_values(by='Total_Billed', ascending=False)

    collapsed_Provider_Name.to_csv(f"Provider_Itemized_{timestamp}.csv", index=True)

    Provider_NoNote = collapsed_Provider_Name[collapsed_Provider_Name['No Note on File'] != 0]
    Provider_NoNote = Provider_NoNote.sort_values(by='No Note on File', ascending=False)
    Provider_NoNote.to_csv(f"Provider_No_Note_{timestamp}.csv", index=True)

def Marketer_Itemized(Incoming_Referrals_Texas_data, timestamp):
    Incoming_Referrals_Texas = Capitalizing_ALL(Incoming_Referrals_Texas_data)
    Incoming_Referrals_Texas['multiple_person_mkqagt70'] = Incoming_Referrals_Texas['multiple_person_mkqagt70'].fillna('NA')

    Incoming_Referrals_Texas = Incoming_Referrals_Texas.rename(columns={'multiple_person_mkqagt70': 'Marketer_Name'})

    # Collapses back down to just the number of patients by each marketer
    Marketer_Sums = Incoming_Referrals_Texas.groupby('Marketer_Name')['Item Name'].count().to_frame(name='Total_Patients')

    Marketer_Sums.to_csv(f"Marketer_Sums_{timestamp}.csv", index=True)
    Incoming_Referrals_Texas = Incoming_Referrals_Texas.rename(columns={'Item Name': 'Patient_Name'})
    return Incoming_Referrals_Texas

def Capitalizing_ALL(Incoming_Referrals_Texas_data):
    Incoming_Referrals_Texas_data['Item Name'] = Incoming_Referrals_Texas_data['Item Name'].str.upper().str.replace(' ', '', regex=False)
    return Incoming_Referrals_Texas_data

def Bridging_Marketer_Patient(Incoming_Referrals_Texas, collapsed_Patient_Name, timestamp):  
    # Merges the Marketer info from Referrals into the billing set of patient data
    Bridge_df = collapsed_Patient_Name.merge(Incoming_Referrals_Texas, on = 'Patient_Name', how = 'left')

    Bridge_df.to_csv(f"Bridged_collapsed_Patient_{timestamp}.csv", index=True)
    Marketer_Billed = Bridge_df.groupby('Marketer_Name')['Total_Billed'].count().to_frame(name='Total_Billed')
    Marketer_Billed.to_csv(f"WoundSize_By_Marketer_{timestamp}.csv", index=True)
    return Bridge_df

def Census_Board_Import(Census_data, Referrals_Billing, timestamp):
    Census_data= Capitalizing_ALL(Census_data)

    Census_data = Census_data.rename(columns={'Item Name': 'Patient_Name'})
    Bridge_df = Census_data.merge(Referrals_Billing, on = 'Patient_Name', how = 'left')
    Bridge_df.to_csv(f"Overall_{timestamp}.csv", index=True)
    Marketer_WoundSize = Bridge_df.groupby('Marketer_Name')['numeric_mknjsfxc'].sum().to_frame(name='Total_WoundArea')
    
    Marketer_WoundSize.to_csv(f"Total_Billed_Marketer_{timestamp}.csv", index=True)

def final_folder_cleaning(timestamp):
    folder_path = "/home/tym/Trinity_Mobile_Export/ty"
    exceptions = {f"Marketer_Sums_{timestamp}.csv", f"Patient_Itemized_{timestamp}.csv", f"Patient_No_Note_{timestamp}.csv",f"Provider_Itemized_{timestamp}.csv",f"Bridged_collapsed_Patient_{timestamp}.csv",f"Overall_{timestamp}.csv"}

    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        
        if filename.endswith(".csv") and filename not in exceptions:
            try:
                os.remove(file_path)
                print(f"Deleted: {filename}")
            except Exception as e:
                print(f"Failed to delete {filename}: {e}")

def __main__():
    Provider_Itemized(patient_data, timestamp)
    collapsed_Patient_Name = Patient_Itemized(patient_data, timestamp)
    Incoming_Referrals_Texas = Marketer_Itemized(Incoming_Referrals_Texas_data, timestamp)
    Bridging_Marketer_Patient(Incoming_Referrals_Texas, collapsed_Patient_Name, timestamp)
    Referrals_Billing = Bridging_Marketer_Patient(Incoming_Referrals_Texas, collapsed_Patient_Name, timestamp)
    Census_Board_Import(Census_data, Referrals_Billing, timestamp)
    final_folder_cleaning(timestamp)

if __name__ == "__main__":
    __main__()
