def process_excel_files(land_file, property_file):
    """
    Stub function to process Excel files.
    TODO for the Pandas developer:
    1. Read 'land_file' and 'property_file' using pd.read_excel() or openpyxl.
    2. Merge, clean, and analyze the data to find inconsistencies.
    3. Return a list of dictionaries, where each dictionary represents a single Record.
       The expected format for each dictionary is:
       {
           "problems": {"issue_1": "Mismatch in area size", ...},
           "land_data": {"cadastral_number": "1234567890:01:001:0001", "area": 1.5, ...},
           "property_data": {"address": "Kyiv, Khreshchatyk 1", "owner": "John Doe", ...}
       }
    """
    
    # HARDCODED FAKE DATA FOR NOW
    fake_records = [
        {
            "problems": {"error": "Cadastral number mismatch between Land and Property registers"},
            "land_data": {
                "owner": "Company A",
                "cadastral_number": "3222486200:03:001:5001",
                "area_ha": 2.5
            },
            "property_data": {
                "owner": "Company B",
                "cadastral_number": "3222486200:03:001:5001",
                "area_ha": 2.5
            }
        },
        {
            "problems": {"warning": "Area size difference detected (> 5%)"},
            "land_data": {
                "owner": "Ivan Franko",
                "cadastral_number": "1210100000:01:002:0001",
                "area_ha": 0.45
            },
            "property_data": {
                "owner": "Ivan Franko",
                "cadastral_number": "1210100000:01:002:0001",
                "area_ha": 0.50
            }
        }
    ]
    
    return fake_records
