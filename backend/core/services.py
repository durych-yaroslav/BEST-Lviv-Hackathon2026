def process_excel_files(land_file, property_file):
    """
    Stub function to process Excel files.
    TODO for the Pandas developer:
    1. Read 'land_file' and 'property_file' using pd.read_excel() or openpyxl.
    2. Merge, clean, and analyze the data to find inconsistencies.
    3. Return a list of dictionaries, where each dictionary represents a single Record.
    """
    
    # HARDCODED FAKE DATA MATCHING README SPECIFICATION FOR NOW
    fake_records = [
        {
            "problems": ["area", "location"],
            "land_data": {
                "cadastral_number": "3222486200:03:001:5001",
                "koatuu": "UA32080000000000000",
                "form_of_ownership": "Private",
                "purpose": "Agricultural",
                "location": "Kyiv region, Bucha district",
                "type_of_agricultural_land": "Arable",
                "area": 2.5,
                "average_monetary_valuation": 150000.0,
                "edrpou_of_land_user": "12345678",
                "land_user": "Company A",
                "share_of_ownership": 1.0,
                "date_of_state_registration_of_ownership": "2026-04-18T10:00:00Z",
                "record_number_of_ownership": "REC-100",
                "authority_that_performed_state_registration_of_ownership": "Local council",
                "type": "Land",
                "subtype": "Field"
            },
            "property_data": {
                "tax_number_of_pp": "87654321",
                "name_of_the_taxpayer": "Company B",
                "type_of_object": "Land plot",
                "address_of_the_object": "Kyiv region, Brovary district",
                "date_of_state_registration_of_ownership": "2026-04-18T10:00:00Z",
                "date_of_state_registration_of_pledge_of_ownership": "2026-04-18T10:00:00Z",
                "total_area": 3.0,
                "type_of_joint_ownership": "Private",
                "share_of_ownership": 1.0
            }
        },
        {
            "problems": ["edrpou_of_land_user"],
            "land_data": {
                "cadastral_number": "1210100000:01:002:0001",
                "koatuu": "UA12345000000000000",
                "form_of_ownership": "State",
                "purpose": "Industrial",
                "location": "Lviv region",
                "type_of_agricultural_land": "None",
                "area": 0.45,
                "average_monetary_valuation": 300000.0,
                "edrpou_of_land_user": "99887766",
                "land_user": "Ivan Franko",
                "share_of_ownership": 0.5,
                "date_of_state_registration_of_ownership": "2026-01-10T10:00:00Z",
                "record_number_of_ownership": "REC-200",
                "authority_that_performed_state_registration_of_ownership": "Ministry",
                "type": "Plot",
                "subtype": "Factory"
            },
            "property_data": {
                "tax_number_of_pp": "11223344",
                "name_of_the_taxpayer": "Ivan Franko",
                "type_of_object": "Industrial zone",
                "address_of_the_object": "Lviv region",
                "date_of_state_registration_of_ownership": "2026-01-10T10:00:00Z",
                "date_of_state_registration_of_pledge_of_ownership": "2026-01-10T10:00:00Z",
                "total_area": 0.45,
                "type_of_joint_ownership": "Shared",
                "share_of_ownership": 0.5
            }
        }
    ]
    
    return fake_records
