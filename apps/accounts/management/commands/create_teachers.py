from django.core.management.base import BaseCommand
from django.db import transaction

from apps.accounts.choices import Gender, UserRole, Wilaya
from apps.accounts.models import CustomUser
from apps.curriculum.models import Level, Subject

DEFAULT_PASSWORD = "Pass.123"

TEACHERS = [
    {
        "email": "teacher001@email.com",
        "first_name": "Karim",
        "last_name": "Messaoudi",
        "gender": Gender.MALE,
        "wilaya": Wilaya.CONSTANTINE,
        "level_name": "moyen",  # must match Level name in DB
        "subject_name": "Mathematics",  # must match Subject name in DB
        "bio": "10 years teaching Maths in Moyen.",
        "hour_price": 500.00,
        "is_verified_teacher": True,
    },
    {
        "email": "teacher002@email.com",
        "first_name": "Nadia",
        "last_name": "Brahimi",
        "gender": Gender.FEMALE,
        "wilaya": Wilaya.SETIF,
        "level_name": "secondaire",
        "subject_name": "Physics",
        "bio": "Specialized in experimental sciences.",
        "hour_price": 700.00,
        "is_verified_teacher": True,
    },
]


class Command(BaseCommand):
    help = "Seed the database with sample teacher accounts."

    def handle(self, *args, **options):
        created_count = 0
        skipped_count = 0

        for data in TEACHERS:
            email = data["email"]

            if CustomUser.objects.filter(email=email).exists():
                self.stdout.write(
                    self.style.WARNING(f"  [SKIP] {email} already exists.")
                )
                skipped_count += 1
                continue

            # Resolve Level
            level = None
            if data.get("level_name"):
                try:
                    level = Level.objects.get(name=data["level_name"])
                except Level.DoesNotExist:
                    self.stdout.write(
                        self.style.ERROR(
                            f"  [ERROR] Level '{data['level_name']}' not found — skipping {email}."
                        )
                    )
                    skipped_count += 1
                    continue

            # Resolve Subject
            subject = None
            if data.get("subject_name"):
                try:
                    subject = Subject.objects.get(
                        name=data["subject_name"], level=level
                    )
                except Subject.DoesNotExist:
                    self.stdout.write(
                        self.style.ERROR(
                            f"  [ERROR] Subject '{data['subject_name']}' under level "
                            f"'{data['level_name']}' not found — skipping {email}."
                        )
                    )
                    skipped_count += 1
                    continue

            with transaction.atomic():
                user = CustomUser.objects.create_user(
                    email=email,
                    password=DEFAULT_PASSWORD,
                    first_name=data["first_name"],
                    last_name=data["last_name"],
                    role=UserRole.TEACHER,
                    gender=data.get("gender", ""),
                    wilaya=data.get("wilaya", ""),
                    is_verified=True,
                )

                # Update the auto-created teacher profile (via signal)
                profile = user.teacher_profile
                profile.level = level
                profile.subject = subject
                profile.bio = data.get("bio", "")
                profile.hour_price = data.get("hour_price", 0)
                profile.is_verified_teacher = data.get("is_verified_teacher", False)
                profile.save()

            self.stdout.write(self.style.SUCCESS(f"  [OK] Created teacher: {user}"))
            created_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"\nDone. {created_count} teacher(s) created, {skipped_count} skipped."
            )
        )
