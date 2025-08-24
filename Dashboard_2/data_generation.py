import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta

# --- Configuration for Data Generation ---

# 1. Bihar Districts and Representative Blocks
# Using all 38 districts of Bihar. For blocks, using a generic list per district.
# You can replace "Block A", "Block B", etc., with actual block names if needed.
districts_bihar = [
    "Araria", "Arwal", "Aurangabad", "Banka", "Begusarai", "Bhagalpur",
    "Bhojpur", "Buxar", "Darbhanga", "East Champaran", "Gaya", "Gopalganj",
    "Jamui", "Jehanabad", "Kaimur", "Katihar", "Khagaria", "Kishanganj",
    "Lakhisarai", "Madhepura", "Madhubani", "Munger", "Muzaffarpur",
    "Nalanda", "Nawada", "Patna", "Purnia", "Rohtas", "Saharsa",
    "Samastipur", "Saran", "Sheikhpura", "Sheohar", "Sitamarhi", "Siwan",
    "Supaul", "Vaishali", "West Champaran"
]
blocks_per_district = ["Block A", "Block B", "Block C", "Block D", "Block E"]

bihar_geo_data = {district: blocks_per_district for district in districts_bihar}

# 2. Incident Types (from the provided dashboard images)
incident_types = [
    "Lightning", "Rail Accident", "Road Accident", "Snakebite",
    "Strong Wind", "Airplane Accident", "Boat Tragedy", "Drowning",
    "Earthquake", "Fire", "Others"
]
# Optional: Weights for incident types to make some more common
# These weights roughly sum to 1. Adjust as needed.
incident_type_weights = [
    0.15,  # Lightning
    0.02,  # Rail Accident
    0.30,  # Road Accident
    0.10,  # Snakebite
    0.08,  # Strong Wind
    0.005, # Airplane Accident
    0.04,  # Boat Tragedy
    0.10,  # Drowning
    0.005, # Earthquake
    0.12,  # Fire
    0.08   # Others
]


# 3. Entry Types
entry_types = ["System Auto-Report", "Manual Field Report", "Citizen Alert", "Agency Verified"]

# 4. Date Range for Sample Data
# Covering a period that would include the dates shown in your images (e.g., 01/04/2025 to 05/06/2025)
start_date_param = datetime(2023, 1, 1)
end_date_param = datetime(2025, 12, 31)
total_days_param = (end_date_param - start_date_param).days

# 5. Number of Sample Incident Records to Generate
num_records_to_generate = 7000  # Adjust as needed for a richer dataset

# --- Data Generation Logic ---
data_list = []

for i in range(num_records_to_generate):
    # Random date for the incident
    random_day_offset = random.randint(0, total_days_param)
    incident_date = start_date_param + timedelta(days=random_day_offset)

    # Randomly select district and one of its blocks
    selected_district = random.choice(list(bihar_geo_data.keys()))
    selected_block = random.choice(bihar_geo_data[selected_district])

    # Randomly select incident type (with weighting)
    selected_incident_type = random.choices(incident_types, weights=incident_type_weights, k=1)[0]

    # Randomly generate number of deaths
    # Higher chance of 0 deaths, occasional 1 or more.
    if random.random() < 0.75:  # 75% chance of 0 deaths
        deaths = 0
    else:
        deaths = random.randint(1, 3)
        if selected_incident_type in ["Road Accident", "Fire", "Boat Tragedy", "Lightning", "Drowning"] and random.random() < 0.1:
            deaths = random.randint(1, 7) # Higher potential for some incidents
        if selected_incident_type == "Airplane Accident" and random.random() < 0.5 : # Rare, but potentially high
             deaths = random.randint(5, 50) if random.random() < 0.1 else random.randint(0,5) # Small chance of high impact
        if selected_incident_type == "Earthquake" and random.random() < 0.3 : # Rare, but potentially high
             deaths = random.randint(2, 30) if random.random() < 0.1 else random.randint(0,5)


    # Randomly generate number of injured
    # Higher chance of 0 or few injuries, can be independent of deaths.
    if random.random() < 0.5: # 50% chance of 0 injured
        injured = 0
    else:
        injured = random.randint(1, 5)
        if selected_incident_type in ["Road Accident", "Fire", "Strong Wind", "Boat Tragedy"] and random.random() < 0.2:
            injured = random.randint(1, 15) # Higher potential for some incidents
        if deaths > 0 and random.random() < 0.7: # If there are deaths, more likely to be injured people too
            injured += random.randint(deaths, deaths * 3)
        if selected_incident_type == "Airplane Accident" and random.random() < 0.5:
            injured = random.randint(10, 100) if random.random() < 0.1 else random.randint(0,10)
        if selected_incident_type == "Earthquake" and random.random() < 0.3:
            injured = random.randint(5, 50) if random.random() < 0.1 else random.randint(0,10)


    # Randomly select entry type
    selected_entry_type = random.choice(entry_types)

    data_list.append({
        "date": incident_date.strftime('%Y-%m-%d'),
        "district": selected_district,
        "block": selected_block,
        "incident_type": selected_incident_type,
        "deaths": deaths,
        "injured": injured,
        "entry_type": selected_entry_type
    })

# Create DataFrame
df_sample_eoc = pd.DataFrame(data_list)

# Sort data by date for better chronological order (optional)
df_sample_eoc['date'] = pd.to_datetime(df_sample_eoc['date'])
df_sample_eoc = df_sample_eoc.sort_values(by=["date", "district", "block"]).reset_index(drop=True)

# Save to CSV
output_filename = 'eoc_sample_data.csv'
df_sample_eoc.to_csv(output_filename, index=False)

print(f"Sample EOC data generated successfully and saved to '{output_filename}'")
print(f"Generated {len(df_sample_eoc)} records.")
print("\nFirst 5 rows of the generated data:")
print(df_sample_eoc.head())