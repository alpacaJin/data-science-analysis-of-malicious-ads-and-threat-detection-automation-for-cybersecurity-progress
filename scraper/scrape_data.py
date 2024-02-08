## Libraries
# Flask
from flask import Blueprint, render_template, request
# Scraping
import requests, tldextract, json, time, random
from bs4 import BeautifulSoup
from csv import writer
# Globe
import geopandas as gpd
# Locality
import pandas as pd
from geopy.geocoders import Nominatim
# Logging
import firebase_admin
from firebase_admin import credentials, db
from datetime import datetime

# Initialize Firebase
cred = credentials.Certificate('key.json')
default_app = firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://careless-8a683-default-rtdb.firebaseio.com/'
})

timestamp = datetime.now().strftime("%H%M%S")
ref = db.reference(f"/{timestamp}")

## Initialize Nominatim API
geolocator = Nominatim(user_agent="MyApp")

## BeautifulSoup web scraper
def scrape_data(keywords, headers, iteration):
    # Specify User Agent to mitigate bot-blocking
    print(headers)

    # Proxy rotation (random)
    start0 = time.time()
    proxies = open("sup-file/proxies.txt", "r").read().strip().split("\n")
    # Rotate proxies
    random_proxy = random.choice(proxies)

    # Specify keywords
    listOfKeywords = keywords
    
    # Specify number of scrapes
    print(iteration)

    numberOfTimes = iteration
    resultDict = {}
    locality, locality2 = '', ''

    # Write headers
    with open("static/company_locality.csv", "w", encoding='utf-8', newline='') as file:
        thewriter = writer(file)
        header = ['Company', 'CityCountry', 'Coordinates']
        thewriter.writerow(header)

    # Read companies_sorted
    start1 = time.time()
    companies_df = pd.read_csv('static/companies_sorted.csv')

    # Get total response time
    totResponseTime1 = time.time() - start1
    print("Total csv read time: " + str(totResponseTime1) + " seconds.")

    # Write advertisement elements to csv file
    with open("scrape-file/scraped_google_urls.csv", "w", encoding='utf-8', newline='') as file:
        thewriter = writer(file)
        header = ['URL', 'Company', 'Title', 'Product_Description']
        thewriter.writerow(header)

        for keyword in listOfKeywords:          
            # To find reoccurent companies
            companyList = []
            numOfAds = 0
            resultDict[keyword] = {}
            adElements = []
            
            try:
                print("Proxy: ", random_proxy)                
                for _ in range(numberOfTimes):
                    # Get requests from google search query
                    payload = {'q': keyword}
                    start = time.time()
                    html = requests.get("https://www.google.com/search?q=", params=payload, headers=headers, proxies = {"http": f"http://{random_proxy}"})
                    
                    # Get response time
                    responseTime = time.time() - start
                    print("Request response time: " + str(responseTime) + " seconds.")

                    # Check valid request
                    status_code = html.status_code
                    if status_code == 200:
                        # Create BeautifulSoup object
                        response = html.text
                        soup = BeautifulSoup(response, 'html.parser')
                            
                        # Scraping top and bottom advertisements -- URL, Company
                        print('--------------------------------Advertisements--------------------------------')
                        topBotAds = soup.find(id = 'main')
                        if (topBotAds):
                            # Monitor number of ads for each keyword
                            if len(topBotAds.findAll('div', class_='uEierd')) > 0:
                                numOfAds += 1
                            absolute_top = 0

                            for container in topBotAds.findAll('div', class_='uEierd'):
                                try:
                                    try:
                                        advertisementTitle = container.find('div', class_='CCgQ5 Va3FIb EE3Upf TElO2c OSrXXb').span.text
                                    except:
                                        advertisementTitle = 'N/A'

                                    url = container.find('div', class_='v5yQqb').find('span', class_='ob9lvb').text
                                    company = tldextract.extract(url).domain

                                    # Determine absolute-top, ad positions
                                    if company not in companyList:
                                        companyList.append(company)
                                        if absolute_top == 0:
                                            resultDict[keyword][company] = {'absolute-top':1, 'ad':0}
                                        else:
                                            resultDict[keyword][company] = {'absolute-top':0, 'ad':1}
                                    else:
                                        if absolute_top == 0:
                                            resultDict[keyword][company]['absolute-top'] += 1
                                        else:
                                            resultDict[keyword][company]['ad'] += 1
                                except:
                                    url = 'N/A'
                                    company = 'N/A'

                                try:
                                    productDesciption = container.find('div', class_='Va3FIb r025kc lVm3ye Hdw6tb').text
                                except:
                                    productDesciption = 'N/A'

                                # Company locality extraction
                                match = companies_df[companies_df['name'] == company]
                                if not match.empty:
                                    locality = match['locality'].iloc[0]

                                    # Remove state/province
                                    # parts = locality.split(", ")
                                    # locality2 = ", ".join([parts[0], parts[-1]])

                                # Coordinates from city, country
                                coordinates = geolocator.geocode(locality)
                                if coordinates:
                                    coordinates_str = "[{}, {}]".format(coordinates.longitude, coordinates.latitude)
                                else:
                                    coordinates_str = "[null, null]"
                                # locationElements = [company, locality2, coordinates_str]

                                locationElements = {
                                    'company': company,
                                    'locality': locality,
                                    'coordinates': coordinates_str
                                }

                                # Push to database
                                ref.push(locationElements)

                                # with open("static/company_locality.csv", "a", encoding='utf-8', newline='') as addfile:
                                #     thewriter2 = writer(addfile)
                                #     thewriter2.writerow(locationElements)

                                # Modify url - check http, www
                                # if not url.startswith(('http://', 'https://')):
                                #     url2 = 'https://' + url

                                # parts = url2.split('://')
                                # protocol = parts[0]
                                # rest_of_url = parts[1]
                                # subdomains = rest_of_url.split('.', 1)
                                # if subdomains[0] != 'www':
                                #     subdomains[0] = 'www'
                                #     rest_of_url = '.'.join(subdomains)

                                # url2 = protocol + '://' + rest_of_url

                                print(url)
                                print(locality)
                                print(coordinates.longitude, coordinates.latitude)
                                print(company)
                                print(advertisementTitle)
                                print(productDesciption)
                                print()
                                absolute_top += 1
                            
                                adElements = [url, company, advertisementTitle, productDesciption]
                                thewriter.writerow(adElements)

                            # Write advertisement source code to html file
                            with open("scrape-file\google_urls.html", "w", encoding='utf-8') as file:
                                file.write(str(soup))   
            except Exception as e:
                print(e)
                    
            keys = list(resultDict[keyword].keys())
            for name in ['ad', 'absolute-top']:
                keys.sort(key=lambda k: resultDict[keyword][k][name], reverse=True)

            # Generate resulting dictionary
            resultDict[keyword]['top performers'] = keys
            resultDict[keyword]['total ads'] = numOfAds

    print(json.dumps(resultDict, indent = 4))

    # Get total response time
    totResponseTime = time.time() - start0
    print("Total request response time: " + str(totResponseTime) + " seconds.")

    return resultDict


## Real-time Globe
# Load in shapefile or GeoJSON file
def load_globe():
    world_polygon = gpd.read_file("sup-file/ne_110m_admin_0_countries.geojson")

    world_polygon.to_file("static/countries_updated.geojson", driver='GeoJSON')


## Flask
scrape_data_bp = Blueprint('scrape_data', __name__)

@scrape_data_bp.route('/webscrape', methods=['GET', 'POST'])
def webscrape():
    # Select keywords
    keywords = request.form.get('serialized_keywords')
    keywords = keywords.split(',') if keywords else ''
    print(keywords)

    # Select user agents
    user_agent = request.form['user_agent']
    headers = {'User-Agent': user_agent}
    
    # Select iterations
    iteration = request.form.get('iteration', 1)
    iteration = int(iteration)

    # Call the load globe function
    load_globe()

    # Call the scrape_data function to get the scraped data
    resultDict = scrape_data(keywords, headers, iteration)

    # Pass to template
    return render_template('index.html', scraped_data=resultDict)