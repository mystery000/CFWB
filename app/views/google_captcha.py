import os 
import requests
from dotenv import load_dotenv

from flask import request
from flask_restful import Resource

load_dotenv()

class VerifyCaptcha(Resource):
    def post(self):
        secret_key = os.getenv('RECAPTCHA_SECRET_SITE_KEY')
        token = request.json.get('token')

        # Make a request to Google reCAPTCHA API for verification
        response = requests.post('https://www.google.com/recaptcha/api/siteverify', data={
            'secret': secret_key,
            'response': token
        })

        data = response.json()

        if data['success']:
            return {'success': True, 'message': 'reCAPTCHA verification successful'}, 200
        else:
            return {'success': False, 'message': 'reCAPTCHA verification failed'}, 401
