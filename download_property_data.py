import os
import requests
import csv
import io
import urllib.parse


DATA_FOLDER = "data"

# Create the data folder if it doesn't exist
os.makedirs(DATA_FOLDER, exist_ok=True)

# Set the APP_TOKEN for authentication (downloads limited to 1000 rows without it)
APP_TOKEN = "iWsUjE9WrjzkkkW2E1zLSfTZZ"
# Note: Please do not abuse this app token. It is provided to streamline use of this script.
# If you would like to set up your own token, create a Cook County developer account (https://datacatalog.cookcountyil.gov/profile/edit/developer_settings)
# and follow the instructions to generate an app token: https://support.socrata.com/hc/en-us/articles/210138558-Generating-App-Tokens-and-API-Keys


def download_csv(url, file_name):
    # Prepare headers with X-App-Token if available
    headers = {}
    if APP_TOKEN:
        headers["X-App-Token"] = APP_TOKEN

    # Download the CSV file
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an error for bad HTTP responses
        csv_content = response.content.decode("utf-8")
    except requests.exceptions.HTTPError as http_err:
        try:
            error_json = response.json()
            print(f"Error code: {error_json.get('code')}")
            print(f"Error message: {error_json.get('message')}")
        except Exception:
            print(f"HTTP error occurred: {http_err}")
            print(f"Response content: {response.text}")
        exit(1)
    except Exception as err:
        print(f"An error occurred: {err}")
        exit(1)

    # Process the CSV to remove unnecessary quotes
    output_rows = []
    reader = csv.reader(io.StringIO(csv_content))
    for row in reader:
        output_rows.append(row)

    # Write the processed CSV to the file
    file_path = os.path.join(DATA_FOLDER, file_name)
    with open(file_path, "w", newline="") as file:
        writer = csv.writer(file, quoting=csv.QUOTE_MINIMAL)
        writer.writerows(output_rows)

    print(f"File downloaded and saved as {file_path}")


# Cook County's Open Data Portal URLs
MULTIFAMILY_QUERY = """
SELECT
  `pin`,
  `class`,
  `township_code`,
  `char_beds` AS num_bedrooms,
  `char_type_resd` AS type_of_residence,
  `char_apts` AS num_apartments,
  `char_ncu`AS num_commercial_units
WHERE
  (`year` = 2025)
  AND caseless_eq(`township_code`, "71")
  AND caseless_ne(`char_use`, "Single-Family")
LIMIT 100000
"""
MULTIFAMILY_DATA_URL = f"https://datacatalog.cookcountyil.gov/resource/x54s-btds.csv?$query={urllib.parse.quote(MULTIFAMILY_QUERY)}"


APARTMENT_QUERY = """
SELECT
  `keypin`,
  `year`,
  `tot_units`
WHERE (`year` > 2021)
  AND caseless_eq(`township`, "Jefferson")
LIMIT 100000
"""
APARTMENT_DATA_URL = f"https://datacatalog.cookcountyil.gov/resource/csik-bsws.csv?$query={urllib.parse.quote(APARTMENT_QUERY)}"


PARCEL_QUERY = """
SELECT
  `pin`,
  `pin10`,
  `class`,
  `lon` AS `longitude`,
  `lat` AS `latitude`,
  `ward_num`,
  `chicago_community_area_num`,
  `chicago_community_area_name`
WHERE caseless_one_of(`zip_code`,"60618", "60639", "60641", "60647")
LIMIT 150000
"""
PARCEL_DATA_URL = f"https://datacatalog.cookcountyil.gov/resource/pabr-t5kh.csv?$query={urllib.parse.quote(PARCEL_QUERY)}"


ADDRESS_QUERY = """
SELECT
  `pin`,
  `pin10`,
  `year` AS `tax_year`,
  `prop_address_full` AS `property_address`,
  `prop_address_city_name` AS `property_city`,
  `prop_address_state` AS `property_state`,
  `prop_address_zipcode_1` AS `property_zip`,
  `mail_address_name` AS `mailing_name`,
  `mail_address_full` AS `mailing_address`,
  `mail_address_city_name` AS `mailing_city`,
  `mail_address_state` AS `mailing_state`,
  `mail_address_zipcode_1` AS `mailing_zip`
WHERE
  `year` IN ("2025")
  AND caseless_one_of(`prop_address_zipcode_1`, "60618", "60639", "60641", "60647")
LIMIT 100000
"""
ADDRESS_DATA_URL = f"https://datacatalog.cookcountyil.gov/resource/3723-97qp.csv?$query={urllib.parse.quote(ADDRESS_QUERY)}"


# Download the CSV files
download_csv(MULTIFAMILY_DATA_URL, "Multi_Family_Improvement_Characteristics.csv")
download_csv(APARTMENT_DATA_URL, "Apartment_Commercial_Valuation_Data.csv")
download_csv(ADDRESS_DATA_URL, "Parcel_Addresses.csv")
download_csv(PARCEL_DATA_URL, "Parcel_Universe_Current_Year_Only.csv")
