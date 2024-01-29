from flask import Blueprint

# Create a Flask Blueprint for the predict package
predict_data_bp = Blueprint('predict_data', __name__)

# Import views from the predict package
from . import predict_data