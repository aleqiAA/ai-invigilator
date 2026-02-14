import stripe
from flask import current_app

class PaymentSystem:
    def __init__(self):
        self.stripe = stripe
    
    def init_stripe(self):
        self.stripe.api_key = current_app.config.get('STRIPE_SECRET_KEY')
    
    def create_checkout_session(self, price_id, customer_email, success_url, cancel_url):
        try:
            session = self.stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{'price': price_id, 'quantity': 1}],
                mode='subscription',
                customer_email=customer_email,
                success_url=success_url,
                cancel_url=cancel_url,
            )
            return session.id, None
        except Exception as e:
            return None, str(e)
    
    def create_customer_portal_session(self, customer_id, return_url):
        try:
            session = self.stripe.billing_portal.Session.create(
                customer=customer_id,
                return_url=return_url,
            )
            return session.url, None
        except Exception as e:
            return None, str(e)
