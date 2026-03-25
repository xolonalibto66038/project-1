import logging
from decimal import Decimal

import stripe
from django.conf import settings

stripe.api_key = settings.STRIPE_TEST_SECRET_KEY

logger = logging.getLogger(__name__)


class StripeService:

    @staticmethod
    def create_checkout_session(student, teacher):

        profile = teacher.teacher_profile
        price = int(profile.hour_price * 100)  # Stripe expects cents

        try:
            checkout = stripe.checkout.Session.create(
                mode="payment",
                customer_email=student.email,
                line_items=[
                    {
                        "price_data": {
                            "currency": "usd",
                            "product_data": {
                                "name": f"Tutoring session with {teacher.get_full_name()}",
                            },
                            "unit_amount": price,
                        },
                        "quantity": 1,
                    }
                ],
                metadata={
                    # "session_id": str(session.id),
                    "type": "tutoring_payment",
                    "student_id": str(student.id),
                    "teacher_id": str(teacher.id),
                },
                success_url=f"{settings.DOMAIN}/billing/payment_success/"
                + "?session_id={CHECKOUT_SESSION_ID}",
                cancel_url=f"{settings.DOMAIN}/billing/payment_cancel/",
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

    # @staticmethod
    # def create_meet_checkout_session(student, session):
    #     price = int(session.price_amount * 100)  # cents

    #     try:
    #         checkout = stripe.checkout.Session.create(
    #             mode="payment",
    #             customer_email=student.email,
    #             line_items=[
    #                 {
    #                     "price_data": {
    #                         "currency": session.price_currency.lower(),
    #                         "product_data": {
    #                             "name": f"Tutoring session with {session.teacher.get_full_name()}",
    #                             "description": (
    #                                 f"{session.proposed_start.strftime('%d %b %Y, %H:%M')} "
    #                                 f"— {session.duration_minutes} min"
    #                             ),
    #                         },
    #                         "unit_amount": price,
    #                     },
    #                     "quantity": 1,
    #                 }
    #             ],
    #             metadata={
    #                 "type": "meet_session_payment",
    #                 "meet_session_id": str(session.pk),
    #                 "student_id": str(student.id),
    #                 "teacher_id": str(session.teacher.id),
    #             },
    #             success_url=(
    #                 f"{settings.DOMAIN}"
    #                 f"/tutoring/student/meet-sessions/{session.pk}/"
    #                 f"?payment=success"
    #             ),
    #             cancel_url=(
    #                 f"{settings.DOMAIN}"
    #                 f"/tutoring/student/meet-sessions/{session.pk}/"
    #                 f"?payment=cancelled"
    #             ),
    #         )

    #         return checkout

    #     except stripe.error.CardError as e:
    #         logger.warning("Stripe CardError: %s", e.user_message)
    #     except stripe.error.RateLimitError as e:
    #         logger.error("Stripe RateLimitError: %s", str(e))
    #     except stripe.error.InvalidRequestError as e:
    #         logger.error("Stripe InvalidRequestError: %s", str(e))
    #     except stripe.error.AuthenticationError as e:
    #         logger.error("Stripe AuthenticationError: %s", str(e))
    #     except stripe.error.APIConnectionError as e:
    #         logger.error("Stripe APIConnectionError: %s", str(e))
    #     except stripe.error.StripeError as e:
    #         logger.error("Stripe StripeError: %s", str(e))
    #     except Exception as e:
    #         logger.exception(
    #             "Unexpected error in create_meet_checkout_session: %s", str(e)
    #         )

    #     return None

    @staticmethod
    def create_meet_checkout_session(student, session):
        # DZD minimum that clears Stripe's ~$0.50 floor
        # 1 USD ≈ 135 DZD → 70 DZD ≈ $0.52 — safe floor
        STRIPE_MIN_AMOUNT_DZD = Decimal("70.00")

        price_amount = session.price_amount
        currency = session.price_currency.lower()  # "dzd"

        if price_amount < STRIPE_MIN_AMOUNT_DZD:
            logger.warning(
                "Session %s price %s DZD is below Stripe minimum, clamping to %s",
                session.pk,
                price_amount,
                STRIPE_MIN_AMOUNT_DZD,
            )
            price_amount = STRIPE_MIN_AMOUNT_DZD

        unit_amount = int(price_amount * 100)  # Stripe expects cents

        try:
            checkout = stripe.checkout.Session.create(
                mode="payment",
                customer_email=student.email,
                line_items=[
                    {
                        "price_data": {
                            "currency": currency,
                            "product_data": {
                                "name": (
                                    f"Tutoring session with "
                                    f"{session.teacher.get_full_name()}"
                                ),
                                "description": (
                                    f"{session.proposed_start.strftime('%d %b %Y, %H:%M')}"
                                    f" — {session.duration_minutes} min"
                                ),
                            },
                            "unit_amount": unit_amount,
                        },
                        "quantity": 1,
                    }
                ],
                metadata={
                    "type": "meet_session_payment",
                    "meet_session_id": str(session.pk),
                    "student_id": str(student.id),
                    "teacher_id": str(session.teacher.id),
                },
                success_url=(
                    f"{settings.DOMAIN}"
                    f"/tutoring/meet/meet-sessions/{session.pk}/"
                    f"?payment=success"
                ),
                cancel_url=(
                    f"{settings.DOMAIN}"
                    f"/tutoring/meet/meet-sessions/{session.pk}/"
                    f"?payment=cancelled"
                ),
            )

            return checkout

        except stripe.error.InvalidRequestError as e:
            logger.error("Stripe InvalidRequestError: %s", str(e))
        except stripe.error.CardError as e:
            logger.warning("Stripe CardError: %s", e.user_message)
        except stripe.error.StripeError as e:
            logger.error("Stripe StripeError: %s", str(e))
        except Exception as e:
            logger.exception(
                "Unexpected error in create_meet_checkout_session: %s", str(e)
            )

        return None
