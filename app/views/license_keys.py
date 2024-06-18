import json
import logging
from flask import request
from flask_restful import Resource
from app.jwtutil import auth_required

from app.services.license_keys_service import LicenseKeysService
from app.services.user_service import UserService

from app.services.logger import get_logger

logger = get_logger(__name__, log_level=logging.DEBUG)

class GenerateLicenseKey(Resource):
    
    @auth_required
    def post(self):
        logger.info(request)
        try:
            email = request.cf.get('user').get('email')
            license_service = LicenseKeysService()
            user_service = UserService()
            is_user_exists = user_service.existing_user(email)
            if not is_user_exists:
                return {'message': 'User does not exist'}, 400
            if not email:
                return {'message': 'Email is required'}, 400
            
            is_existing_key = license_service.existing_user_license_key(email)
            if is_existing_key:
                return {'success': False, "data": {'message': "User is already subscribed"}}, 200
            license_key = license_service.generate_subscription_key(email)
            user_subscription_id = user_service.get_user_subscription_id(email)
            license_service.store_license_key(license_key, user_subscription_id)
            return {'success': True, "data": {'message': license_key, "email": email}}, 200
        except Exception as e:
            logger.debug(e)
            return {'success': False,'data': {"message": str(e)}}, 500

class RetrieveLicenseKey(Resource):

    @auth_required
    def get(self):
        """The function would retrieve the existing license"""
        logger.info(request)
        try:
            license_service = LicenseKeysService()
            user_email = request.cf.get('user').get('email')
            license_key = license_service.existing_user_license_key(user_email)
            if not license_key:
                return {'success': False, "data": {'message': "User is not subscribed"}}, 200
            data = {
                'license_key': license_key,
                'email': user_email
            }
            return {'success': True, "data": data}, 200
        except Exception as e:
            logger.debug(e)
            return {'success': False,'data': {"message": str(e)}}, 500
        
    @auth_required
    def post(self):
        """The function would revoke and regenerate new key. 
        Considering if he lost license key is also covered below"""
        logger.info(request)
        try:
            license_service = LicenseKeysService()
            user_email = request.cf.get('user').get('email')
            license_key = license_service.existing_user_license_key(user_email)
            if not license_key:
                return {'success': False, "data": {'message': "User is not subscribed"}}, 200
            
            new_license_key = license_service.revoke_and_regenerate_license_key(license_key, 
                                                                                user_email)
            data = {
                'license_key': new_license_key,
                'email': user_email
            }
            return {'success': True, "data": data}, 200
        except Exception as e:
            logger.debug(str(e))
            return {'success': False,'data': {"message": str(e)}}, 500
        
        
class AuthenticateLicenseKey(Resource):
    def post(self):
        logger.info(request)
        try:
            data = json.loads(request.data)
            email = data['email']
            requested_license_key = data['license_key']
            license_service = LicenseKeysService()
            user_service = UserService()
            is_user_exists = user_service.existing_user(email)
            if not email:
                return {'message': 'Email is required'}, 400
            if not is_user_exists:
                return {'message': 'User does not exist'}, 400
            license_key = license_service.existing_user_license_key(email)
            if not license_key:
                return {'success': False, "data": {'message': "User isnot subscribed"}}, 200

            user_data = user_service.get_user_by_email(email)

            is_authenticated_key, status = license_service.authenticate_license_key(email, requested_license_key)
            if status != 200:
                return {'success': False, 'data': is_authenticated_key}, status
            else:
                return {'success': True, 'data': is_authenticated_key, 'user_data': user_data}, status
        except Exception as e:
            logger.debug(str(e))
            return {'success': False,'data': {"message": str(e)}}, 500

class RecurringLicenseKeyCheck(Resource):
    def post(self):
        data = json.loads(request.data)
        requested_license_key = data['license_key']
        license_service = LicenseKeysService()
        is_authenticated_key, status = license_service.check_license_key_availability(requested_license_key)
        if status != 200:
            return {'success': False, 'data': is_authenticated_key}, status
        else:
            return {'success': True, 'data': is_authenticated_key}, status
