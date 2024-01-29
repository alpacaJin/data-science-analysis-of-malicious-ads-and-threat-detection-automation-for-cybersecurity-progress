# Libraries
from flask import Flask, render_template
from scraper.scrape_data import scrape_data_bp
from predict.predict_data import predict_data_bp

app = Flask(__name__)

# Blueprints
app.register_blueprint(scrape_data_bp)
app.register_blueprint(predict_data_bp)

@app.route('/')
def home():  
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)