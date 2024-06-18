import os
import json
import uuid
import stripe
import traceback
from flask import request
from flask_restful import Resource
from app.jwtutil import auth_required
from app.services.logger import get_logger
from app.services.user_service import UserService
from app.services.subscription_service import UserSubscriptionService

logger = get_logger(__name__)

class UserSubsciption(Resource):
    @auth_required
    def post(self):
        logger.info(request)
        try:
            stripe.api_key = os.getenv('STRIPE_API_KEY')
            subscription_service = UserSubscriptionService()
            user_service = UserService()
            data = json.loads(request.data)
            price_id = data['price_id']
            user_email = data['user_email']
            request_uuid = str(uuid.uuid4())
            session = stripe.checkout.Session.create(
            success_url=os.getenv('STRIPE_SUCCESS_URL'),
            cancel_url=os.getenv('STRIPE_CANCEL_URL'),
            mode='subscription',
            line_items=[{
                'price': price_id,
                # For metered billing, do not pass quantity
                'quantity': 1
            }],
            client_reference_id=request_uuid,
            customer_email=user_email
            )
            user_id = user_service.get_user_id_by_email(user_email)
            user_subscription = subscription_service.insert_user_subscription(expiry=session['expires_at'],
                                                                            user_id=user_id,
                                                                            subscription_id=None,
                                                                            last_payment=None)
            payments = subscription_service.insert_payments(request_uuid, user_id, status="Initiated")
            return {
                'success': True,
                'payment_url': session['url'],
                "user_email": user_email,
                "session_id": session['id'],
                "request_uuid": request_uuid
            }
        except Exception as e:
            logger.info(f"{e}")
            logger.info(traceback.format_exc())
            return {
                'success': False,
                'message': str(e)
            }

class Subscriptions(Resource):
    @auth_required
    def get(self):
        try:
            logger.info(request)
            subscription_service = UserSubscriptionService()
            subscriptions = subscription_service.get_all_subscriptions()

            return {"data": subscriptions}, 200
        except Exception as e:
            logger.info(f"{e}")
            logger.info(traceback.format_exc())
            return {'data': str(e)}, 500

class FetchUserSubscriptions(Resource):

    @auth_required
    def get(self, user_id):

        try:
            logger.info(request)
            subscription_service = UserSubscriptionService()
            user_subscriptions = subscription_service.get_subscriptions_by_user_id(user_id)
            return {"data": user_subscriptions}, 200
        except Exception as e:
            logger.info(f"{e}")
            logger.info(traceback.format_exc())
            return {'data': str(e)}, 500

class FetchUserPaymentHistory(Resource):

    @auth_required
    def get(self, user_id):
        try:
            subscription_service = UserSubscriptionService()
            payments = subscription_service.get_payments_by_user_id(user_id)
            return {"data": payments}, 200
        except Exception as e:
            return {"data": str(e)}, 500

class StripeSubscriptionCallback(Resource):
    def post(self):
        subscription_service = UserSubscriptionService()
        user_service = UserService()
        stripe.api_key = os.getenv('STRIPE_API_KEY')
        endpoint_secret = os.getenv('STRIPE_ENDPOINT_SECRET')
        logger.error('checking secret')
        print(endpoint_secret)
        if endpoint_secret:
            logger.error("STRIPE_ENDPOINT_SECRET found")
            logger.error(endpoint_secret)
        else:
            logger.error("STRIPE_ENDPOINT_SECRET not found")


        event = None
        payload = request.data
        sig_header = request.headers['STRIPE_SIGNATURE']

        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, endpoint_secret
            )
        except ValueError as e:
            logger.info(e)
            raise e
        except stripe.error.SignatureVerificationError as e:
            logger.info(e)
            raise e

        try:
            # Handle the event
            if event['type'] == 'checkout.session.completed':
                session = event['data']['object']
                # print(session, "checkout.session.completed")
                transaction_id = session['payment_intent']
                stripe_customer = session['customer']
                status = session['status']
                request_uuid = session['client_reference_id']
                subscription_service.update_user_subscription(request_uuid=request_uuid,
                                                                status=status,
                                                                transaction_id=transaction_id,
                                                                stripe_customer=stripe_customer,
                                                                stripe_data=session)
            if event['type'] == 'invoice.payment_succeeded':
                session = event['data']['object']
                transaction_id = session['payment_intent']
                user_email = session['customer_email']
                user_id = user_service.get_user_id_by_email(user_email)
                price_id = session['lines']['data'][0]['plan']['id']
                subscription_id = subscription_service.get_subscription_id_by_price_id(price_id)
                customer_request_uuid = subscription_service.get_payment_by_customer_email(session['customer_email'])
                subscription_service.update_user_subscription(request_uuid=customer_request_uuid,
                                                              transaction_id=transaction_id,
                                                              user_id=user_id)
                subscription_service.update_subscription(user_id, subscription_id)
                subscription_service.update_payments(user_id=user_id,
                                                     subscription_id=subscription_id)
            if event['type'] == 'invoice.payment_failed':
                session = event['data']['object']
                transaction_id = session['payment_intent']
                user_email = session['customer_email']
                user_id = user_service.get_user_id_by_email(user_email)
                price_id = session['lines']['data'][0]['plan']['id']
                subscription_id = subscription_service.get_subscription_id_by_price_id(price_id)

                customer_request_uuid = subscription_service.get_payment_by_customer_email(session['customer_email'])
                subscription_service.create_failed_transaction(request_uuid=customer_request_uuid,
                                                              transaction_id=transaction_id,
                                                              status="failed",
                                                              stripe_data=session,
                                                              stripe_customer=session['customer'],
                                                              user_id=user_id,
                                                              subscription_id=subscription_id)
            # TODO: Cancellation not in scope, will be handled manually
            # if event['type'] == 'subscription_schedule.canceled':
            #     subscription_schedule = event['data']['object']
            #     stripe.Subscription.cancel("sub_1OZryaEbLTf7azJEV88KL13k")
            #     # print("inside canceled", subscription_schedule)

            return {"success": True, "message": "Subscription created successfully"}, 200
        except Exception as e:
            logger.info(e)
            logger.info(traceback.format_exc())
            return {"success": False, "error": str(e)}, 500
