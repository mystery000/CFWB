from datetime import datetime
import logging
import traceback 
from dateutil.relativedelta import relativedelta

from flask_restful import Resource
from app.models.models import Payments, Subscription, UserSubscription, User

from app.database import SessionLocal
from app.services.logger import get_logger

logger = get_logger(__name__, log_level=logging.DEBUG)


class UserSubscriptionService(Resource):
    
    @staticmethod
    def register_subscription(transaction_id, stripe_customer, stripe_data, user_id, subscription_id):
        try:
            db_session = SessionLocal()
            new_subscription = UserSubscription(
                transaction_id=transaction_id,
                stripe_customer=stripe_customer,
                stripe_data=stripe_data,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                user_id=user_id,
                subscription_id=subscription_id
            )
            db_session.add(new_subscription)
            db_session.commit()
            subscription_id = new_subscription.id
        finally:
            db_session.close()
        return subscription_id
    

    @staticmethod
    def get_subscription_id_by_price_id(price_id):
        db_session = SessionLocal()
        subscription = db_session.query(Subscription).filter(Subscription.price_id == price_id).first()
        subscription_id = subscription.id
        db_session.close()
        return subscription_id
    
    @staticmethod
    def get_all_subscriptions():
        db_session = SessionLocal()
        subscriptions = db_session.query(Subscription).all()
        all_subscription = [subscription.serialize for subscription in subscriptions]
        db_session.close()
        return all_subscription
    
    @staticmethod
    def get_subscriptions_by_user_id(user_id):
        db_session = SessionLocal()
        user_subscription = db_session.query(UserSubscription)\
                .join(User, UserSubscription.user_id == User.id) \
                .filter(UserSubscription.user_id == user_id)\
                .first()
        if user_subscription:
            user_subscription = user_subscription.serialize
        else:
            user_subscription = {}
        db_session.close()
        return user_subscription
    
    @staticmethod
    def get_payments_by_user_id(user_id):
        db_session = SessionLocal()
        payments = db_session.query(Payments)\
                .join(User, Payments.user_id == User.id) \
                .filter(Payments.user_id == user_id)\
                .all()
        payments = [payment.serialize for payment in payments]
        db_session.close()
        return payments
    
    @staticmethod
    def insert_user_subscription(expiry, user_id, subscription_id=None, last_payment=None):
        try:
            db_session = SessionLocal()
            expiry =  datetime.now() + relativedelta(months=1)
            existing_user_subscription = db_session.query(UserSubscription)\
                .filter(UserSubscription.user_id == user_id)\
                .first()
            if existing_user_subscription:
                existing_user_subscription.expiry=expiry
                existing_user_subscription.last_payment=datetime.now() if last_payment is None else last_payment
                existing_user_subscription.updated_at=datetime.now()
                existing_user_subscription.subscription_id=subscription_id if subscription_id else existing_user_subscription.subscription_id
                user_subscription_id = existing_user_subscription.id
            else:
                new_user_subscription = UserSubscription(
                    expiry=expiry,
                    last_payment=datetime.now() if last_payment is None else last_payment,
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                    user_id=user_id,
                    subscription_id=subscription_id
                )
                db_session.add(new_user_subscription)
                user_subscription_id = new_user_subscription.id
            db_session.commit()
        finally:
            db_session.close()
        return user_subscription_id
    
    @staticmethod
    def insert_payments(request_uuid, user_id, status, subscription_id=None):
        try:
            db_session = SessionLocal()
            new_payment = Payments(
                request_uuid=request_uuid,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                status=status,
                user_id=user_id,
                subscription_id=subscription_id
            )
            db_session.add(new_payment)
            db_session.commit()
            payment_id = new_payment.id
        finally:
            db_session.close()
        return payment_id
    
    @staticmethod
    def update_user_subscription(request_uuid,status=None,transaction_id=None,stripe_customer=None, stripe_data=None, user_id=None):
        request_uuid = str(request_uuid)
        try:
            db_session = SessionLocal()
            if transaction_id:
                payments = db_session.query(Payments).filter(Payments.user_id == user_id,
                                                             Payments.transaction_id.is_(None)).first()
                payments.transaction_id = transaction_id if transaction_id else payments.transaction_id
            else:
                payments = db_session.query(Payments).filter(Payments.request_uuid == request_uuid)\
                            .filter(Payments.status == 'Initiated')\
                            .first()
                payments.status = status if status else payments.status
                payments.stripe_customer = stripe_customer if stripe_customer else payments.stripe_customer
                payments.stripe_data = stripe_data if stripe_data else payments.stripe_data
            payments.updated_at = datetime.now()
            db_session.commit()
            return True
        except Exception as e:
            return False
        finally:
            db_session.close()

    @staticmethod
    def update_subscription(user_id,subscription_id):
        try:
            db_session = SessionLocal()
            user_subscription = db_session.query(UserSubscription).filter(UserSubscription.user_id == user_id).first()
            user_subscription.subscription_id = subscription_id
            user_subscription.updated_at = datetime.now()
            db_session.commit()
            return True
        except Exception as e:
            logger.error(e)
            logger.error(traceback.format_exc())

    @staticmethod
    def update_payments(user_id,subscription_id=None):
        try:
            db_session = SessionLocal()
            payments = db_session.query(Payments).filter(Payments.user_id == user_id,
                                                         Payments.status == 'complete',
                                                         Payments.subscription_id.is_(None)).first()
            payments.subscription_id = subscription_id if subscription_id else payments.subscription_id
            payments.updated_at = datetime.now()
            db_session.commit()
            return True
        except Exception as e:
            logger.error(e)
            logger.error(traceback.format_exc())

    @staticmethod
    def create_failed_transaction(request_uuid,status,transaction_id,stripe_customer, stripe_data, user_id, subscription_id):
        request_uuid = str(request_uuid)
        try:
            db_session = SessionLocal()
            payments = Payments(
                request_uuid=request_uuid,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                status=status,
                transaction_id=transaction_id,
                stripe_customer=stripe_customer,
                stripe_data=stripe_data,
                user_id=user_id,
                subscription_id=subscription_id
            )
            db_session.add(payments)
            db_session.commit()
            return True
        except Exception as e:
            return False
        finally:
            db_session.close()


    @staticmethod
    def get_payment_by_customer_email(email):
        try:
            db_session = SessionLocal()
            payment = db_session.query(Payments) \
                        .join(User, Payments.user_id == User.id) \
                        .filter(User.email == email)\
                        .first()
            return payment.request_uuid
        finally:
            db_session.close()

    @staticmethod
    def get_subscription_by_priceid(price_id):
        try:
            db_session = SessionLocal()
            subscription = db_session.query(Subscription).filter(Subscription.price_id == price_id).first()
            return subscription
        finally:
            db_session.close()