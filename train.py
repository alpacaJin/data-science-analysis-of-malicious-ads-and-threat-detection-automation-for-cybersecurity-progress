## Libraries
# Base
import pandas as pd, re, time
from tld import get_tld
from urllib.parse import urlparse
# Modeling
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
# Export
import pickle

# Path of file
malicious_urls_file_path = "kaggle/Malicious_URLs_dataset.csv"
malicious_urls_data = pd.read_csv(malicious_urls_file_path)

start0 = time.time()

## Data Preprocessing -- Check missing data, Omit (www.), Feature extraction, & Split into train/test
malicious_urls_data.isnull().sum()

# Omit (www.)
malicious_urls_data['URL'] = malicious_urls_data['URL'].replace('www.', '', regex = True)

# Further Identification
rem = {"Category": {"benign": 0, "defacement": 1, "phishing": 2, "malware": 3}}
malicious_urls_data['Category'] = malicious_urls_data['Type']
malicious_urls_data = malicious_urls_data.replace(rem)

# Feature Engineering -- URL length, Domain, Symbols
malicious_urls_data['URL_Len'] = malicious_urls_data['URL'].apply(lambda x: len(str(x)))

def process_tld(URL):
    try:
        res = get_tld(URL, as_object = True, fail_silently = False, fix_protocol = True)
        pri_domain= res.parsed_url.netloc
    except :
        pri_domain= None
    return pri_domain

malicious_urls_data["Domain"] = malicious_urls_data['URL'].apply(lambda i: process_tld(i))

# Features
feature = ['@','?','-','=','.','#','%','+','$','!','*',',','//']
for a in feature:
    malicious_urls_data[a] = malicious_urls_data['URL'].apply(lambda i: i.count(a))

# Abnormal
def abnormal_url(URL):
    hostname = urlparse(URL).hostname
    hostname = str(hostname)
    match = re.search(hostname, URL)
    if match:
        return 1
    else:
        return 0
    
malicious_urls_data['Abnormal_url'] = malicious_urls_data['URL'].apply(lambda i: abnormal_url(i))

# HTTP Presence
def httpSecure(URL):
    htp = urlparse(URL).scheme
    match = str(htp)
    if match=='https':
        return 1
    else:
        return 0
    
malicious_urls_data['Https'] = malicious_urls_data['URL'].apply(lambda i: httpSecure(i))

# Count number of digits
def digit_count(URL):
    digits = 0
    for i in URL:
        if i.isnumeric():
            digits = digits + 1
    return digits

malicious_urls_data['Digits'] = malicious_urls_data['URL'].apply(lambda i: digit_count(i))

# Count number of letter characters
def letter_count(URL):
    letters = 0
    for i in URL:
        if i.isalpha():
            letters = letters + 1
    return letters

malicious_urls_data['Letters']= malicious_urls_data['URL'].apply(lambda i: letter_count(i))

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
    
malicious_urls_data['Shortening_Service'] = malicious_urls_data['URL'].apply(lambda x: Shortening_Service(x))

# Check whether ip address is present
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
    
malicious_urls_data['Having_ip_address'] = malicious_urls_data['URL'].apply(lambda i: having_ip_address(i))

# Get total preprocessing runtime
totPreprocessTime = time.time() - start0
print("Total request response time: " + str(totPreprocessTime) + " seconds.")
print(malicious_urls_data.head(5))


# X, Y objects
X = malicious_urls_data.drop(['URL','Type','Category','Domain'], axis=1)
y = malicious_urls_data['Category']

# Set "Category" from object ot multiclass
y = y.astype('int')

# Split into Train & Test (validate) data -- 70-30 distribution
train_X, test_X, train_y, test_y = train_test_split(X, y, test_size = 0.2, random_state = 42)

print(f"No. of training sets: {train_X.shape[0]}")
print(f"No. of testing sets: {test_X.shape[0]}")


## Random Forest Model -- Classification Algorithm
start1 = time.time()
malicious_urls_forest_model = RandomForestClassifier(random_state = 42)

# Fit the model w/ training data + Make predictions
malicious_urls_forest_model.fit(train_X, train_y)
malicious_urls_pred2 = malicious_urls_forest_model.predict(test_X)

# Display accuracy score of model
acc_score2 = accuracy_score(test_y, malicious_urls_pred2)
acc_perc2 = acc_score2 * 100
print(f"Accuracy score of Random Forest Model: {acc_perc2}%")

# Get total model runtime
totModelTime = time.time() - start1
print("Total request response time: " + str(totModelTime) + " seconds.")


## Pickle
pickle.dump(malicious_urls_forest_model, open("models/random_forest.pkl", "wb"))


## Output
# Total request response time: 74.00511121749878 seconds.
#                                                  URL        Type  Category  ...  Letters Shortening_Service  Having_ip_address    
# 0                                   br-icloud.com.br    phishing         2  ...       13                  0                  0    
# 1                mp3raid.com/music/krizz_kaliko.html      benign         0  ...       29                  0                  0    
# 2                    bopsecrets.org/rexroth/cr/1.htm      benign         0  ...       25                  0                  0    
# 3  http://garage-pirenne.be/index.php?option=com_...  defacement         1  ...       60                  0                  0    
# 4  http://adventure-nicaragua.net/index.php?optio...  defacement         1  ...      199                  0                  0    

# [5 rows x 24 columns]
# No. of training sets: 520952
# No. of testing sets: 130239
# Accuracy score of Random Forest Model: 91.43267377667212%
# Total request response time: 75.90915298461914 seconds.