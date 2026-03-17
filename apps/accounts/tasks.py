from datetime import timedelta

from celery import shared_task
from django.utils import timezone


@shared_task(name="apps.accounts.tasks.delete_unverified_accounts")
def delete_unverified_accounts():
    from allauth.account.models import EmailAddress
    from django.contrib.auth import get_user_model

    User = get_user_model()
    cutoff = timezone.now() - timedelta(minutes=2)

    # IDs of users with at least one verified email — never touch these
    verified_user_ids = EmailAddress.objects.filter(verified=True).values_list(
        "user_id", flat=True
    )

    # IDs of users with at least one unverified email
    unverified_user_ids = EmailAddress.objects.filter(verified=False).values_list(
        "user_id", flat=True
    )

    deleted_count, _ = (
        User.objects.filter(
            id__in=unverified_user_ids,
            date_joined__lt=cutoff,
        )
        .exclude(id__in=verified_user_ids)
        .delete()
    )

    return f"Deleted {deleted_count} unverified accounts"


# @shared_task(name="apps.accounts.tasks.delete_unverified_accounts")
# def delete_unverified_accounts():
#     from allauth.account.models import EmailAddress
#     from django.contrib.auth import get_user_model

#     User = get_user_model()
#     cutoff = timezone.now() - timedelta(minutes=2)  # → timedelta(hours=24) in prod

#     # Users who have at least one verified email — never touch these
#     verified_user_ids = EmailAddress.objects.filter(verified=True).values_list(
#         "user_id", flat=True
#     )

#     deleted_count, _ = (
#         User.objects.filter(
#             date_joined__lt=cutoff,
#             emailaddress__verified=False,  # joined via allauth related name
#         )
#         .exclude(id__in=verified_user_ids)
#         .distinct()  # a user could have multiple unverified emails
#         .delete()
#     )

#     return f"Deleted {deleted_count} unverified accounts"
