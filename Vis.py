import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
import datetime
from pathlib import Path

timestamp = datetime.datetime.now().strftime("%Y%m%d")
pngs = Path('pngs')
Path_csv = Path('csv_folder')

Marketer_sums = pd.read_csv(Path_csv/ f'Marketer_Sums_{timestamp}.csv')
# Removing the 0's two Marketers aren't listed on old discharges
Marketer_sums = Marketer_sums[Marketer_sums['Marketer_Name'] != '0']

plt.figure(figsize=(8, 6))
plt.bar(Marketer_sums['Marketer_Name'], Marketer_sums['Total_Wound_Size_cm'], color='skyblue', edgecolor='black')
plt.title('Distribution of Marketers in cm')
plt.xlabel('Marketers')
plt.ylabel('Total wound size in cm')

plt.savefig(pngs/ 'Marketer_distribution_Wounds.png')

Marketer_sums_Active = pd.read_csv(Path_csv/ f'Marketer_Sums_ActivePatients_{timestamp}.csv')

plt.figure(figsize=(8, 6))
plt.bar(Marketer_sums_Active['Marketer_Name'], Marketer_sums_Active['Total_Wound_Size_cm'], color='skyblue', edgecolor='black')
plt.title('Distribution of Marketers in cm')
plt.xlabel('Marketers')
plt.ylabel('Total wound size in cm')
plt.savefig(pngs/ 'Marketer_sums_Active_Wounds.png')

Marketer_sums_Pending_Skin = pd.read_csv(Path_csv/ f'Marketer_Sums_PendingSkin_{timestamp}.csv')

plt.figure(figsize=(8, 6))
plt.bar(Marketer_sums_Pending_Skin['Marketer_Name'], Marketer_sums_Pending_Skin['Total_Wound_Size_cm'], color='skyblue', edgecolor='black')
plt.title('Distribution of Marketers in cm')
plt.xlabel('Marketers')
plt.ylabel('Total wound size in cm')
plt.savefig(pngs/ 'Marketer_sums_Pending_Skin_cm.png')

# Repeating Process for Providers

Provider_sums = pd.read_csv(Path_csv/ f'Provider_Itemized_{timestamp}.csv')

plt.figure(figsize=(10, 6))
plt.bar(Provider_sums['Provider_Name'], Provider_sums['Total_Billed'], color='skyblue', edgecolor='black')
plt.title('Distribution of Providers in Amount Billed')
plt.xlabel('Providers')
plt.ylabel('Amount Billed All Time')
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.savefig(pngs/ 'Providers_by_Billing.png')

plt.figure(figsize=(10, 6))
plt.bar(Provider_sums['Provider_Name'], Provider_sums['No Note on File'], color='skyblue', edgecolor='black')
plt.title('Distribution of Providers in No Note on File')
plt.xlabel('Providers')
plt.ylabel(f'Number of Notes Missing as of {timestamp}')
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.savefig(pngs/ 'Providers_by_NoNote.png')