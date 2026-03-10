import stripe
from django.conf import settings

stripe.api_key = settings.STRIPE_TEST_SECRET_KEY


class StripeService:

    @staticmethod
    def create_checkout_session(session):

        print(session.teacher.teacher_profile.hour_price)

        try:
            checkout = stripe.checkout.Session.create(
                mode="payment",
                customer_email=session.student.email,
                line_items=[
                    {
                        "price_data": {
                            "currency": "usd",
                            "product_data": {
                                "name": f"Tutoring session with {session.teacher.get_full_name()}",
                            },
                            "unit_amount": int(
                                session.teacher.teacher_profile.hour_price * 100
                            ),
                        },
                        "quantity": 1,
                    }
                ],
                metadata={"session_id": str(session.id), "type": "tutoring_payment"},
                success_url=f"{settings.DOMAIN}/billing/payment_success/",
                cancel_url=f"{settings.DOMAIN}/billing/cancel/",
            )

            return checkout

        except stripe.error.CardError as e:
            print("Stripe Card Error:", e.user_message)

        except stripe.error.RateLimitError as e:
            print("Stripe Rate Limit Error:", str(e))

        except stripe.error.InvalidRequestError as e:
            print("Stripe Invalid Request:", str(e))

        except stripe.error.AuthenticationError as e:
            print("Stripe Authentication Error:", str(e))

        except stripe.error.APIConnectionError as e:
            print("Stripe Network Error:", str(e))

        except stripe.error.StripeError as e:
            print("Stripe General Error:", str(e))

        except Exception as e:
            print("Unexpected Error:", str(e))

        return None
