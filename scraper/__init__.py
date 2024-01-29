from flask import Blueprint

# Create a Flask Blueprint for the scraper package
scrape_data_bp = Blueprint('scrape_data', __name__)

# Import views from the scraper package
from . import scrape_data