import pandas as pd

# Load data
address_file_path = "data/Assessor_-_Parcel_Addresses_20250430.csv"
address_data = pd.read_csv(address_file_path)
parcel_universe_file_path = "data/Assessor_-_Parcel_Universe__Current_Year_Only__20250430.csv"
parcel_universe_data = pd.read_csv(parcel_universe_file_path)

# Filter parcel universe on apartments and condos
filtered_parcel_universe = parcel_universe_data[
    (parcel_universe_data['class'].str.startswith('3') & 
     ~parcel_universe_data['class'].isin(['300', '301'])) | 
    (parcel_universe_data['class'].str.startswith('9') & 
     ~parcel_universe_data['class'].isin(['900', '901'])) | 
    (parcel_universe_data['class'] == '299') # condos
]

# Join address data
merged_data = pd.merge(
    address_data,
    filtered_parcel_universe,
    on=['pin', 'pin10'],
    how='inner'
)

# Drop columns
columns_to_keep = [
    'pin', 'class', 'latitude', 'longitude', 'ward_num', 
    'chicago_community_area_name', 'property_address', 
    'property_city', 'property_state', 'property_zip', 
    'mailing_name', 'mailing_address', 'mailing_city', 
    'mailing_state', 'mailing_zip'
]
merged_data = merged_data[columns_to_keep]

# Save the data
output_file_path = "output/local_apartments-condos.csv"
merged_data.to_csv(output_file_path, index=False)
