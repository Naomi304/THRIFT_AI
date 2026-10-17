import os
from flask import Flask, render_template, request, flash, jsonify
import pandas as pd
import joblib
import logging
from concurrent.futures import ThreadPoolExecutor
import traceback

# Import API functions
from apis.amazon_api import get_amazon_data
from apis.craigslist_api import get_craigslist_data
from apis.kijiji_api import get_kijiji_data
from apis.ebay_api import get_ebay_data
from apis.google_api import get_google_data
from utils import validate_input, sanitize_input, is_na

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev-key-change-in-production')

# Global variables for models
model = None
label_encoder = None
condition_encoder = None

def load_models():
    """Load ML models with error handling"""
    global model, label_encoder, condition_encoder
    try:
        model = joblib.load('price_predictor_model.pkl')
        label_encoder = joblib.load('label_encoder.pkl')
        condition_encoder = joblib.load('condition_encoder.pkl')
        logger.info("ML models loaded successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to load ML models: {e}")
        return False


def _match_class(encoder, value):
    """Case-insensitively map a user-entered value to a known encoder class.

    Returns the canonical class string if found, else None. This lets users
    type "Hoodie"/"NIKE" and still match the model's "hoodie"/"Nike" classes.
    """
    if value is None:
        return None
    target = str(value).strip().lower()
    for cls in encoder.classes_:
        if str(cls).strip().lower() == target:
            return cls
    return None

# Load models on startup
models_loaded = load_models()

@app.route('/')
def home():
    return render_template('input.html')  # This is the search form where users enter their input

def get_ml_prediction(brand, item_type, condition):
    """Get ML price prediction with error handling.

    The model is trained on Brand + Item Type + Condition (from real
    marketplace sold data). Brand/item lookups are case-insensitive; an
    unknown brand or item type returns a friendly message.
    """
    if not models_loaded:
        return None, "ML models not available"

    if is_na(brand) or is_na(item_type):
        return None, "AI prediction skipped: brand and item type are required (one or more marked N/A)"

    # Case-insensitively match the user's text to known model categories.
    brand_cls = _match_class(label_encoder, brand)
    item_cls = _match_class(label_encoder, item_type)

    unknown = []
    if brand_cls is None:
        unknown.append(f"brand '{brand}'")
    if item_cls is None:
        unknown.append(f"item type '{item_type}'")
    if unknown:
        known_brands = "Nike, Adidas, H&M, Zara, Gap, Levi's, Tommy Hilfiger"
        return None, (
            f"The model hasn't seen {', '.join(unknown)} yet. "
            f"Try a trained brand (e.g. {known_brands}) and a common item type."
        )

    # Condition: fall back to 'used' for N/A or anything the model doesn't know.
    condition_cls = _match_class(condition_encoder, condition) \
        or _match_class(condition_encoder, "used")
    if condition_cls is None:
        # Extremely unlikely (model always has at least one condition class).
        condition_cls = condition_encoder.classes_[0]

    try:
        brand_encoded = label_encoder.transform([brand_cls])[0]
        item_type_encoded = label_encoder.transform([item_cls])[0]
        condition_encoded = condition_encoder.transform([condition_cls])[0]

        user_input = pd.DataFrame(
            [[brand_encoded, item_type_encoded, condition_encoded]],
            columns=['Brand', 'Item Type', 'Condition']
        )
        predicted_price = model.predict(user_input)[0]
        return round(predicted_price, 2), None

    except Exception as e:
        logger.error(f"ML prediction error: {e}")
        return None, "Prediction temporarily unavailable"

def fetch_api_data(brand, item_type, size, color, material, condition):
    """Fetch data from all APIs concurrently"""

    results = {
        'amazon': {'status': 'error', 'data': None, 'message': 'Not fetched'},
        'craigslist': {'status': 'error', 'data': None, 'message': 'Not fetched'},
        'kijiji': {'status': 'error', 'data': None, 'message': 'Not fetched'},
        'ebay': {'status': 'error', 'data': None, 'message': 'Not fetched'},
        'google': {'status': 'error', 'data': None, 'message': 'Not fetched'}
    }

    def is_success(data):
        if not data:
            return False
        status = str(data.get("status", "")).lower()
        return status == "success"

    def get_message(data):
        if not data:
            return "No data returned"
        return data.get("message") or data.get("Message") or data.get("error") or "API error"

    def fetch_amazon():
        try:
            data = get_amazon_data(brand, item_type, size, color, material, condition)

            if is_success(data):
                results['amazon'] = {
                    'status': 'success',
                    'data': data,
                    'message': data.get('message', 'Data retrieved')
                }
            else:
                results['amazon'] = {
                    'status': 'error',
                    'data': data,
                    'message': get_message(data)
                }

        except Exception as e:
            results['amazon'] = {
                'status': 'error',
                'data': None,
                'message': str(e)
            }

    def fetch_craigslist():
        try:
            data = get_craigslist_data(brand, item_type, size, color, material, condition)

            if is_success(data):
                results['craigslist'] = {
                    'status': 'success',
                    'data': data,
                    'message': data.get('message', 'Data retrieved')
                }
            else:
                results['craigslist'] = {
                    'status': 'error',
                    'data': data,
                    'message': get_message(data)
                }

        except Exception as e:
            results['craigslist'] = {
                'status': 'error',
                'data': None,
                'message': str(e)
            }

    def fetch_ebay():
        try:
            data = get_ebay_data(brand, item_type, size, color, material, condition)

            if is_success(data):
                results['ebay'] = {
                    'status': 'success',
                    'data': data,
                    'message': data.get('message', 'Data retrieved')
                }
            else:
                results['ebay'] = {
                    'status': 'error',
                    'data': data,
                    'message': get_message(data)
                }

        except Exception as e:
            results['ebay'] = {
                'status': 'error',
                'data': None,
                'message': str(e)
            }

    def fetch_kijiji():
        try:
            data = get_kijiji_data(brand, item_type, size, color, material, condition)

            if is_success(data):
                results['kijiji'] = {
                    'status': 'success',
                    'data': data,
                    'message': data.get('message', 'Data retrieved')
                }
            else:
                results['kijiji'] = {
                    'status': 'error',
                    'data': data,
                    'message': get_message(data)
                }

        except Exception as e:
            results['kijiji'] = {
                'status': 'error',
                'data': None,
                'message': str(e)
            }

    def fetch_google():
        try:
            data = get_google_data(brand, item_type, size, color, material, condition)

            if is_success(data):
                results['google'] = {
                    'status': 'success',
                    'data': data,
                    'message': data.get('message', 'Data retrieved')
                }
            else:
                results['google'] = {
                    'status': 'error',
                    'data': data,
                    'message': get_message(data)
                }

        except Exception as e:
            results['google'] = {
                'status': 'error',
                'data': None,
                'message': str(e)
            }

    with ThreadPoolExecutor(max_workers=5) as executor:
        executor.submit(fetch_amazon)
        executor.submit(fetch_craigslist)
        executor.submit(fetch_kijiji)
        executor.submit(fetch_ebay)
        executor.submit(fetch_google)

    return results

#workshop
# If the price ratio is 0.7 or less, it means the user's price is 30% or more lower than the predicted price: excellent deal
# If the price ratio is between 0.71 and 0.85, the user's price is still a good deal, but not as much of a discount: good deal
# If the price ratio is between 0.86 and 1.15, the user's price is within 15% of the predicted price: fair price
# If the price ratio is between 1.16 and 1.3, the user's price is slightly high, but not too bad: slightly high
# If the price ratio is above 1.3, the user's price is more than 30% higher than the predicted price: overpriced

def determine_deal_quality(predicted_price, market_data):
    """Determine if the user is getting a good deal"""
    if not predicted_price:
        return "Unable to determine", "insufficient-data"
    

    user_price_input = request.form.get('user_price')
    
    if not user_price_input:
        return "Enter your price to compare", "no-price"
    
    try:
        user_price = float(user_price_input)
        price_ratio = user_price / predicted_price
        
        if price_ratio <= 0.7:
            return "Excellent Deal! 🎉", "excellent"
        elif price_ratio <= 0.85:
            return "Good Deal! 👍", "good"
        elif price_ratio <= 1.15:
            return "Fair Price", "fair"
        elif price_ratio <= 1.3:
            return "Slightly High", "high"
        else:
            return "Overpriced ⚠️", "overpriced"
            
    except (ValueError, TypeError):
        return "Invalid price entered", "invalid"

@app.route('/search', methods=['POST'])
def search():
    try:
        # Get and sanitize user input
        form_data = {
            'brand': sanitize_input(request.form.get('brand', '')),
            'item_type': sanitize_input(request.form.get('item_type', '')),
            'size': sanitize_input(request.form.get('size', '')),
            'color': sanitize_input(request.form.get('color', '')),
            'material': sanitize_input(request.form.get('material', '')),
            'condition': request.form.get('condition', 'used'),
            'user_price': request.form.get('user_price', '')
        }
        
        # Validate input
        is_valid, error_message = validate_input(form_data)
        if not is_valid:
            flash(error_message, 'error')
            return render_template('input.html')
        
        # Extract clean values
        brand = form_data['brand']
        item_type = form_data['item_type']
        size = form_data['size'] or 'M'  # Default size
        color = form_data['color']
        material = form_data['material']
        condition = form_data['condition']
        
        # Get ML prediction (model uses brand + item type + condition)
        predicted_price, prediction_error = get_ml_prediction(brand, item_type, condition)

        # Fetch market data from APIs — treat N/A as absent so we don't literally
        # search marketplaces for the string "N/A".
        def _drop_na(v):
            return "" if is_na(v) else v

        market_data = fetch_api_data(
            _drop_na(brand),
            _drop_na(item_type),
            _drop_na(size),
            _drop_na(color),
            _drop_na(material),
            _drop_na(condition) or "used",
        )
        logger.info(f"Fetching market data for {brand} {item_type}")
        
        # Determine deal quality
        deal_assessment, deal_class = determine_deal_quality(predicted_price, market_data)
        
        # Prepare results
        results = {
            'search_params': {
                'brand': brand,
                'item_type': item_type,
                'size': size,
                'color': color,
                'material': material,
                'condition': condition
            },
            'predicted_price': predicted_price,
            'prediction_error': prediction_error,
            'market_data': market_data,
            'deal_assessment': deal_assessment,
            'deal_class': deal_class
        }
        
        return render_template('results.html', **results)
        
    except Exception as e:
        logger.error(f"Search error: {e}")
        logger.error(traceback.format_exc())
        flash('An error occurred during search. Please try again.', 'error')
        return render_template('input.html')

if __name__ == '__main__':
    app.run(debug=True)
