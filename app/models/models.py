from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Boolean, TIMESTAMP, ForeignKey, JSON, UUID

Base = declarative_base()
metadata = Base.metadata

class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    email = Column(String(255), unique=True, nullable=False)
    password = Column(String, nullable=True)
    created_at = Column(TIMESTAMP, nullable=False)
    updated_at = Column(TIMESTAMP, nullable=False, onupdate=TIMESTAMP)
    is_deleted = Column(Boolean, default=False)
    health_check = Column(Boolean, default=True)

    subscriptions = relationship('UserSubscription', backref='user', lazy=True)
    payments = relationship('Payments', backref='user', lazy=True)

    @property
    def serialize(self):
        return {
            'id': self.id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'email': self.email,
            'created_at': self.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            'updated_at': self.updated_at.strftime("%Y-%m-%d %H:%M:%S"),
            'is_deleted': self.is_deleted,
            'health_check': self.health_check
        }
    
class Subscription(Base):
    __tablename__ = 'subscriptions'

    id = Column(Integer, primary_key=True)
    subscription_name = Column(String, nullable=False)
    product_id = Column(String(255), unique=False, nullable=True)
    price_id = Column(String(255), unique=False, nullable=True)
    subscription_amount = Column(String, nullable=False)
    subscription_product_link = Column(String, nullable=False) 
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, nullable=False)
    updated_at = Column(TIMESTAMP, nullable=False, onupdate=TIMESTAMP)

    user_subscriptions = relationship('UserSubscription', backref='subscriptions', lazy=True)
    payments = relationship('Payments', backref='subscriptions', lazy=True)

    @property
    def serialize(self):
        return {
            'id': self.id,
            'subscription_name': self.subscription_name,
            'product_id': self.product_id,
            'price_id': self.price_id,
            'subscription_amount': self.subscription_amount,
            'subscription_product_link': self.subscription_product_link
        }


class UserSubscription(Base):
    __tablename__ = "user_subscription"
    id = Column(Integer, primary_key=True)
    expiry = Column(TIMESTAMP, nullable=True)
    last_payment = Column(TIMESTAMP, nullable=True)
    created_at = Column(TIMESTAMP, nullable=False)
    updated_at = Column(TIMESTAMP, nullable=False, onupdate=TIMESTAMP)

    user_id = Column(Integer, ForeignKey('user.id'), nullable=True)
    subscription_id = Column(Integer, ForeignKey('subscriptions.id'), nullable=True)
    @property
    def serialize(self):
        subscription_data = self.subscriptions.serialize if self.subscriptions else None
        user_data = self.user.serialize if self.user else None
        return {
            'id': self.id,
            'expiry': self.expiry.strftime("%Y-%m-%d %H:%M:%S"),
            'last_payment': self.last_payment.strftime("%Y-%m-%d %H:%M:%S"),
            'user': user_data,
            'subscription': subscription_data
        }
    
class Payments(Base):
    __tablename__ = "payments"
    id = Column(Integer, primary_key=True)
    request_uuid = Column(UUID, nullable=True)
    transaction_id = Column(String(255), unique=False, nullable=True)
    stripe_customer = Column(String(255), unique=False, nullable=True)
    stripe_data = Column(JSON, nullable=True)
    created_at = Column(TIMESTAMP, nullable=False)
    updated_at = Column(TIMESTAMP, nullable=False, onupdate=TIMESTAMP)
    status = Column(String, default='initiated')
    user_id = Column(Integer, ForeignKey('user.id'), nullable=True)
    subscription_id = Column(Integer, ForeignKey('subscriptions.id'), nullable=True)    
    @property
    def serialize(self):
        subscription_data = self.subscriptions.serialize if self.subscriptions else None
        user_data = self.user.serialize if self.user else None
        return {
            'id': self.id,
            'transaction_id': self.transaction_id,
            'stripe_customer': self.stripe_customer,
            'stripe_data': self.stripe_data,
            'user': user_data,
            'subscription': subscription_data,
            'status': self.status,
            'created_at': self.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            'updated_at': self.updated_at.strftime("%Y-%m-%d %H:%M:%S")
        }
    
class LicenseKeysModel(Base):
    __tablename__ = 'license_keys'
    id = Column(Integer, primary_key=True)
    user_license_key = Column(String, nullable=False)
    user_subscription_id = Column(Integer, ForeignKey('user_subscription.id'), nullable=True)
    in_use = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, nullable=False)
    updated_at = Column(TIMESTAMP, nullable=False, onupdate=TIMESTAMP)

    @property
    def serialize(self):
        user_subscription = self.user_subscription.serialize if self.user_subscription else None
        return {
            'id': self.id,
            'subscription_name': self.subscription_name,
            'user_subscription_id': user_subscription,
            'is_active': self.is_active,
            'in_use': self.in_use
        }