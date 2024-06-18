from flask_cors import CORS
from flask_restful import Api
from flask import Blueprint, Flask
from flask_swagger_ui import get_swaggerui_blueprint

from app.services.logger import get_logger
from app.database import configure_database
from app.views.user_login import Callback
from app.views.users import DeleteUserData
from app.views.google_captcha import VerifyCaptcha
from app.views.license_keys import GenerateLicenseKey, RetrieveLicenseKey, AuthenticateLicenseKey, RecurringLicenseKeyCheck
from app.views.subscriptions import FetchUserPaymentHistory, StripeSubscriptionCallback, UserSubsciption, Subscriptions, FetchUserSubscriptions

app = Flask(__name__)
CORS(app)

logger = get_logger(__name__)

# Swagger setting
SWAGGER_URL = "/api/v1/swagger"
API_URL = '/static/swagger.json'
swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL, API_URL, config={'app_name': "User Management APIs"}
)

app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)
configure_database(app)
api = Api(app)

v1_blueprint = Blueprint('v1', __name__, url_prefix='/v1')
api_v1 = Api(v1_blueprint)

# TODO: Login and Register will be with Google and cognito
# api_v1.add_resource(Users, '/users', strict_slashes=False)
# api_v1.add_resource(UserLogin, '/user/login', strict_slashes=False)
@app.route('/v1/ping')
def ping():
    return 'pong'

api_v1.add_resource(Callback, '/callback', strict_slashes=False)
api_v1.add_resource(VerifyCaptcha, '/verify-captcha', strict_slashes=False)
api_v1.add_resource(DeleteUserData, '/delete-user-data/<string:scan_uuid>', strict_slashes=False)
api_v1.add_resource(Subscriptions, '/subscriptions', strict_slashes=False)
api_v1.add_resource(StripeSubscriptionCallback, '/stripe-subscription-callback', strict_slashes=False)
api_v1.add_resource(UserSubsciption, '/user_subscription', strict_slashes=False)
api_v1.add_resource(FetchUserSubscriptions, '/user_subscription/<string:user_id>', strict_slashes=False)
api_v1.add_resource(FetchUserPaymentHistory, '/user_payment_history/<string:user_id>', strict_slashes=False)
api_v1.add_resource(GenerateLicenseKey, '/generate-license-key', strict_slashes=False)
api_v1.add_resource(RetrieveLicenseKey, '/retrieve-license-key', strict_slashes=False)
api_v1.add_resource(AuthenticateLicenseKey, '/authenticate-license-key', strict_slashes=False)
api_v1.add_resource(RecurringLicenseKeyCheck, '/recurring-license-key-check', strict_slashes=False)
app.register_blueprint(v1_blueprint)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)