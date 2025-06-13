import pandas as pd
import datetime
import re

patient_data = pd.read_csv('monday_export_20250612_235215.csv')

def clean_patient_name(name): 
    if pd.isnull(name):
        return name
    
    name = name.strip()

    cleaned = re.sub(r'\s+\d{1,2}/\d{1,2}(/?\d{2,4})?$', '', name)
    return cleaned

patient_data['Item Name'] = patient_data['Item Name'].apply(clean_patient_name)

def Patient_Itemized(patient_data):
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

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H")
    collapsed_Patient_Name.to_csv(f"Patient_Itemized_{timestamp}.csv", index=True)

def Provider_Itemized(patient_data):
    Charge_codes = ['numeric_mkng945v', 'numeric_mkng1ekp', 'numeric_mkngdap1', 'numeric_mkngbb06',
                'numeric_mknghpcs', 'numeric_mkng9d2s', 'numeric_mkng6bmr', 'numeric_mkqnk160', 'numeric_mkqn9t3r']

    patient_data = patient_data.rename(columns={'dropdown_mkngnttn': 'Provider_Name'})

    patient_data['Total_Billed'] = patient_data[Charge_codes].sum(axis=1)

    Group_counts = patient_data.groupby(['Provider_Name', 'color_mkngbtn2']).size().unstack(fill_value=0)

    billed_sums = patient_data.groupby('Provider_Name')['Total_Billed'].sum().to_frame(name='Total_Billed')

    collapsed_Provider_Name = Group_counts.merge(billed_sums, left_index=True, right_index=True)

    cols = ['Total_Billed'] + [col for col in collapsed_Provider_Name.columns if col != 'Total_Billed']
    collapsed_Provider_Name = collapsed_Provider_Name[cols]

    collapsed_Provider_Name = collapsed_Provider_Name.sort_values(by='Total_Billed', ascending=False)

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H")
    collapsed_Provider_Name.to_csv(f"Provider_Itemized_{timestamp}.csv", index=True)

def __main__():
    Provider_Itemized(patient_data)
    Patient_Itemized(patient_data)


if __name__ == "__main__":
    __main__()
