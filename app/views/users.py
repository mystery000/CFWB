import os

from flask_restful import Resource, reqparse
from app.models.models import User
from app.database import db
from flask import request
from app.services.user_service import UserService
from botocore.exceptions import ClientError
import boto3
import hashlib
import hmac
import base64
import requests

class Users(Resource):

    @staticmethod
    def compute_secret_hash(username, client_id, client_secret):
        message = username + client_id
        dig = hmac.new(str(client_secret).encode('utf-8'),
                    msg=str(message).encode('utf-8'), digestmod=hashlib.sha256).digest()
        return base64.b64encode(dig).decode()
    

    def post(self):
        data = request.get_json(force=True)
        first_name = data['first_name']
        last_name = data['last_name']
        email = data['email']
        password = data['password']
        confirm_password = data['confirm_password']

        if password != confirm_password:
            return {'message': 'Incorrect password and confirm password'}, 400

        if not email or not first_name or not last_name or not password or not confirm_password:
            return {'message': 'All fields are required'}, 400

        user_service = UserService()
        is_existing_user = user_service.existing_user(data['email'])
        if is_existing_user:
            return {'message': 'User already exists'}, 400
        
        user_pool_id = os.getenv('USER_POOL_ID') #ss
        client_id = os.getenv('COGNITO_CLIENT_ID')
        client_secret = os.getenv('COGNITO_CLIENT_SECRET')
        cognito_client = boto3.client('cognito-idp', region_name=os.getenv('AWS_REGION'))
        secret_hash = self.compute_secret_hash(email, client_id, client_secret)
        try:
            response = cognito_client.sign_up(
                ClientId=client_id,
                Username=email,
                Password=password,
                SecretHash=secret_hash,
                UserAttributes=[
                    {'Name': 'email', 'Value': email}
                ]
            )
        except ClientError as e:
            if e.response['Error']['Code'] == 'UsernameExistsException' or e.response['Error']['Code'] == 'AliasExistsException':
                print("User already exists. Please choose a different username or email.")
            else:
                print(f"Error: {str(e)}")

    @staticmethod
    def create_or_update_user(data):
        user_service = UserService()
        user = user_service.upsert_user(data)
        return user, 201


class DeleteUserData(Resource):
    def delete(self, scan_uuid):
        user_service = UserService()
        message, status = user_service.delete_user_data(scan_uuid)
        return message, status