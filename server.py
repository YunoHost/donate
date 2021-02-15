#! /usr/bin/env python3.6

"""
server.py
Stripe Sample.
Python 3.6 or newer required.
"""

import stripe
import json
import os

from flask import Flask, render_template, jsonify, request, send_from_directory
from flask_simple_csrf import CSRF
from dotenv import load_dotenv, find_dotenv


# Setup Stripe python client library.
load_dotenv(find_dotenv())

stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
stripe.api_version = os.getenv('STRIPE_API_VERSION')

static_dir = str(os.path.abspath(os.path.join(
    __file__, "..", os.getenv("STATIC_DIR"))))
app = Flask(__name__, static_folder=static_dir,
            static_url_path="", template_folder=static_dir)
CSRF = CSRF(config=os.getenv('CSRF_CONFIG'))
app = CSRF.init_app(app)

@app.before_request
def before_request():
    if 'CSRF_TOKEN' not in session or 'USER_CSRF' not in session:
        session['USER_CSRF'] = random_string(64)
        session['CSRF_TOKEN'] = CSRF.create(session['USER_CSRF'])

@app.route('/', methods=['GET'])
def get_index():
    return render_template('index.html')


@app.route('/config', methods=['GET'])
def get_publishable_key():
    return jsonify({
      'publicKey': os.getenv('STRIPE_PUBLISHABLE_KEY'),
      'name': os.getenv('PROJECT_NAME'),
      'csrf': session['USER_CSRF'],
    })

@app.route('/create-checkout-session', methods=['POST'])
def create_checkout_session():
    data = json.loads(request.data)
    domain_url = os.getenv('DOMAIN')
    try:
        if CSRF.verify(data['user_csrf'], session['CSRF_TOKEN']) is False or
           data['frequency'] not in ['RECURING', 'ONE_TIME'] or
           data['currency'] not in ['EUR', 'USD'] or
           int(data['quantity']) <= 0:
            return jsonify(error="Bad value"), 400

        # Create new Checkout Session for the order
        price = f"{data['frequency']}_{data['currency']}_DONATION"
        mode = "payment" if data['frequency'] == 'ONE_TIME' else "subscription"

        checkout_session = stripe.checkout.Session.create(
            success_url=domain_url +
            "/success.html?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=domain_url + "/canceled.html",
            payment_method_types= ["card"],
            mode=mode,
            line_items=[
                {
                    "price": os.getenv(price),
                    "quantity": data['quantity']
                }
            ]
        )
        return jsonify({'sessionId': checkout_session['id']})
    except Exception as e:
        return jsonify(error=str(e)), 403



if __name__ == '__main__':
    app.run(port=os.getenv('PORT'), debug=os.getenv('DEBUG'))
