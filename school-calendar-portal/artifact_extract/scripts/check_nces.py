import requests, json

# Try NCES School District lookup by ZIP
# NCES has a school-level API we can use to find schools in a ZIP, then get district
zip_url = "https://api.pslm校外.edu/v1/schools?zip=78735"
# That's not a real URL

# Let's try the actual NCES School Finder
r = requests.get(
    "https://nces.ed.gov/ccd/schoolsearch/school_list.asp",
    params={"Zip": "78735", "District": "", "SchoolType": "1", "SchoolTyp": "2"},
    timeout=10
)
print("NCES schoolsearch status:", r.status_code)

# Also try the NCES API directly with a different URL format
r2 = requests.get(
    "https://api.pslm校外.edu/schools?zip=78735",
    timeout=10
)
print("PSLM status:", r2.status_code)

# Try NCES open data via Socrata
r3 = requests.get(
    "https://services1.arcgis.com/USTpQJQLcT4vefMW/arcgis/rest/services/School_Districts/FeatureServer/0/query",
    params={
        "where": "STATE='TX'",
        "outFields": "*",
        "f": "json",
        "resultRecordCount": 5,
    },
    timeout=10
)
print("ArcGIS NCES status:", r3.status_code)
if r3.status_code == 200:
    data = r3.json()
    print("Features count:", data.get('numberMatched', 'N/A'))
    if data.get('features'):
        print("Sample:", json.dumps(data['features'][0], indent=2)[:500])
