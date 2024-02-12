import requests
import re
import json
import html
import datetime
from zoneinfo import ZoneInfo
import psycopg2

from db import get_db_conn

URL = 'https://visitseattle.org/events/page/'
URL_LIST_FILE = './data/links.json'
URL_DETAIL_FILE = './data/data.json'

def list_links():
    res = requests.get(URL + '1/', headers={'User-Agent': 'Mozilla/5.0'})
    last_page_link = re.findall(r'bpn-last-page-link"><a href="(https://visitseattle.org/events/page/(\d+)/)?', res.text)
    
    if last_page_link:
        last_page_url, last_page_no = last_page_link[0]
        print('--- Starting to scrape event links, last page is "{last_page_no}" ---')
        links = []
        for page_no in range(1, int(last_page_no) + 1):
        # for page_no in range(1, 2):
            print(f'Scraping page {page_no} of {last_page_no}...')
            res = requests.get(URL + str(page_no) + '/', headers={'User-Agent': 'Mozilla/5.0'})
            links.extend(re.findall(r'<h3 class="event-title"><a href="(https://visitseattle.org/events/.+?/)" title=".+?">.+?</a></h3>', res.text))
        print('--- Finished scraping event links ---')

        with open(URL_LIST_FILE, 'w') as file:
            json.dump(links, file)
    else:
        print('Could not find the last page link')
    
# Get geolocation(lat, lon) from location
def get_lat_lon(location):
    # print('-----location-----')
    # print(location)
    # print('-----location-----')
    if  '/' in location:
        location = location.split(' / ')[0].strip()
    location_query = f'{location}, Seattle, WA'
    base_url = "https://nominatim.openstreetmap.org/search"
    query_params = {
        "q": location_query,
        "format": "jsonv2"
    }
    response = requests.get(base_url, params=query_params)
    data = response.json()

    if data and isinstance(data, list) and len(data) > 0:
        return data[0].get('lat'), data[0].get('lon')
    else:
        return None, None 

# Get gridpoint for weather details
def get_gridpoint(url):
    weather_summary = {'MaxTemp': 'No data', 'MinTemp': 'No data', 'WindChill': 'No data'} 
    try:
        gridPoint_res = requests.get(url)
        gridPoint_data = gridPoint_res.json()

        if gridPoint_res.status_code == 200 and 'properties' in gridPoint_data:
            maxTemp = gridPoint_data['properties']['maxTemperature']['values'][0]['value']
            minTemp = gridPoint_data['properties']['minTemperature']['values'][0]['value']
            windChill= gridPoint_data['properties']['windChill']['values'][0]['value']
            weather_summary = {
                'MaxTemp': maxTemp, 
                'MinTemp': minTemp, 
                'WindChill': windChill
            }
        else:
            print(f"Weather data not available for {url}")
    except Exception as e:
        print(f"Error fetching weather data: {e}")
    return weather_summary

# Get weather from the lat and lon
def get_weather_data(lat, lon):
    weather_summary = {'ShortForecast': 'No data', 'GridPoint': 'No data'}  # Default summary

    if lat is None or lon is None:
        return weather_summary  # Return default summary if lat or lon is missing

    point_url = f"https://api.weather.gov/points/{lat},{lon}"
    try:
        point_res = requests.get(point_url)
        if point_res.status_code == 200:
            point_data = point_res.json()
            # print('---- point data ----')
            # print(point_data)
            # print('---- point data ----')
            forecast_url = point_data['properties'].get('forecast')
            grid_point_url = point_data['properties'].get('forecastGridData') 
            # print('---- grid point url ----')
            # print(grid_point_url)
            # print('---- grid point url ----')

            forecast_res = requests.get(forecast_url)
            if forecast_res.status_code == 200:
                forecast_data = forecast_res.json()
                if 'properties' in forecast_data and 'periods' in forecast_data['properties']:
                    periods = forecast_data['properties']['periods']
                    for period in periods:
                        if period['isDaytime']:
                            weather_summary = {
                                'ShortForecast': period['shortForecast'],
                                'GridPoint': grid_point_url  # Include the grid point URL for later use
                            }
                            break
        else:
            print(f"Weather data not available for {lat},{lon}")
    except Exception as e:
        print(f"Error fetching weather data: {e}")

    return weather_summary

def get_detail_page():
    links = json.load(open(URL_LIST_FILE, 'r'))
    data = []
    for link in links:
        try:
            row = {}
            res = requests.get(link)
            row['title'] = html.unescape(re.findall(r'<h1 class="page-title" itemprop="headline">(.+?)</h1>', res.text)[0])
            datetime_venue = re.findall(r'<h4><span>.*?(\d{1,2}/\d{1,2}/\d{4})</span> \| <span>(.+?)</span></h4>', res.text)[0]
            row['date'] = datetime.datetime.strptime(datetime_venue[0], '%m/%d/%Y').replace(tzinfo=ZoneInfo('America/Los_Angeles')).isoformat()
            row['venue'] = datetime_venue[1].strip() # remove leading/trailing whitespaces
            metas = re.findall(r'<a href=".+?" class="button big medium black category">(.+?)</a>', res.text)
            row['category'] = html.unescape(metas[0])
            row['location'] = metas[1]
            # Get latitude and longitude
            lat, lon = get_lat_lon(row['location'])
            row['geolocation'] = lat, lon
            weather_forecast = get_weather_data(lat, lon)
            row['weather_condition'] = weather_forecast['ShortForecast']
            # Get minTemp, maxTemp, windChill from gridPoint
            grid_point_data = get_gridpoint(weather_forecast['GridPoint'])
            row['weather_minTemp'] = grid_point_data['MinTemp']
            row['weather_maxTemp'] = grid_point_data['MaxTemp']
            row['weather_windChill'] = grid_point_data['WindChill']

            data.append(row)

            print('current data')
            print()
            print(data)
            print('----------------')
            print()

        except IndexError as e:
            print(f'Error: {e}')
            print(f'Link: {link}')
    json.dump(data, open(URL_DETAIL_FILE, 'w'))



def insert_to_pg():
    q = '''
    CREATE TABLE IF NOT EXISTS events (
        url TEXT PRIMARY KEY,
        title TEXT,
        date TIMESTAMP WITH TIME ZONE,
        venue TEXT,
        category TEXT,
        location TEXT,
        geolocation TEXT,
        weathercondition TEXT,
        weathermintemp FLOAT,
        weathermaxtemp FLOAT,
        weatherwindchill FLOAT
    );
    '''
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute(q)
    
    urls = json.load(open(URL_LIST_FILE, 'r'))
    data = json.load(open(URL_DETAIL_FILE, 'r'))
    for url, row in zip(urls, data):
        q = '''
        INSERT INTO events (url, title, date, venue, category, location, geolocation, weathercondition, weathermintemp, weathermaxtemp, weatherwindchill)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (url) DO NOTHING;
        '''
        cur.execute(q, (url, row['title'], row['date'], row['venue'], row['category'], row['location'], row['geolocation'], row['weather_condition'], row['weather_minTemp'], row['weather_maxTemp'], row['weather_windChill']))

def scrape_events_data():
    list_links()
    get_detail_page()
    insert_to_pg()

if __name__ == '__main__':
    scrape_events_data()