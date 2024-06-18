
import os
import requests
from flask import request
from functools import wraps
from jose import JWTError, jwt
from datetime import datetime,timedelta
from app.database import SessionLocal
from app.models.models import User
from app.services.user_service import UserService

# Secret key for signing and verifying JWT tokens
SECRET_KEY = os.getenv('JWT_SECRET_KEY')
ALGORITHM = "HS256"
EXPIRE_DELTA = 30

# Function to create a JWT token
def create_jwt_token(token_data: dict):
    to_encode = token_data.copy()
    expire = datetime.utcnow() + timedelta(minutes=EXPIRE_DELTA)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt



# Function to decode a JWT token
def decode_token(token: str):
    try:
        payload = jwt.decode(token, algorithms=['RS256'], options={'verify_signature': False})
        return payload.get("email"), 200
    except jwt.ExpiredSignatureError:
        return {"message": "Token has expired"}, 401
    except jwt.JWTError:
        return {"message": "Invalid token"}, 403


COGNITO_USER_POOL_URL = os.getenv('COGNITO_USER_POOL_URL')

def get_token_from_request():
    auth_header = request.headers.get('cf-token')
    return auth_header

def get_cognito_public_key(kid):
    jwks_url = f'{COGNITO_USER_POOL_URL}/.well-known/jwks.json'
    jwks_response = requests.get(jwks_url)

    if jwks_response.status_code == 200:
        jwks = jwks_response.json()['keys']
        for key in jwks:
            if key['kid'] == kid:
                return key
    return None

def validate_access_token(token):
    header = jwt.get_unverified_header(token)
    kid = header.get('kid')

    if kid:
        # Retrieve the public key from Cognito
        public_key = get_cognito_public_key(kid)

        if public_key:
            # Verify the token using the public key
            decoded_token = jwt.decode(
                token,
                public_key,
                algorithms=['RS256'],
                issuer=COGNITO_USER_POOL_URL,
            )
            return decoded_token

    return None

def auth0_login_strategy(user_detail, auth0_token):
    db_session = SessionLocal()
    user = db_session.query(User).filter(User.email == auth0_token).first()
    if user:
        return user.serialize
    else:
        user_service = UserService()
        user = user_service.get_user_id_by_email(user_detail['email'])
        user.auth0_token = auth0_token
        user.updated_at = datetime.utcnow()
        return user

def get_user_information_from_auth0(token):
    user_pool_url = os.getenv('USER_POOL_URL')
    access_token = token

    userinfo_url = f'{user_pool_url}/oauth2/userInfo'

    headers = {
        'Authorization': f'Bearer {access_token}',
    }

    response = requests.get(userinfo_url, headers=headers)
    return response.json()


def auth_required(func):
    def wrapper(*args, **kwargs):
        access_token = get_token_from_request()

        if access_token:
            try:
                decoded_token = validate_access_token(access_token)
                if decoded_token:
                    user_info = get_user_information_from_auth0(access_token)
                    request.cf = {}
                    
                    if not user_info:
                        return {'error': 'Invalid access token'}, 401
                    request.cf['user'] = user_info
                    return func(*args, **kwargs)
                else:
                    return {'error': 'Invalid access token'}, 401
            except Exception as e:
                return {'error': 'Invalid or expired access token'}, 401
        else:
            return {'error': 'Access token is missing'}, 401

    return wrapper