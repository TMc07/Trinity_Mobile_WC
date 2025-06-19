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

def Capitalizing_ALL(df):
    df['Item Name'] = (df['Item Name']
        .str.upper()
        .str.replace(' ', '', regex=False)              
        .str.replace(r'(,)?JR$', '', regex=True)        
        .str.replace(r'(G|J)$', '', regex=True) 
        .str.replace(r'JR$', '', regex=True)          
    )
    df = df.rename(columns={'Item Name': 'Patient_Name'})
    return df


def clean_patient_name(name):
    if pd.isnull(name):
        return name
    name = re.sub(r'^JR[\s,]*', '', name)
    name = name.strip()
    name = re.sub(r'(\d{1,2}/\d{1,2}(/?\d{2,4})?)$', '', name)
    name = name.replace(' ', '')
    return name

# In its current form the billing data == patient data
patient_data = pd.read_csv('8585885825.csv')
Census_data = pd.read_csv('8586310441.csv')
Scheduling_Texas_data = pd.read_csv('9023723118.csv')
Incoming_Referrals_Texas_data = pd.read_csv('9023703555.csv')

patient_data = Capitalizing_ALL(patient_data)
Census_data = Capitalizing_ALL(Census_data)
Scheduling_Texas_data = Capitalizing_ALL(Scheduling_Texas_data)
Incoming_Referrals_Texas_data = Capitalizing_ALL(Incoming_Referrals_Texas_data)

def master_set_fcn(patient_data , Census_data, Scheduling_Texas_data, Incoming_Referrals_Texas_data):
    left_half_df = Census_data.merge(patient_data, on='Patient_Name', how='left')
    adding_Scheduling_df = left_half_df.merge(Scheduling_Texas_data, on='Patient_Name', how='left')
    Incoming_Referrals_Texas_data = Incoming_Referrals_Texas_data.rename(columns={
        'Item ID': 'Item ID_ref'})
    master_set = adding_Scheduling_df.merge(
        Incoming_Referrals_Texas_data,
        on='Patient_Name',
        how='left'
    )
    master_set.to_csv('removeme1.csv', index=False)
    return master_set

def Patient_Itemized(master_set, timestamp):
    print(master_set.columns.tolist())
    master_set['Patient_Name'] = master_set['Patient_Name'].apply(clean_patient_name)
    Charge_codes = ['numeric_mkng945v', 'numeric_mkng1ekp', 'numeric_mkngdap1', 'numeric_mkngbb06',
                'numeric_mknghpcs', 'numeric_mkng9d2s', 'numeric_mkng6bmr', 'numeric_mkqnk160', 'numeric_mkqn9t3r']

    master_set['Total_Billed'] = master_set[Charge_codes].sum(axis=1)
    Group_counts = master_set.groupby(['Patient_Name', 'color_mkngbtn2']).size().unstack(fill_value=0)

    billed_sums = master_set.groupby('Patient_Name')['Total_Billed'].sum().to_frame(name='Total_Billed')
    marketers_dist = master_set.groupby('Patient_Name')['multiple_person_mkqagt70'].first().reset_index()
    print(marketers_dist.head())

    Group_counts = master_set.groupby(['Patient_Name', 'color_mkngbtn2']).size().unstack(fill_value=0)
    billed_sums = master_set.groupby('Patient_Name')['Total_Billed'].sum().to_frame(name='Total_Billed')
    marketers_dist = marketers_dist.groupby('Patient_Name')['multiple_person_mkqagt70'].sum().to_frame(name='multiple_person_mkqagt70')

    collapsed_Patient_Name = Group_counts.merge(billed_sums, left_index=True, right_index=True)
    collapsed_Patient_Name = collapsed_Patient_Name.merge(marketers_dist, left_index=True, right_index=True)


    cols = ['Total_Billed'] + [col for col in collapsed_Patient_Name.columns if col != 'Total_Billed']
    collapsed_Patient_Name = collapsed_Patient_Name[cols]

    collapsed_Patient_Name = collapsed_Patient_Name.sort_values(by='Total_Billed', ascending=False)

    collapsed_Patient_Name.to_csv(f"Patient_Itemized_{timestamp}.csv", index=True)

    # Making subset for patients that have an outstanding note 
    Patient_NoNote = collapsed_Patient_Name[collapsed_Patient_Name['No Note on File'] != 0]
    Patient_NoNote = Patient_NoNote.sort_values(by='No Note on File', ascending=False)
    Patient_NoNote.to_csv(f"Patient_No_Note_{timestamp}.csv", index=True)

    return collapsed_Patient_Name

def Provider_Itemized(master_set, timestamp):
    Charge_codes = ['numeric_mkng945v', 'numeric_mkng1ekp', 'numeric_mkngdap1', 'numeric_mkngbb06',
                'numeric_mknghpcs', 'numeric_mkng9d2s', 'numeric_mkng6bmr', 'numeric_mkqnk160', 'numeric_mkqn9t3r']

    master_set = master_set.rename(columns={'dropdown_mkngnttn': 'Provider_Name'})

    master_set['Total_Billed'] = master_set[Charge_codes].sum(axis=1)

    Group_counts = master_set.groupby(['Provider_Name', 'color_mkngbtn2']).size().unstack(fill_value=0)

    billed_sums = master_set.groupby('Provider_Name')['Total_Billed'].sum().to_frame(name='Total_Billed')
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

def Marketer_Itemized(collapsed_Patient_Name, timestamp):
    collapsed_Patient_Name['multiple_person_mkqagt70'] = collapsed_Patient_Name['multiple_person_mkqagt70'].fillna('NA')

    Incoming_Referrals_Texas = collapsed_Patient_Name.rename(columns={'multiple_person_mkqagt70': 'Marketer_Name'})
    print(Incoming_Referrals_Texas.head())

    # Collapses back down to just the number of patients by each marketer
    Incoming_Referrals_Texas = Incoming_Referrals_Texas.reset_index()
    Marketer_Sums = Incoming_Referrals_Texas.groupby('Marketer_Name')['Patient_Name'].count().to_frame(name='Total_Patients')


    Marketer_Sums.to_csv(f"Marketer_Sums_{timestamp}.csv", index=True)
    return Incoming_Referrals_Texas

def Bridging_Marketer_Patient(Incoming_Referrals_Texas, collapsed_Patient_Name, timestamp):  
    # Merges the Marketer info from Referrals into the billing set of patient data
    Incoming_trimmed = Incoming_Referrals_Texas[['Patient_Name', 'Marketer_Name']].drop_duplicates()
    Bridge_Marketer = collapsed_Patient_Name.merge(Incoming_trimmed, on = 'Patient_Name', how = 'left')

    Bridge_Marketer.to_csv(f"Bridged_collapsed_Patient_{timestamp}.csv", index=True)
    Marketer_Billed = Bridge_Marketer.groupby('Marketer_Name')['Total_Billed'].count().to_frame(name='Total_Billed_Marketer')
    Marketer_Billed.to_csv(f"WoundSize_By_Marketer_{timestamp}.csv", index=True)
    return Bridge_Marketer

def Census_Board_Import(Census_data, Referrals_Billing, timestamp):

    Bridge_Census = Census_data.merge(Referrals_Billing, on = 'Patient_Name', how = 'left')
    Bridge_Census['Marketer_Name'] = Bridge_Census['Marketer_Name'].fillna('NA')
    Bridge_Census.to_csv('removeme.csv')
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
    Marketer_WoundSize.to_csv(f"Total_Billed_Marketer_{timestamp}.csv", index=False)

def final_folder_cleaning(timestamp):
    folder_path = "/home/tym/Trinity_Mobile_Export/ty"
    exceptions = {f"Marketer_Sums_{timestamp}.csv", f"Patient_Itemized_{timestamp}.csv", f"Patient_No_Note_{timestamp}.csv",f"Provider_Itemized_{timestamp}.csv",f"Bridged_collapsed_Patient_{timestamp}.csv",f"Overall_{timestamp}.csv", f"Total_Billed_Marketer_{timestamp}.csv", 'removeme.csv'}

    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        
        if filename.endswith(".csv") and filename not in exceptions:
            try:
                os.remove(file_path)
                print(f"Deleted: {filename}")
            except Exception as e:
                print(f"Failed to delete {filename}: {e}")

def __main__():
    master_set = master_set_fcn(patient_data , Census_data, Scheduling_Texas_data, Incoming_Referrals_Texas_data)
    Provider_Itemized(master_set, timestamp)
    collapsed_Patient_Name = Patient_Itemized(master_set, timestamp)
    Incoming_Referrals_Texas = Marketer_Itemized(collapsed_Patient_Name, timestamp)
    Bridging_Marketer_Patient(Incoming_Referrals_Texas, collapsed_Patient_Name, timestamp)
    Referrals_Billing = Bridging_Marketer_Patient(Incoming_Referrals_Texas, collapsed_Patient_Name, timestamp)
    Census_Board_Import(Census_data, Referrals_Billing, timestamp)
    final_folder_cleaning(timestamp)

if __name__ == "__main__":
    __main__()


# dropdown_mkrxh1cs for census group 
