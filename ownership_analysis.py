from rapidfuzz import fuzz
import re
import usaddress
import pandas as pd

## Load data
multifamily_file_path = "data/Assessor_-_Single_and_Multi-Family_Improvement_Characteristics_20250509.csv"
multifamily_data = pd.read_csv(multifamily_file_path)
apartment_file_path = "data/Assessor_-_Commercial_Valuation_Data_20250508.csv"
apartment_data = pd.read_csv(apartment_file_path)
address_file_path = "data/Assessor_-_Parcel_Addresses_20250430.csv"
address_data = pd.read_csv(address_file_path)
parcel_universe_file_path = "data/Assessor_-_Parcel_Universe__Current_Year_Only__20250430.csv"
parcel_universe_data = pd.read_csv(parcel_universe_file_path)
print("Data loaded successfully")



## Process unit count data

# Remove duplicates, prioritizing rows where 'num_apartments' is not empty
multifamily_data = multifamily_data.sort_values(
    # Prioritize non-empty 'num_apartments'
    by='num_apartments', na_position='last')
multifamily_data = multifamily_data.drop_duplicates(subset='pin', keep='first')

# Drop rows where 'num_apartments' is null and map string values to numbers
multifamily_data = multifamily_data.dropna(subset=['num_apartments'])
apartment_mapping = {'Two': 2, 'Three': 3, 'Four': 4, 'Five': 5, 'Six': 6}
multifamily_data['num_apartments'] = multifamily_data['num_apartments'].map(
    apartment_mapping)

# remove hyphens in apartment pins
apartment_data['keypin'] = apartment_data['keypin'].str.replace(
    '-', '', regex=False)

# remove duplicates, prioritizing rows where 'tot_units' is not empty and most recent year
apartment_data = apartment_data.sort_values(
    by=['tot_units', 'year'],
    ascending=[False, False],
    na_position='last'
)
apartment_data = apartment_data.drop_duplicates(subset='keypin', keep='first')


# Concatenate the unit count dataframes
multifamily_df = multifamily_data[['pin', 'num_apartments']].rename(columns={
    'pin': 'pin',
    'num_apartments': 'total_units'
})
apartment_df = apartment_data[['keypin', 'tot_units']].rename(columns={
    'keypin': 'pin',
    'tot_units': 'total_units'
})
unit_counts = pd.concat([multifamily_df, apartment_df], ignore_index=True)

# clean up the dataframe
unit_counts['pin'] = unit_counts['pin'].astype(str)
unit_counts = unit_counts.dropna(subset=['total_units'])
unit_counts = unit_counts.drop_duplicates(subset='pin', keep='first')
unit_counts['total_units'] = unit_counts['total_units'].astype(int)




## Join parcel/address data

merged_data = pd.merge(
    address_data,
    parcel_universe_data,
    on=['pin', 'pin10'],
    how='inner'
)
merged_data['pin'] = merged_data['pin'].astype(str) # Ensure pin is string type

# Drop unnecessary columns and rename
columns_to_keep = [
    'pin', 'class', 'latitude', 'longitude', 'ward_num',
    'chicago_community_area_name', 'property_address',
    'property_city', 'property_state', 'property_zip',
    'mailing_name', 'mailing_address', 'mailing_city',
    'mailing_state', 'mailing_zip'
]
merged_data = merged_data[columns_to_keep]
merged_data.rename(columns={
    'mailing_name': 'taxpayer_name',
    'mailing_address': 'taxpayer_address',
    'mailing_city': 'taxpayer_city',
    'mailing_state': 'taxpayer_state',
    'mailing_zip': 'taxpayer_zip'
}, inplace=True)
print("Data merged successfully")

# Join unit counts on pin
merged_data = pd.merge(
    merged_data,
    unit_counts,
    on='pin',
    how='left'
)
# Assume NaN 'total_units' values are single-family homes and fill with 1
merged_data['total_units'] = merged_data['total_units'].fillna(1)




## Perform ownership analysis

# LLC matching
merged_data['is_corporate_owned'] = merged_data['taxpayer_name'].str.contains(
    r'\b(?:LLC|INC|TRUST|TRUSTEE|CORP|CO|CORPORATION)\b', case=False, na=False
)


merged_data['is_housing'] = merged_data['class'].str.startswith(
    ('2', '3', '9'))


def is_apartment(class_code: str) -> bool:
    if class_code.startswith('3') and class_code not in ['300', '301']:
        return True
    if class_code.startswith('9') and class_code not in ['900', '901']:
        return True
    return False

merged_data['is_apartment'] = merged_data['class'].apply(is_apartment)


# functions for address parsing and similarity checking
def clean_address(addr: str) -> str:
    if pd.isna(addr):  # Handle NaN values
        return ""
    addr = addr.upper()
    # insert space between number and direction
    addr = re.sub(r'([0-9]+)([NSWE]{1,2})\b', r'\1 \2', addr)
    addr = re.sub(r'[^\w\s]', ' ', addr)  # remove all punctuation
    addr = re.sub(r'\s+', ' ', addr)     # collapse multiple spaces
    return addr.strip()


def parse_with_usaddress(addr: str):
    try:
        parsed = usaddress.tag(addr)[0]
    except usaddress.RepeatedLabelError:
        return {}
    return parsed


def is_owner_occupied(addr1: str, addr2: str, is_corporate_owned=False, threshold: int = 50) -> tuple[bool, float]:

    if is_corporate_owned:
        return False, 0.0

    if addr1 == addr2:
        # if addresses are identical, return true without fuzziness check
        return True, 100.0

    addr1_clean = clean_address(addr1)
    addr2_clean = clean_address(addr2)

    p1 = parse_with_usaddress(addr1_clean)
    p2 = parse_with_usaddress(addr2_clean)

    num1 = p1.get('AddressNumber')
    num2 = p2.get('AddressNumber')

    try:
        if abs(int(num1) - int(num2)) > 10:
            return False, 0.0
    except (TypeError, ValueError):
        return False, 0.0  # Handle missing or non-numeric address numbers

    street1 = f"{num1} {p1.get('StreetName', '')}"
    street2 = f"{num2} {p2.get('StreetName', '')}"

    sim_score = fuzz.token_set_ratio(street1, street2)
    is_match = sim_score >= threshold
    return is_match, sim_score


merged_data[['is_owner_occupied', 'parcel_taxpayer_address_similarity_score']] = merged_data.apply(
    lambda row: is_owner_occupied(
        row['property_address'], row['taxpayer_address'], row['is_corporate_owned']),
    axis=1, result_type='expand'
)
print("Address similarity checks completed")

merged_data['has_tenants'] = merged_data['is_housing'] & (
    merged_data['is_apartment'] | ~merged_data['is_owner_occupied'])

# Save the rental property data (includes all data with ownership flags)
output_file_path = "output/local_property_ownership_data.csv"
merged_data.to_csv(output_file_path, index=False)

# Filter the data where is_housing is True
housing_data = merged_data[(merged_data['is_housing'] == True) & (
    merged_data['is_owner_occupied'] == False)]
housing_data = housing_data.drop(columns=['is_housing', 'is_owner_occupied'])
housing_output_file_path = "output/local_rental_housing.csv"
housing_data.to_csv(housing_output_file_path, index=False)



## Group data by taxpayer_address to find taxpayers with most units
grouped_data = housing_data.groupby(['taxpayer_address', 'taxpayer_city']).agg({
    'total_units': 'sum'}).reset_index()
grouped_data.rename(columns={'total_units': 'total_units_count'}, inplace=True)

grouped_data.sort_values(by='total_units_count',
                         ascending=False, inplace=True)

grouped_output_file_path = "output/local_rental_housing_grouped.csv"
grouped_data.to_csv(
    grouped_output_file_path, index=False)
print("Data saved successfully")
