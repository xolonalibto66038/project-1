# apps/accounts/migrations/000X_seed_users.py
from decimal import Decimal

from django.db import migrations

DEFAULT_PASSWORD = "Pass.123"


def create_users(apps, schema_editor):
    CustomUser = apps.get_model("accounts", "CustomUser")
    StudentProfile = apps.get_model("accounts", "StudentProfile")
    TeacherProfile = apps.get_model("accounts", "TeacherProfile")
    Grade = apps.get_model("curriculum", "Grade")
    Specialty = apps.get_model("curriculum", "Specialty")
    Level = apps.get_model("curriculum", "Level")
    Subject = apps.get_model("curriculum", "Subject")
    Gender = apps.get_model("accounts", "CustomUser")._meta.get_field("gender").choices
    UserRole = apps.get_model("accounts", "CustomUser")._meta.get_field("role").choices
    Wilaya = apps.get_model("accounts", "CustomUser")._meta.get_field("wilaya").choices

    # ── Superadmin ──
    if not CustomUser.objects.filter(email="admin@platform.com").exists():
        CustomUser.objects.create(
            email="admin@platform.com",
            password=DEFAULT_PASSWORD,
            first_name="Super",
            last_name="Admin",
            role="teacher",
            gender="MALE",
            wilaya="16",  # Algiers code in your Wilaya choices
            is_verified=True,
        )

    # ── Students ──
    students_data = [
        {
            "email": "student001@student.com",
            "first_name": "Ahmed",
            "last_name": "Benali",
            "gender": "MALE",
            "wilaya": "16",  # Algiers
            "grade_name": "1st Year Middle",
            "specialty_name": None,
            "bio": "Passionate about mathematics.",
        },
        {
            "email": "student002@student.com",
            "first_name": "Fatima",
            "last_name": "Zahra",
            "gender": "FEMALE",
            "wilaya": "31",  # Oran
            "grade_name": "1st Year Secondary",
            "specialty_name": "Common Core Science and Technology",
            "bio": "Loves biology and chemistry.",
        },
    ]

    for data in students_data:
        if CustomUser.objects.filter(email=data["email"]).exists():
            continue

        grade = None
        if data.get("grade_name"):
            try:
                grade = Grade.objects.get(name=data["grade_name"])
            except Grade.DoesNotExist:
                continue

        specialty = None
        if data.get("specialty_name"):
            try:
                specialty = Specialty.objects.get(name=data["specialty_name"])
            except Specialty.DoesNotExist:
                continue

        user = CustomUser.objects.create(
            email=data["email"],
            password=DEFAULT_PASSWORD,
            first_name=data["first_name"],
            last_name=data["last_name"],
            role="student",
            gender=data.get("gender", ""),
            wilaya=data.get("wilaya", ""),
            is_verified=True,
        )

        profile = StudentProfile.objects.create(
            user=user,
            grade=grade,
            specialty=specialty,
            bio=data.get("bio", ""),
        )

    # ── Teachers ──
    teachers_data = [
        {
            "email": "teacher001@email.com",
            "first_name": "Karim",
            "last_name": "Messaoudi",
            "gender": "MALE",
            "wilaya": "25",  # Constantine
            "level_name": "moyen",
            "subject_name": "Mathematics",
            "bio": "10 years teaching Maths in Moyen.",
            "hour_price": Decimal("500.00"),
            "is_verified_teacher": True,
        },
        {
            "email": "teacher002@email.com",
            "first_name": "Nadia",
            "last_name": "Brahimi",
            "gender": "FEMALE",
            "wilaya": "19",  # Setif
            "level_name": "secondaire",
            "subject_name": "Physics",
            "bio": "Specialized in experimental sciences.",
            "hour_price": Decimal("700.00"),
            "is_verified_teacher": True,
        },
    ]

    for data in teachers_data:
        if CustomUser.objects.filter(email=data["email"]).exists():
            continue

        try:
            level = Level.objects.get(name=data["level_name"])
        except Level.DoesNotExist:
            continue

        try:
            subject = Subject.objects.get(name=data["subject_name"], level=level)
        except Subject.DoesNotExist:
            continue

        user = CustomUser.objects.create(
            email=data["email"],
            password=DEFAULT_PASSWORD,
            first_name=data["first_name"],
            last_name=data["last_name"],
            role="teacher",
            gender=data.get("gender", ""),
            wilaya=data.get("wilaya", ""),
            is_verified=True,
        )

        profile = TeacherProfile.objects.create(
            user=user,
            level=level,
            subject=subject,
            bio=data.get("bio", ""),
            hour_price=data.get("hour_price", Decimal("0.00")),
            is_verified_teacher=data.get("is_verified_teacher", False),
        )


class Migration(migrations.Migration):

    dependencies = [
        (
            "accounts",
            "0002_teacherprofile_hour_price",
        ),  # replace with your last migration
        (
            "curriculum",
            "0011_gradesubject_slug_and_more",
        ),  # ensure Grades, Levels, Subjects exist
    ]

    operations = [
        migrations.RunPython(create_users),
    ]
