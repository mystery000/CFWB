import os
import requests
from datetime import datetime
from flask_restful import Resource
from passlib.context import CryptContext

from app.database import SessionLocal
from app.models.models import User, UserSubscription

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserService(Resource):
        
    # @staticmethod
    # def hash_password(password):
    #     return hashlib.sha256(password.encode()).hexdigest()

    @staticmethod
    def existing_user(email):
        db_session = SessionLocal()
        user = db_session.query(User).filter(User.email == email).first()
        if user:
            return True
        else:
            return False

    @staticmethod
    def get_password_hash(password):
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password, hashed_password):
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def search_user_by_id(id):
        db_session = SessionLocal()
        user = db_session.query(User).filter(User.id == id).first()
        if user:
            return user
        else:
            return False
        
    @staticmethod
    def get_user_by_email(email):
        db_session = SessionLocal()
        user = db_session.query(User).filter(User.email == email).first()
        if user:
            return user.serialize
        else:
            return False
        
    def create_user(self, data):
        data['password'] = self.hash_password(data['password'])
        db_session = SessionLocal()
        new_user = User(
            first_name=data['first_name'],
            last_name=data['last_name'],
            email=data['email'],
            password=data['password'],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        db_session.add(new_user)
        db_session.commit()
        db_session.close()                

        return {'message': 'User created successfully'}, 201

    @staticmethod
    def upsert_user(data):
        try:
            db_session = SessionLocal()
            user = db_session.query(User).filter(User.email == data['email']).first()
            if user:
                user.first_name = data.get('first_name')
                user.last_name = data.get('last_name')
                user.email = data.get('email')
                user.updated_at = datetime.now()
                db_session.add(user)
                db_session.commit()
                return user.serialize
            else:
                new_user = User(
                    first_name=data.get('first_name'),
                    last_name=data.get('last_name'),
                    email=data.get('email'),
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                db_session.add(new_user)
                db_session.commit()
                return new_user.serialize
        finally:
            db_session.close()

    @staticmethod
    def delete_user_data(scan_uuid):
        try:
            mutation = """
                mutation($scanUuid: String!)  {
                deleteScanData(scan_uuid: $scanUuid) {
                    message
                    success
                }
                }
            """
            variables = {
                'scanUuid': scan_uuid
            }
            graphql_url = os.getenv('GRAPHQL_URL', 'http://localhost:3000/v1/graphql')
            response = requests.post(graphql_url, json={'query': mutation, 'variables': variables})
            if response.status_code == 200:
                result = response.json()
                return {'data': result['data']['deleteScanData']}, 200
            else:
                return {'data': 'Failed to delete user data'}, 400
        except Exception as e:
            return {'data': str(e)}, 500
        
    @staticmethod
    def get_user_id_by_email(email):
        db_session = SessionLocal()
        user = db_session.query(User).filter(User.email == email).first()
        if user:
            return user.id
        else:
            return False
        
    @staticmethod
    def get_user_subscription_id(email):
        db_session = SessionLocal()
        user_subscription = db_session.query(UserSubscription).join(User, UserSubscription.user_id == User.id)\
            .filter(User.email == email).first()
        if user_subscription:
            return user_subscription.id
        else:
            return False