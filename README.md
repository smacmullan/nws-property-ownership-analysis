# Chicago Northwest Side Property Ownership Analysis

This repository contains Python scripts to analyze property ownership on the Northwest Side of Chicago (Avondale, Logan Square, and areas covered by the Northwest Preservation Ordinance). The analysis focuses on identifying tenant-occupied properties and large property owners.

## Usage
To use this repository:
1. Run `pip install -r requirements.txt` to install the required packages.
2. Download required data as CSV files and place into the `data` folder.
3. Run analysis scripts to process data into the `output` folder.

Outputted data can be analyzed in your mapping program of choice (QGIS, Kepler.gl, Leaflet, etc.).

There are two available scripts:
* **ownership_analysis.py** - this performs ownership analysis on the property data and produces several files. Ownership is estimated by looking for LLC/corporate owned buildings and buildings where the taxpayer and property address don't match. This is mostly accurate, but address data is not consistently formatted and some LLCs are better at hiding themselves. Produced files include:
    * `local_property_ownership_data.csv` - a list of all property in the area (including commercial buildings) tagged with ownership calculations.
    * `local_rental_housing.csv` - a list of tenant-occupied housing in the area.
    * `local_rental_housing_grouped.csv` - a list of the top landlord addresses in the area, sorted by total housing unit ownership. (Landlord names are not included because they're hidden behind LLCs, but you can usually find these by searching for their address)
* **apartment_outreach_analysis.py** - this generates a list of local apartment and condo buildings `local_apartments-condos.csv` that is useful for general neighborhood outreach.

## Data Sources
This analysis uses the following data sources from the Cook County Open Data Portal:
* [Parcel Universe (Current Year)](https://datacatalog.cookcountyil.gov/Property-Taxation/Assessor-Parcel-Universe-Current-Year-Only-/pabr-t5kh/about_data)
    * PIN, geolocation, property class codes, and more per parcel
    * Filtered on zip_codes or chicago_community_area_num/chicago_community_area_name
* [Parcel Addresses](https://datacatalog.cookcountyil.gov/Property-Taxation/Assessor-Parcel-Addresses/3723-97qp/about_data)
    * Property address and taxpayer mailing addresses
    * Filtered on tax_year and property_zip
* [Commercial Valuation Data](https://datacatalog.cookcountyil.gov/Property-Taxation/Assessor-Commercial-Valuation-Data/csik-bsws/about_data)
    * Apartment unit counts
    * Filtered on township name (Jefferson for northwest side) and tax year. Properties are re-evaluated once every 3 years so you need to include a three year window.
* [Single and Multi-Family Improvement Characteristics](https://datacatalog.cookcountyil.gov/Property-Taxation/Assessor-Single-and-Multi-Family-Improvement-Chara/x54s-btds/about_data)
    * Multi-family home unit counts
    * Filtered on township code (71 for northwest side) and tax year

### Data Notes
* Property class codes are specified in [this PDF](https://prodassets.cookcountyassessor.com/s3fs-public/form_documents/classcode.pdf)
* Condos (299) have individual parcels/PINs per unit
* Many LLCs have the same mailing address that can be used to tied them to the same parent company. This is not always the case as sometimes the LLC will use the property address. [Landlord Mapper](https://landlordmapper.org/chi/home) is a more sophisticated tool for connecting properties to their owners.
* Most addresses have typos. You cannot rely on exact matching to make comparisons
