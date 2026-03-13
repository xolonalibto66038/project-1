from django.core.management.base import BaseCommand
from django.db import transaction

from apps.accounts.choices import Gender, UserRole, Wilaya
from apps.accounts.models import CustomUser
from apps.curriculum.models import Grade, Specialty

DEFAULT_PASSWORD = "Pass.123"

STUDENTS = [
    {
        "email": "student001@student.com",
        "first_name": "Ahmed",
        "last_name": "Benali",
        "gender": Gender.MALE,
        "wilaya": Wilaya.ALGIERS,
        "grade_name": "1st Year Middle",  # must match Grade name in DB
        "specialty_name": None,  # None for Primaire/Moyen
        "bio": "Passionate about mathematics.",
    },
    {
        "email": "student002@student.com",
        "first_name": "Fatima",
        "last_name": "Zahra",
        "gender": Gender.FEMALE,
        "wilaya": Wilaya.ORAN,
        "grade_name": "1st Year Secondary",
        "specialty_name": "Common Core Science and Technology",  # must match Specialty name in DB
        "bio": "Loves biology and chemistry.",
    },
]


class Command(BaseCommand):
    help = "Seed the database with sample student accounts."

    def handle(self, *args, **options):
        created_count = 0
        skipped_count = 0

        for data in STUDENTS:
            email = data["email"]

            if CustomUser.objects.filter(email=email).exists():
                self.stdout.write(
                    self.style.WARNING(f"  [SKIP] {email} already exists.")
                )
                skipped_count += 1
                continue

            # Resolve Grade
            grade = None
            if data.get("grade_name"):
                try:
                    grade = Grade.objects.get(name=data["grade_name"])
                except Grade.DoesNotExist:
                    self.stdout.write(
                        self.style.ERROR(
                            f"  [ERROR] Grade '{data['grade_name']}' not found — skipping {email}."
                        )
                    )
                    skipped_count += 1
                    continue

            # Resolve Specialty
            specialty = None
            if data.get("specialty_name"):
                try:
                    specialty = Specialty.objects.get(name=data["specialty_name"])
                except Specialty.DoesNotExist:
                    self.stdout.write(
                        self.style.ERROR(
                            f"  [ERROR] Specialty '{data['specialty_name']}' not found — skipping {email}."
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
                    role=UserRole.STUDENT,
                    gender=data.get("gender", ""),
                    wilaya=data.get("wilaya", ""),
                    is_verified=True,
                )

                # Update the auto-created student profile (via signal)
                profile = user.student_profile
                profile.grade = grade
                profile.specialty = specialty
                profile.bio = data.get("bio", "")
                profile.save()

            self.stdout.write(self.style.SUCCESS(f"  [OK] Created student: {user}"))
            created_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"\nDone. {created_count} student(s) created, {skipped_count} skipped."
            )
        )
