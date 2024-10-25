from flask import Flask, jsonify
from datetime import datetime
from bs4 import BeautifulSoup
from botasaurus import *

app = Flask(__name__)
PORT = 8000

state_url_suffixes = {
    "andaman-and-nicobar-islands": "andaman-nicobar-s1",
    "andhra-pradesh": "andhra-pradesh-s2",
    "arunachal-pradesh": "arunachal-pradesh-s3",
    "assam": "assam-s4",
    "bihar": "bihar-s5",
    "chandigarh": "chandigarh-s6",
    "chhattisgarh": "chhatisgarh-s7",
    "dadra-and-nagar-haveli": "dadra-nagarhaveli-s8",
    "daman-and-diu": "daman-diu-s9",
    "delhi": "delhi-s10",
    "goa": "goa-s11",
    "gujarat": "gujarat-s12",
    "haryana": "haryana-s13",
    "himachal-pradesh": "himachal-pradesh-s14",
    "jammu-and-kashmir": "jammu-kashmir-s15",
    "jharkhand": "jharkhand-s16",
    "karnataka": "karnataka-s17",
    "kerala": "kerala-s18",
    "madhya-pradesh": "madhya-pradesh-s19",
    "maharashtra": "maharashtra-s20",
    "manipur": "manipur-s21",
    "meghalaya": "meghalaya-s22",
    "mizoram": "mizoram-s23",
    "nagaland": "nagaland-s24",
    "odisha": "odisha-s25",
    "pondicherry": "pondicherry-s26",
    "punjab": "punjab-s27",
    "rajasthan": "rajasthan-s28",
    "sikkim": "sikkim-s29",
    "tamil-nadu": "tamil-nadu-s30",
    "telangana": "telangana-s31",
    "tripura": "tripura-s32",
    "uttar-pradesh": "uttar-pradesh-s33",
    "uttarakhand": "uttarakhand-s34",
    "west-bengal": "west-bengal-s35"
}

@request(use_stealth=True)
def fetch_url_content(request: AntiDetectRequests, url_suffix):
    base_url = 'https://www.goodreturns.in'
    url = f"{base_url}/{url_suffix}"
    response = request.get(url)
    if response.status_code == 200:
        return response.text
    else:
        print(f"Failed to fetch data with status code {response.status_code}, URL: {url}")
        raise Exception(f"Failed to fetch data with status code {response.status_code}")


def scrape_data_for_state(html, fuel_type, state_name, state_suffix):
    soup = BeautifulSoup(html, 'html.parser')
    city_prices = {}

    # Extract the title from the page and check if it matches the required format
    page_title = soup.find('title').get_text(strip=True)
    # Break the state name into words and check if any word is in the title
    state_words = state_suffix.replace('-', ' ').title().split()
    if not any(word in page_title for word in state_words):
        # Log the mismatch and skip the scraping if none of the words from the state name match the title
        print(f"Title mismatch: expected one of {state_words} in title, got '{page_title}'")
        return city_prices  # Return empty dict for this fuel type

    # Find the div with class 'gd-fuel-table-data'
    data_div = soup.find('div', class_='gd-fuel-table-data')

    if not data_div:
        # Handle the case where the div is not found
        print(f"Div for {fuel_type} not found, skipping...")
        return city_prices  # Return empty dict for this fuel type

    # Find all tables within the div
    tables = data_div.find_all('table', class_='gd-fuel-table-list')

    if not tables:
        # Handle the case where no tables are found within the div
        print(f"No tables found for {fuel_type}, skipping...")
        return city_prices  # Return empty dict for this fuel type

    # Flag to indicate if the header row has been skipped
    header_skipped = False

    # Iterate over each table found in the div
    for table in tables:
        # Determine if the header row should be skipped
        rows = table.find('tbody').find_all('tr')

        # Skip the first row only in the first table
        if not header_skipped and rows:
            rows = rows[1:]  # Skip the header row
            header_skipped = True

        # Iterate over the rows in the table
        for row in rows:
            columns = row.find_all('td')
            if len(columns) >= 3:
                city_link = columns[0].find('a')
                city = city_link.get_text(strip=True) if city_link else 'Unknown City'

                today_price = columns[1].get_text(strip=True).replace('₹', '').replace(',', '').strip()
                yesterday_price = columns[2].get_text(strip=True).replace('₹', '').replace(',', '').strip()

                # Handle cases with unfamiliar words, non-numeric data, or blank spaces
                today_price = safe_convert_to_float(today_price)
                yesterday_price = safe_convert_to_float(yesterday_price)

                # If prices are None, use default or placeholder values
                if today_price is None:
                    today_price = 0.0  # or some other appropriate placeholder
                if yesterday_price is None:
                    yesterday_price = today_price  # Assume no change if yesterday's price is unknown

                price_change = today_price - yesterday_price if today_price is not None and yesterday_price is not None else None

                city_id = city.lower().replace(' ', '-')
                if city_id not in city_prices:
                    city_prices[city_id] = {
                        "cityId": city_id,
                        "cityName": city,
                        "applicableOn": datetime.now().strftime("%Y-%m-%d"),
                        "fuel": {}
                    }
                city_prices[city_id]["fuel"][fuel_type] = {
                    "retailPrice": today_price,
                    "retailPriceChange": price_change,
                    "retailUnit": "litre",
                    "currency": "INR",
                    "retailPriceChangeInterval": "day"
                }

    return city_prices

def safe_convert_to_float(price_str):
    try:
        # Attempt to convert directly to float
        return float(price_str)
    except ValueError:
        # Handle cases where conversion fails
        if not price_str or not price_str.replace('.', '', 1).isdigit():
            return None  # Return None if the string is empty or not a valid number
        return None


@app.route('/all/<state_name>')
def get_state_data(state_name):
    state_suffix = state_url_suffixes.get(state_name.replace(' ', '-').lower())
    if not state_suffix:
        return jsonify({'error': 'State not found'}), 404

    fuel_types = ['petrol', 'diesel', 'cng']  # As an example
    consolidated_city_data = {}
    for fuel_type in fuel_types:
        url_suffix = f"{fuel_type}-price-in-{state_suffix}.html"
        html = fetch_url_content(url_suffix)
        fuel_data = scrape_data_for_state(html, fuel_type, state_name, state_suffix)
        for city_id, data in fuel_data.items():
            if city_id not in consolidated_city_data:
                consolidated_city_data[city_id] = data
            else:
                consolidated_city_data[city_id]['fuel'].update(data['fuel'])

    return jsonify({
        "stateId": state_suffix.split('-')[0],
        "stateName": state_name.replace('-', ' ').title(),
        "countryId": "india",
        "countryName": "India",
        "cityPrices": list(consolidated_city_data.values())
    })

if __name__ == '__main__':
    app.run(port=PORT, debug=True)