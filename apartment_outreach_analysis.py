import pandas as pd


def load_data():
    """Load address and parcel universe data."""
    address_file_path = "data/Parcel_Addresses.csv"
    parcel_universe_file_path = "data/Parcel_Universe_Current_Year_Only.csv"

    address_data = pd.read_csv(address_file_path)
    parcel_universe_data = pd.read_csv(parcel_universe_file_path)
    return address_data, parcel_universe_data


def filter_on_apartments_and_condos(parcel_universe_data):
    """Filter parcel universe data for apartments and condos."""
    return parcel_universe_data[
        (parcel_universe_data['class'].str.startswith('3') &
         ~parcel_universe_data['class'].isin(['300', '301'])) |
        (parcel_universe_data['class'].str.startswith('9') &
         ~parcel_universe_data['class'].isin(['900', '901'])) |
        (parcel_universe_data['class'] == '299')  # condos
    ]


def merge_data(address_data, parcel_universe_data):
    """Merge address data with parcel universe data."""
    merged_data = pd.merge(
        address_data,
        parcel_universe_data,
        on=['pin', 'pin10'],
        how='inner'
    )
    columns_to_keep = [
        'pin', 'class', 'latitude', 'longitude', 'ward_num',
        'chicago_community_area_name', 'property_address',
        'property_city', 'property_state', 'property_zip',
        'mailing_name', 'mailing_address', 'mailing_city',
        'mailing_state', 'mailing_zip'
    ]
    return merged_data[columns_to_keep]


def save_data(data):
    """Save the processed data to a CSV file."""
    output_file_path = "output/local_apartments-condos.csv"
    data.to_csv(output_file_path, index=False)


def main():
    address_data, parcel_universe_data = load_data()
    multi_unit_parcels = filter_on_apartments_and_condos(parcel_universe_data)
    merged_data = merge_data(address_data, multi_unit_parcels)
    save_data(merged_data)


if __name__ == "__main__":
    main()
