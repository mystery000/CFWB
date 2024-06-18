import hashlib
from datetime import datetime

from app.database import SessionLocal
from app.services.user_service import UserService
from app.models.models import LicenseKeysModel, User, UserSubscription


class LicenseKeysService:
    @staticmethod
    def generate_subscription_key(email):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        data_to_hash = f"{timestamp}{email}"
        sha256_hash = hashlib.sha256(data_to_hash.encode()).hexdigest()
        return sha256_hash
    
    @staticmethod
    def store_license_key(license_key, user_subscription_id):
        db_session = SessionLocal()
        license_key = LicenseKeysModel(
            user_license_key=license_key,
            user_subscription_id=user_subscription_id,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        db_session.add(license_key)
        db_session.commit()
        db_session.close()

    @staticmethod
    def existing_user_license_key(email):
        db_session = SessionLocal()
        license_key = db_session.query(LicenseKeysModel)\
            .join(UserSubscription, LicenseKeysModel.user_subscription_id == UserSubscription.id)\
            .join(User, UserSubscription.user_id == User.id)\
            .filter(User.email == email, LicenseKeysModel.is_active == True).first()
        if license_key:
            license_key = license_key.user_license_key
        else:
            license_key = None
        db_session.close()
        return license_key
    
    @staticmethod
    def set_user_license_key_inactive(license_key):
        db_session = SessionLocal()
        license_key = db_session.query(LicenseKeysModel).filter(LicenseKeysModel.user_license_key == license_key).first()
        license_key.is_active = False
        license_key.updated_at = datetime.now()
        db_session.commit()
        db_session.close()

    @staticmethod
    def revoke_and_regenerate_license_key(license_key, email):
        LicenseKeysService.set_user_license_key_inactive(license_key)
        new_license_key = LicenseKeysService.generate_subscription_key(email)
        user_subscription_id = UserService.get_user_subscription_id(email)
        LicenseKeysService.store_license_key(new_license_key, user_subscription_id)
        return new_license_key
    
    @staticmethod
    def authenticate_license_key(email, license_key):
        db_session = SessionLocal()
        in_use_license_key = db_session.query(LicenseKeysModel)\
            .filter(LicenseKeysModel.in_use == True, 
                    LicenseKeysModel.user_license_key == license_key)\
            .first()
        if in_use_license_key:
            return {'message': "The license key is already in use"}, 401
        
        user_license_id = db_session.query(LicenseKeysModel)\
            .join(UserSubscription, LicenseKeysModel.user_subscription_id == UserSubscription.id)\
            .join(User, UserSubscription.user_id == User.id)\
            .filter(User.email == email, LicenseKeysModel.user_license_key == license_key, LicenseKeysModel.is_active == True).first()
        if not user_license_id or (user_license_id.user_license_key != license_key):
            return {'message': "The license key is not valid or deleted"}, 401

        user_license_id.in_use = True
        user_license_id.updated_at = datetime.now()
        db_session.commit()
        db_session.close()
        return {'message': "The license key is valid"}, 200
    
    @staticmethod
    def check_license_key_availability(license_key):
        db_session = SessionLocal()
        user_license_id = db_session.query(LicenseKeysModel)\
            .filter(LicenseKeysModel.user_license_key == license_key, 
                    LicenseKeysModel.is_active == True, 
                    LicenseKeysModel.in_use == True).first()
        if not user_license_id:
            return {'message': "The license key is deleted or already in use."}, 401
        return {'message': "The license key is available"}, 200