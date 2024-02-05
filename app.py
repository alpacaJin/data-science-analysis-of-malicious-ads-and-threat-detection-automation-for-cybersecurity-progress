# Libraries
from flask import Flask, render_template, jsonify
from scraper.scrape_data import scrape_data_bp
from predict.predict_data import predict_data_bp
import os, csv

app = Flask(__name__)

# Blueprints
app.register_blueprint(scrape_data_bp)
app.register_blueprint(predict_data_bp)

@app.route('/')
def home():  
    return render_template('index.html')

@app.route('/data')
def data():
    csv_file_path = os.path.join(app.static_folder, 'company_locality.csv')
    company_locality = []
    
    # Open the CSV file and read its contents
    with open(csv_file_path, mode='r', encoding='utf-8') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        
        # Convert each row of the CSV file into a dictionary and append to the list
        for row in csv_reader:
            company_locality.append(row)
    
    # Return the data as JSON
    return jsonify(company_locality)

if __name__ == '__main__':
    app.run(debug=True)