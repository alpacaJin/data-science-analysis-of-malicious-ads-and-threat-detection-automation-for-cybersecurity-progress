## Libraries
# Flask
from flask import Blueprint, render_template
# Base
import pandas as pd, re, time
from tld import get_tld
from urllib.parse import urlparse
# Export
import pickle


## Preprocessing + RF model
def predict_data():
    # Path of file
    scraped_urls_file_path = "scrape-file/scraped_google_urls.csv"
    scraped_urls_data = pd.read_csv(scraped_urls_file_path)

    start0 = time.time()

    ## Data Preprocessing -- Check missing data, duplicates, Omit (www.), Feature extraction, & Split into train/test
    scraped_urls_data.isnull().sum()

    # Count duplicates
    duplicates = scraped_urls_data[scraped_urls_data.duplicated(subset=['URL'], keep=False)]
    # if not duplicates.empty:
    #     print("Duplicate values found:")
    #     print(duplicates)
    # else:
    #     print("No duplicate values found")

    # Remove duplicates
    scraped_urls_data.drop_duplicates(subset=['URL'], keep=False, inplace=True)

    # Reset the index to start at 0
    scraped_urls_data.reset_index(drop=True, inplace=True)

    # Omit (www.)
    scraped_urls_data['URL'] = scraped_urls_data['URL'].replace('www.', '', regex = True)

    # Feature Engineering -- URL length, Domain, Symbols
    scraped_urls_data['URL_Len'] = scraped_urls_data['URL'].apply(lambda x: len(str(x)))

    def process_tld(URL):
        try:
            res = get_tld(URL, as_object = True, fail_silently = False, fix_protocol = True)
            pri_domain= res.parsed_url.netloc
        except :
            pri_domain= None
        return pri_domain

    scraped_urls_data["Domain"] = scraped_urls_data['URL'].apply(lambda i: process_tld(i))

    # Features
    feature = ['@','?','-','=','.','#','%','+','$','!','*',',','//']
    for a in feature:
        scraped_urls_data[a] = scraped_urls_data['URL'].apply(lambda i: i.count(a))

    # Abnormal
    def abnormal_url(URL):
        hostname = urlparse(URL).hostname
        hostname = str(hostname)
        match = re.search(hostname, URL)
        if match:
            return 1
        else:
            return 0
        
    scraped_urls_data['Abnormal_url'] = scraped_urls_data['URL'].apply(lambda i: abnormal_url(i))

    # HTTP Presence
    def httpSecure(URL):
        htp = urlparse(URL).scheme
        match = str(htp)
        if match=='https':
            return 1
        else:
            return 0
        
    scraped_urls_data['Https'] = scraped_urls_data['URL'].apply(lambda i: httpSecure(i))

    # Count number of digits
    def digit_count(URL):
        digits = 0
        for i in URL:
            if i.isnumeric():
                digits = digits + 1
        return digits

    scraped_urls_data['Digits'] = scraped_urls_data['URL'].apply(lambda i: digit_count(i))

    # Count number of letter characters
    def letter_count(URL):
        letters = 0
        for i in URL:
            if i.isalpha():
                letters = letters + 1
        return letters

    scraped_urls_data['Letters']= scraped_urls_data['URL'].apply(lambda i: letter_count(i))

    # Check whether shortening service is present
    def Shortening_Service(URL):
        match = re.search('bit\.ly|goo\.gl|shorte\.st|go2l\.ink|x\.co|ow\.ly|t\.co|tinyurl|tr\.im|is\.gd|cli\.gs|'
                        'yfrog\.com|migre\.me|ff\.im|tiny\.cc|url4\.eu|twit\.ac|su\.pr|twurl\.nl|snipurl\.com|'
                        'short\.to|BudURL\.com|ping\.fm|post\.ly|Just\.as|bkite\.com|snipr\.com|fic\.kr|loopt\.us|'
                        'doiop\.com|short\.ie|kl\.am|wp\.me|rubyurl\.com|om\.ly|to\.ly|bit\.do|t\.co|lnkd\.in|'
                        'db\.tt|qr\.ae|adf\.ly|goo\.gl|bitly\.com|cur\.lv|tinyurl\.com|ow\.ly|bit\.ly|ity\.im|'
                        'q\.gs|is\.gd|po\.st|bc\.vc|twitthis\.com|u\.to|j\.mp|buzurl\.com|cutt\.us|u\.bb|yourls\.org|'
                        'x\.co|prettylinkpro\.com|scrnch\.me|filoops\.info|vzturl\.com|qr\.net|1url\.com|tweez\.me|v\.gd|'
                        'tr\.im|link\.zip\.net',
                        URL)
        if match:
            return 1
        else:
            return 0

    scraped_urls_data['Shortening_Service'] = scraped_urls_data['URL'].apply(lambda x: Shortening_Service(x))

    # Check if ip address is present
    def having_ip_address(URL):
        match = re.search(
            '(([01]?\\d\\d?|2[0-4]\\d|25[0-5])\\.([01]?\\d\\d?|2[0-4]\\d|25[0-5])\\.([01]?\\d\\d?|2[0-4]\\d|25[0-5])\\.'
            '([01]?\\d\\d?|2[0-4]\\d|25[0-5])\\/)|'  # IPv4
            '(([01]?\\d\\d?|2[0-4]\\d|25[0-5])\\.([01]?\\d\\d?|2[0-4]\\d|25[0-5])\\.([01]?\\d\\d?|2[0-4]\\d|25[0-5])\\.'
            '([01]?\\d\\d?|2[0-4]\\d|25[0-5])\\/)|'  # IPv4 with port
            '((0x[0-9a-fA-F]{1,2})\\.(0x[0-9a-fA-F]{1,2})\\.(0x[0-9a-fA-F]{1,2})\\.(0x[0-9a-fA-F]{1,2})\\/)' # IPv4 in hexadecimal
            '(?:[a-fA-F0-9]{1,4}:){7}[a-fA-F0-9]{1,4}|'
            '([0-9]+(?:\.[0-9]+){3}:[0-9]+)|'
            '((?:(?:\d|[01]?\d\d|2[0-4]\d|25[0-5])\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d|\d)(?:\/\d{1,2})?)', URL)  # Ipv6
        if match:
            return 1
        else:
            return 0
        
    scraped_urls_data['Having_ip_address'] = scraped_urls_data['URL'].apply(lambda i: having_ip_address(i))

    # Drop undesired features
    X2 = scraped_urls_data.drop(['URL','Company', 'Title', 'Product_Description', 'Domain'], axis=1)

    # Create Test (validate) data on scraped data
    test_X2 = X2

    # Get total preprocessing runtime
    totPreprocessTime = time.time() - start0
    print("Total request response time: " + str(totPreprocessTime) + " seconds.")


    ## Random Forest Model -- Classification Algorithm
    ## Load model
    malicious_urls_forest_model = pickle.load(open("models/random_forest.pkl", "rb"))

    # Make predictions on scraped data
    sraped_urls_pred = malicious_urls_forest_model.predict(test_X2)

    # Add prediction column
    test_X2['Prediction'] = sraped_urls_pred
    print(test_X2.head(5))


    ## Results
    # Benign/Defacement/Phishing/Malware URLs Target Distribution
    temp = test_X2['Prediction'].value_counts()
    print(temp)

    # Find rows with malicious classification (Prediction values 1, 2, 3,)
    malicious_rows = test_X2[test_X2['Prediction'].isin([0, 1, 2, 3])]

    # Map to the original dataset
    malicious_urls = pd.merge(scraped_urls_data, malicious_rows, left_index=True, right_index=True)

    # Create dict
    resultDict = dict(zip(malicious_urls['URL'], malicious_urls['Prediction']))
    print(resultDict)

    return resultDict


## Flask
predict_data_bp = Blueprint('predict_data', __name__)

@predict_data_bp.route('/predict', methods=['GET', 'POST'])
def predict():
    # Call the scrape_data function to get the scraped data
    resultDict = predict_data()

    # Pass to template
    return render_template('index.html', predict_data=resultDict)