import requests
import re
import json
import html
import datetime
from zoneinfo import ZoneInfo
import psycopg2

URL = 'https://visitseattle.org/events/page/'
URL_LIST_FILE = './data/links.json'
URL_DETAIL_FILE = './data/data.json'
DB_CONNECTION_STRING = "dbname='postgres' user='chelsey' host='techin510-lab5.postgres.database.azure.com' password='5074AVril'"

def list_links():
    # Fetch the initial page to find out the number of pages
    res = requests.get(URL + '1/', headers={'User-Agent': 'Mozilla/5.0'})
    # Corrected regex to match the 'href' attribute correctly and extract the page number
    last_page_match = re.search(r'<li class="bpn-last-page-link"><a href="https://visitseattle.org/events/page/(\d+)/?', res.text)
    if last_page_match:
        last_page_no = int(last_page_match.group(1))
    else:
        last_page_no = 1  # Default to 1 if no match is found

    links = []
    for page_no in range(1, last_page_no + 1):
        res = requests.get(URL + f'page/{page_no}/', headers={'User-Agent': 'Mozilla/5.0'})
        # Ensure the regex for scraping links matches the actual HTML structure you're targeting
        # The example regex below assumes the structure provided earlier; adjust as necessary
        page_links = re.findall(r'<h3 class="event-title"><a href="(https://visitseattle.org/events/.+?/)" title=".+?">', res.text)
        links.extend(page_links)

    with open(URL_LIST_FILE, 'w') as file:
        json.dump(links, file)

def get_detail_page():
    links = json.load(open(URL_LIST_FILE, 'r'))
    data = []
    for link in links:
        try:
            row = {}
            res = requests.get(link, headers={'User-Agent': 'Mozilla/5.0'})
            row['title'] = html.unescape(re.findall(r'<h1 class="page-title" itemprop="headline">(.+?)</h1>', res.text)[0])
            
            datetime_venue = re.findall(r'<h4><span>.*?(\d{1,2}/\d{1,2}/\d{4})</span> \| <span>(.+?)</span></h4>', res.text)[0]
            row['date'] = datetime.datetime.strptime(datetime_venue[0], '%m/%d/%Y').replace(tzinfo=ZoneInfo('America/Los_Angeles')).isoformat()
            row['venue'] = datetime_venue[1].strip()
            
            metas = re.findall(r'<a href=".+?" class="button big medium black category">(.+?)</a >', res.text)
            row['category'] = html.unescape(metas[0])
            
            # Assuming the second element in 'metas' is the region, and using it as 'location'
            row['location'] = metas[1] if len(metas) > 1 else "Region Not Available"

            data.append(row)
        except IndexError as e:
            print(f'Error: {e}')
            print(f'Link: {link}')

    json.dump(data, open(URL_DETAIL_FILE, 'w'))

def insert_to_pg():
    urls = json.load(open(URL_LIST_FILE, 'r'))
    data = json.load(open(URL_DETAIL_FILE, 'r'))
    
    conn = psycopg2.connect(DB_CONNECTION_STRING)
    cur = conn.cursor()

    for url, row in zip(urls, data):
        try:
            cur.execute(
                """
                INSERT INTO events (url, title, date, venue, category, location)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (url) DO NOTHING;
                """,
                (url, row['title'], row['date'], row['venue'], row['category'], row['location'])
            )
        except psycopg2.Error as e:
            print(f"Error inserting data for URL: {url}")
            print(e)

    conn.commit()
    cur.close()
    conn.close()

def scrape_events_data():
    list_links()
    get_detail_page()
    insert_to_pg()

if __name__ == '__main__':
    scrape_events_data()