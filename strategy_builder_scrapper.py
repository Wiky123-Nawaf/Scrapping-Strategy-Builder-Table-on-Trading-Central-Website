import requests
import csv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json
import time
import re


# Set up Chrome WebDriver options
options = webdriver.ChromeOptions()
options.set_capability("goog:loggingPrefs", {"performance": "ALL"})  # Enable network logs

driver = webdriver.Chrome(options=options)

def extract_token(api_url):
    """Extract token from API URL."""
    match = re.search(r'token=([\w\-\.]+)', api_url)
    return match.group(1) if match else None

try:
    # ✅ Step 1: Open Login Page
    login_url = "https://example.tradingcentral.com/dark/serve.shtml?page=login"
    driver.get(login_url)

    # Wait for login fields to load
    wait = WebDriverWait(driver, 10)
    username_input = wait.until(EC.presence_of_element_located((By.NAME, "User-ID")))
    password_input = driver.find_element(By.NAME, "Password")

    # Enter credentials
    username_input.send_keys("input_username_here") #input username here
    password_input.send_keys("input_password_here") #input password here

    # Click the login button
    login_button = driver.find_element(By.CLASS_NAME, "loginbutton")
    login_button.click()

    # ✅ Step 2: Navigate to the Data Page
    data_url = "https://example.tradingcentral.com/dark/presto/build_screen?sid=P0%252FD4wbMu0hB0jHNQSYSFypZyhUXFMEm"
    driver.get(data_url)

    # ✅ Step 3: Click the "Export" Button
    try:
        export_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Export Matches']")))
        export_button.click()
        print("✅ Export button clicked (Standard Method).")
    except:
        print("⚠️ Standard click failed. Trying JavaScript click...")
        export_button_js = driver.find_element(By.XPATH, "//button[@aria-label='Export Matches']")
        driver.execute_script("arguments[0].click();", export_button_js)
        print("✅ Export button clicked (JavaScript Method).")

    time.sleep(3)  # Ensure request is made

    # ✅ Step 4: Extract API URL from network logs
    logs = driver.get_log("performance")
    extracted_api_url = None
    token = None

    for log in logs:
        log_data = json.loads(log["message"])["message"]
        if log_data["method"] == "Network.requestWillBeSent":
            request_url = log_data["params"]["request"]["url"]
            if "api.tradingcentral.com/screens/v3/instruments" in request_url:
                extracted_api_url = request_url
                token = extract_token(extracted_api_url)
                break

except Exception as e:
    print(f"⚠️ Error: {e}")

finally:
    driver.quit()
    print("✅ Browser closed.")

# ✅ Step 5: Prompt User for Country
#user_country = input("Enter the country: ").strip()

# Find the corresponding group ID
#group_ids = COUNTRY_TO_IDS.get(user_country)

if token:
    print(f"✅ Extracted Token: {token}")
    #print(f"✅ Group IDs for {user_country}: {group_ids}")
else:
    print("⚠️ No valid token found or country name incorrect.")
    

COUNTRY_TO_IDS = {
    "USA/Canada": "AMEX,NASDAQ,NYSE,XCNQ,NEO,TORONTO,TSXV",
    "Australia": "ASX",
    "Bahrain": "BAH",
    "Belgium": "BRU",
    "CBOE": "CBOE-AT,CBOE-BE,CBOE-CH,CBOE-CZ,CBOE-DE,CBOE-DK,CBOE-ES,CBOE-FI,CBOE-FR,CBOE-IE,CBOE-IT,CBOE-NL,CBOE-NO,CBOE-PT,CBOE-SE,CBOE-UK",
    "China": "SHH,SHZ",
    "Denmark": "CSE",
    "Egypt": "EGX",
    "Finland": "HEX",
    "France": "PAR",
    "Germany": "FSE,XETRA",
    "Hong Kong Exchange": "HKG",
    "India": "BSE,NSI",
    "Ireland": "ISE",
    "Israel": "TLV",
    "Japan": "TYO",
    "Korea": "KSC",
    "Kuwait": "KUW",
    "Malaysia": "MYX",
    "Mexico": "MEX",
    "Netherlands": "AEX",
    "Norway": "OSL",
    "Philippines": "PSE",
    "Portugal": "LIS",
    "Qatar": "DSM",
    "Saudi Arabia": "SAU",
    "Singapore": "SGX-ST",
    "Spain": "SIBE",
    "Sweden": "SSE",
    "Switzerland": "SWX",
    "Taiwan": "TAI,TPEX",
    "Thailand": "SET",
    "Turkey": "IST",
    "UAE": "DFM,ADX",
    "United Kingdom": "LONDON"
}

def fetch_api_data(api_url, params, token):
    extracted_data = []
    page = 1
    base_params = {
        # "distributionGroupIds":  # Removed, set in main loop
        "page": 1,
        "size": 500,
        "lang": "en",
        "token": token,
        "sort": "rank:desc"
    }
    base_params.update(params)

    while True:
        base_params["page"] = page
        response = requests.get(api_url, params=base_params)

        if response.status_code == 200:
            data = response.json()
            if not data:
                break

            for item in data:
                instrument = item["instrument"]
                criteria = {c["criterionId"]: c["value"] for c in item["criteria"]}

                extracted_row = {
                    "company_name": instrument["name"],
                    "symbol": instrument["symbol"],
                    "instrument_id": instrument["instrumentId"],
                    "price": criteria.get("prc01"),
                    "share_type": instrument.get("issueType")
                }

                for criterion in [
                    'PF002', 'PF003', 'PF004', 'PF005', 'PF006', 'PF101',
                    'TR003', 'TR005', 'TR006', 'TR007', 'TR008', 'TR102', 'TR104',
                    'DE201', 'DE202', 'DE203', 'GE201', 'GE202', 'GE205', 'GE206',
                    'VA201', 'VA204', 'VA205', 'VA206', 'VA207', 'DI101', 'DI202',
                    'DI203', 'DI204', 'PR201', 'PR202', 'PR203', 'PR204', 'PR205',
                    'PR206', 'PR207', 'PR208', 'PR209', 'AN003', 'AN004', 'AN005',
                    'AN006', 'AN007', 'AN008'
                ]:
                    extracted_row[criterion] = criteria.get(criterion, None)

                extracted_data.append(extracted_row)

            print(f"Page {page}: Fetched {len(data)} records")
            page += 1
        else:
            print(f"Failed to fetch data. Status: {response.status_code}")
            break

    return extracted_data


# Configuration
API_URL = "https://api.tradingcentral.com/screens/v3/instruments"
TOKEN = token

API_CONFIGS = [
    {"criterion_name": "Price Performance 5 Day (%)", "criterion": "PF002:is:notnull", "criterion_id": 'PF002', "ba005_filter": "COM:UNI:PFD"},
    {"criterion_name": "Price Performance 4 Week (%)", "criterion": "PF003:is:notnull", "criterion_id": 'PF003', "ba005_filter": "COM:UNI:PFD"},
    {"criterion_name": "Price Performance 13 Week (%)", "criterion": "PF004:is:notnull", "criterion_id": 'PF004', "ba005_filter": "COM:UNI:PFD"},
    {"criterion_name": "Price Performance 52 Week (%)", "criterion": "PF005:is:notnull", "criterion_id": 'PF005', "ba005_filter": "COM:UNI:PFD"},
    {"criterion_name": "Price Performance Year-to-Date (%)", "criterion": "PF006:is:notnull", "criterion_id": 'PF006', "ba005_filter": "COM:UNI:PFD"},
    {"criterion_name": "Price Performance Today (%)", "criterion": "PF101:is:notnull", "criterion_id": 'PF101', "ba005_filter": "COM:UNI:PFD"},
    {"criterion_name": "Volume 90-Day", "criterion": "TR003:is:notnull", "criterion_id": 'TR003', "ba005_filter": "COM:UNI:PFD"},
    {"criterion_name": "Volume 10-Day vs. 90-Day", "criterion": "TR005:is:notnull", "criterion_id": 'TR005', "ba005_filter": "COM:UNI:PFD"},
    {"criterion_name": "% Change from 52-Week High", "criterion": "TR006:is:notnull", "criterion_id": 'TR006', "ba005_filter": "COM:UNI:PFD"},
    {"criterion_name": "% Change from 52-Week Low", "criterion": "TR007:is:notnull", "criterion_id": 'TR007', "ba005_filter": "COM:UNI:PFD"},
    {"criterion_name": "Days Since New 52-Week High/Low", "criterion": "TR008:is:notnull", "criterion_id": 'TR008', "ba005_filter": "COM:UNI:PFD"},
    {"criterion_name": "Volume Today", "criterion": "TR102:is:notnull", "criterion_id": 'TR102', "ba005_filter": "COM:UNI:PFD"},
    {"criterion_name": "Volume Today vs. 10-Day", "criterion": "TR104:is:notnull", "criterion_id": 'TR104', "ba005_filter": "COM:UNI:PFD"},
    {"criterion_name": "Current Ratio", "criterion": "DE201:is:notnull", "criterion_id": 'DE201', "ba005_filter": "COM:UNI:PFD"},
    {"criterion_name": "Debt to Equity Ratio", "criterion": "DE202:is:notnull", "criterion_id": 'DE202', "ba005_filter": "COM:UNI:PFD"},
    {"criterion_name": "Debt to Capital Ratio", "criterion": "DE203:is:notnull", "criterion_id": 'DE203', "ba005_filter": "COM:UNI:PFD"},
    {"criterion_name": "EPS Growth (Last Quarter vs. Prior Year)", "criterion": "GE201:is:notnull", "criterion_id": 'GE201', "ba005_filter": "COM:UNI:PFD"},
    {"criterion_name": "EPS Growth (5-Year Historical)", "criterion": "GE202:is:notnull", "criterion_id": 'GE202', "ba005_filter": "COM:UNI:PFD"},
    {"criterion_name": "Cash Flow Growth (Last Qtr. vs. Prior Yr.)", "criterion": "GE205:is:notnull", "criterion_id": 'GE205', "ba005_filter": "COM:UNI:PFD"},
    {"criterion_name": "Revenue Growth (Last Qtr. vs. Prior Yr.)", "criterion": "GE206:is:notnull", "criterion_id": 'GE206', "ba005_filter": "COM:UNI:PFD"},
    {"criterion_name": "P/E (TTM)", "criterion": "VA201:is:notnull", "criterion_id": 'VA201', "ba005_filter": "COM:UNI:PFD"},
    {"criterion_name": "Price/Book Ratio", "criterion": "VA204:is:notnull", "criterion_id": 'VA204', "ba005_filter": "COM:UNI:PFD"},
    {"criterion_name": "Price/Cash Flow Ratio", "criterion": "VA205:is:notnull", "criterion_id": 'VA205', "ba005_filter": "COM:UNI:PFD"},
    {"criterion_name": "Price/Sales Ratio", "criterion": "VA206:is:notnull", "criterion_id": 'VA206', "ba005_filter": "COM:UNI:PFD"},
    {"criterion_name": "Earnings Yield (EPS/Price per Share)", "criterion": "VA207:is:notnull", "criterion_id": 'VA207', "ba005_filter": "COM:UNI:PFD"},
    {"criterion_name": "Dividend Yield", "criterion": "DI101:is:notnull", "criterion_id": 'DI101', "ba005_filter": "COM:UNI:PFD"},
    {"criterion_name": "Dividend Growth Rate Current to Prior Year", "criterion": "DI202:is:notnull", "criterion_id": 'DI202', "ba005_filter": "COM:UNI:PFD"},
    {"criterion_name": "Dividend Growth Rate 5 Year Average", "criterion": "DI203:is:notnull", "criterion_id": 'DI203', "ba005_filter": "COM:UNI:PFD"},
    {"criterion_name": "Dividend Coverage", "criterion": "DI204:is:notnull", "criterion_id": 'DI204', "ba005_filter": "COM:UNI:PFD"},
    {"criterion_name": "Operating Margin (TTM)", "criterion": "PR201:is:notnull", "criterion_id": 'PR201', "ba005_filter": "COM:UNI:PFD"},
    {"criterion_name": "EBITD Margin (TTM)", "criterion": "PR202:is:notnull", "criterion_id": 'PR202', "ba005_filter": "COM:UNI:PFD"},
    {"criterion_name": "Gross Margin (TTM)", "criterion": "PR203:is:notnull", "criterion_id": 'PR203', "ba005_filter": "COM:UNI:PFD"},
    {"criterion_name": "Return on Equity (TTM)", "criterion": "PR204:is:notnull", "criterion_id": 'PR204', "ba005_filter": "COM:UNI:PFD"},
    {"criterion_name": "Return on Investment (TTM)", "criterion": "PR205:is:notnull", "criterion_id": 'PR205', "ba005_filter": "COM:UNI:PFD"},
    {"criterion_name": "Return on Sales (TTM)", "criterion": "PR206:is:notnull", "criterion_id": 'PR206', "ba005_filter": "COM:UNI:PFD"},
    {"criterion_name": "Return on Assets (TTM)", "criterion": "PR207:is:notnull", "criterion_id": 'PR207', "ba005_filter": "COM:UNI:PFD"},
    {"criterion_name": "Return on Capital (TTM)", "criterion": "PR208:is:notnull", "criterion_id": 'PR208', "ba005_filter": "COM:UNI:PFD"},
    {"criterion_name": "Revenue Per Employee", "criterion": "PR209:is:notnull", "criterion_id": 'PR209', "ba005_filter": "COM:UNI:PFD"},
    {"criterion_name": "TC Quantamental Rating®", "criterion": "AN003:is:notnull", "criterion_id": 'AN003', "ba005_filter": "COM:UNI:PFD"},
    {"criterion_name": "TC Growth Factor Rating", "criterion": "AN004:is:notnull", "criterion_id": 'AN004', "ba005_filter": "COM:UNI:PFD"},
    {"criterion_name": "TC Income Factor Rating", "criterion": "AN005:is:notnull", "criterion_id": 'AN005', "ba005_filter": "COM:UNI:PFD"},
    {"criterion_name": "TC Momentum Factor Rating", "criterion": "AN006:is:notnull", "criterion_id": 'AN006', "ba005_filter": "COM:UNI:PFD"},
    {"criterion_name": "TC Value Factor Rating", "criterion": "AN007:is:notnull", "criterion_id": 'AN007', "ba005_filter": "COM:UNI:PFD"},
    {"criterion_name": "TC Quality Factor Rating", "criterion": "AN008:is:notnull", "criterion_id": 'AN008', "ba005_filter": "COM:UNI:PFD"}
]

def run_data_extraction():
    """Runs the complete data extraction process and saves to a single CSV."""

    all_data = {}  # Accumulate all data here

    for user_country, country_ids in COUNTRY_TO_IDS.items():
        # 1. Fetch initial core data WITHOUT BA005 filter
        print(f"Fetching initial core data for {user_country} (without BA005 filter)...")
        initial_params = {
            "criterion": ["prc01:is:notnull"],
            "distributionGroupIds": country_ids  # Use the specific IDs
        }

        core_data = fetch_api_data(API_URL, initial_params, TOKEN)
        all_instrument_ids = {item["instrument_id"] for item in core_data}
        print(f"Total unique instruments found for {user_country}: {len(all_instrument_ids)}")

        if not all_instrument_ids:
            print(f"No data extracted for country {user_country}")
            continue

        # 2. Initialize/Update data structure with instrument IDs
        for instrument_id in all_instrument_ids:
            core_entry = next(item for item in core_data if item["instrument_id"] == instrument_id)
            if instrument_id not in all_data:
                all_data[instrument_id] = {
                    "company_name": core_entry["company_name"],
                    "symbol": core_entry["symbol"],
                    "instrument_id": instrument_id,
                    "price": core_entry["price"],
                    "share_type": core_entry["share_type"],
                    "country" : user_country #add country column
                }
                for criterion in [
                    'PF002', 'PF003', 'PF004', 'PF005', 'PF006', 'PF101',
                    'TR003', 'TR005', 'TR006', 'TR007', 'TR008', 'TR102', 'TR104',
                    'DE201', 'DE202', 'DE203', 'GE201', 'GE202', 'GE205', 'GE206',
                    'VA201', 'VA204', 'VA205', 'VA206', 'VA207', 'DI101', 'DI202',
                    'DI203', 'DI204', 'PR201', 'PR202', 'PR203', 'PR204', 'PR205',
                    'PR206', 'PR207', 'PR208', 'PR209', 'AN003', 'AN004', 'AN005',
                    'AN006', 'AN007', 'AN008'
                ]:
                    all_data[instrument_id][criterion] = None  # Initialize


        # 3. Populate criteria (WITH BA005)
        for config in API_CONFIGS:
            print(f"Fetching data for {config['criterion_name']} for {user_country}...")
            params = {
                "criterion": [config["criterion"], "prc01:is:notnull",
                             f"BA005:any:{config['ba005_filter']}"] ,
                "distributionGroupIds": country_ids
            }
            data = fetch_api_data(API_URL, params, TOKEN)

            for item in data:
                instrument_id = item["instrument_id"]
                if instrument_id in all_data: #check it exists
                  criterion_value = item.get(config['criterion_id'])
                  if config['criterion_id'] in ['PF002', 'PF003', 'PF004', 'PF005', 'PF006',
                                              'PF101', 'TR006', 'TR007', 'GE201', 'GE202',
                                              'GE205', 'GE206', 'VA207', 'DI101', 'DI202',
                                              'DI203', 'DI204', 'PR201', 'PR202', 'PR203',
                                              'PR204', 'PR205', 'PR206', 'PR207', 'PR208']:
                    if criterion_value is not None:
                          criterion_value *= 100

                  all_data[instrument_id][config['criterion_id']] = criterion_value


    # 4. CSV Export
    csv_columns = ["country", "company_name", "symbol", "instrument_id", "price", "share_type"] + [
        'PF002', 'PF003', 'PF004', 'PF005', 'PF006', 'PF101',
        'TR003', 'TR005', 'TR006', 'TR007', 'TR008', 'TR102', 'TR104',
        'DE201', 'DE202', 'DE203', 'GE201', 'GE202', 'GE205', 'GE206',
        'VA201', 'VA204', 'VA205', 'VA206', 'VA207', 'DI101', 'DI202',
        'DI203', 'DI204', 'PR201', 'PR202', 'PR203', 'PR204', 'PR205',
        'PR206', 'PR207', 'PR208', 'PR209', 'AN003', 'AN004', 'AN005',
        'AN006', 'AN007', 'AN008'
    ]

    csv_header_map = {
        "country" : "Country",
        "company_name": "Company Name",
        "symbol": "Stock Symbol",
        "instrument_id": "Instrument ID",
        "price": "Stock Price",
        "share_type": "Share Type",
        'PF002': "Price Performance 5 Day (%)",
        'PF003': "Price Performance 4 Week (%)",
        'PF004': "Price Performance 13 Week (%)",
        'PF005': "Price Performance 52 Week (%)",
        'PF006': "Price Performance Year-to-Date (%)",
        'PF101': "Price Performance Today (%)",
        'TR003': "Volume 90-Day",
        'TR005': "Volume 10-Day vs. 90-Day",
        'TR006': "% Change from 52-Week High",
        'TR007': "% Change from 52-Week Low",
        'TR008': "Days Since New 52-Week High/Low",
        'TR102': "Volume Today",
        'TR104': "Volume Today vs. 10-Day",
        'DE201': "Current Ratio",
        'DE202': "Debt to Equity Ratio",
        'DE203': "Debt to Capital Ratio",
        'GE201': "EPS Growth (Last Quarter vs. Prior Year) (%)",
        'GE202': "EPS Growth (5-Year Historical) (%)",
        'GE205': "Cash Flow Growth (Last Qtr. vs. Prior Yr.) (%)",
        'GE206': "Revenue Growth (Last Qtr. vs. Prior Yr.) (%)",
        'VA201': "P/E (TTM)",
        'VA204': "Price/Book Ratio",
        'VA205': "Price/Cash Flow Ratio",
        'VA206': "Price/Sales Ratio",
        'VA207': "Earnings Yield (EPS/Price per Share) (%)",
        'DI101': "Dividend Yield (%)",
        'DI202': "Dividend Growth Rate Current to Prior Year (%)",
        'DI203': "Dividend Growth Rate 5 Year Average (%)",
        'DI204': "Dividend Coverage (%)",
        'PR201': "Operating Margin (TTM) (%)",
        'PR202': "EBITD Margin (TTM) (%)",
        'PR203': "Gross Margin (TTM) (%)",
        'PR204': "Return on Equity (TTM) (%)",
        'PR205': "Return on Investment (TTM) (%)",
        'PR206': "Return on Sales (TTM) (%)",
        'PR207': "Return on Assets (TTM) (%)",
        'PR208': "Return on Capital (TTM) (%)",
        'PR209': "Revenue Per Employee",
        'AN003': "TC Quantamental Rating®",
        'AN004': "TC Growth Factor Rating",
        'AN005': "TC Income Factor Rating",
        'AN006': "TC Momentum Factor Rating",
        'AN007': "TC Value Factor Rating",
        'AN008': "TC Quality Factor Rating"
    }


    with open("complete_stockwash_data.csv", "w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=csv_columns)
        writer.writerow(csv_header_map)
        for data in all_data.values():
            writer.writerow(data)

    print("Data export completed successfully!")


# --- Main Execution ---
run_data_extraction()