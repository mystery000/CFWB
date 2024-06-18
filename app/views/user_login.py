import os
import jwt
import json
import requests
import traceback
from flask import request
from flask_restful import Resource
from app.views.users import Users
from app.jwtutil import create_jwt_token
from app.services.logger import get_logger
from app.services.user_service import UserService
from urllib.parse import urlparse, parse_qs

logger = get_logger(__name__)

class UserLogin(Resource):

    def post(self):
        email = request.json['email']
        user_service = UserService()
        user = user_service.existing_user(email)
        if not user:
            return {'message': 'User does not exist'}, 400

        is_authenticated_user = user_service.verify_password(
            request.json['password'],
            user.password
        )

        if not is_authenticated_user:
            return {'message': 'Incorrect password'}, 400
        
        email = user.email
        token_data = {'email': email}
        jwt_token = create_jwt_token(token_data)
        return {"user_id":user.id, 
                "email": email, 
                "first_name": user.first_name, 
                "last_name": user.last_name,
                "token": jwt_token}, 200
    
    def get(self, user_id):
        print(request)
        return "hello"
    
class Callback(Resource):

    def get(self):
        try:
            client_id = os.getenv('COGNITO_CLIENT_ID')
            client_secret = os.getenv('COGNITO_CLIENT_SECRET')
            redirect_uri = os.getenv('COGNITO_REDIRECT_URI')
            user_pool_url = os.getenv('USER_POOL_URL')

            parsed_url = urlparse(request.url)
            query_params = parse_qs(parsed_url.query)

            authorization_code = query_params.get('code')[0]
            token_url = f'{user_pool_url}/oauth2/token'

            token_params = {
                'grant_type': 'authorization_code',
                'code': authorization_code,
                'redirect_uri': redirect_uri,
                'client_id': client_id,
                'client_secret': client_secret
            }

            headers = {
                'Content-Type': 'application/x-www-form-urlencoded'
            }

            encoded_params = '&'.join([f'{key}={value}' for key, value in token_params.items()])

            response = requests.post(token_url, data=encoded_params, headers=headers)
            response = json.loads(response.content)
            
            cognito_data = jwt.decode(response['id_token'], algorithms=['RS256'], options={"verify_signature": False}, verify=False)
            email = cognito_data.get('email')
            first_name = cognito_data.get('given_name')
            last_name = cognito_data.get('family_name')
            profile_picture = cognito_data.get('profile')
            id_token = response['id_token']
            access_token = response['access_token']
            refresh_token = response['refresh_token']

            users = Users()
            created_user, status = users.create_or_update_user({'email': email, 'first_name': first_name, 'last_name': last_name})

            return {
                    "user": created_user,
                    "profile": profile_picture,
                    "id_token": id_token,
                    "access_token": access_token,
                    "refresh_token": refresh_token
                    }, 200
        except Exception as e:
            logger.info(f"{e}")
            logger.info(traceback.format_exc())
            return {'message': str(e)}, 400