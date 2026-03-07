# apps/curriculum/migrations/0008_seed_grade_subjects.py

import uuid
from django.db import migrations


def seed_grade_subjects(apps, schema_editor):
    Level        = apps.get_model('curriculum', 'Level')
    Grade        = apps.get_model('curriculum', 'Grade')
    Subject      = apps.get_model('curriculum', 'Subject')
    Specialty    = apps.get_model('curriculum', 'Specialty')
    GradeSubject = apps.get_model('curriculum', 'GradeSubject')

    for level in Level.objects.all():
        subjects = Subject.objects.filter(level=level)
        grades   = Grade.objects.filter(level=level)

        for grade in grades:
            specialties = Specialty.objects.filter(grade=grade)

            if specialties.exists():
                # ── Grade has specialties (2AS, 3AS) ──────────────────────
                # Each subject is linked per specialty
                for specialty in specialties:
                    for subject in subjects:
                        GradeSubject.objects.get_or_create(
                            grade=grade,
                            subject=subject,
                            specialty=specialty,
                            defaults={'id': uuid.uuid4()},
                        )
            else:
                # ── Grade has no specialties (all primaire, moyen, 1AS) ───
                # Subjects apply to the whole grade — specialty=None
                for subject in subjects:
                    GradeSubject.objects.get_or_create(
                        grade=grade,
                        subject=subject,
                        specialty=None,
                        defaults={'id': uuid.uuid4()},
                    )


def unseed_grade_subjects(apps, schema_editor):
    GradeSubject = apps.get_model('curriculum', 'GradeSubject')
    GradeSubject.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('curriculum', '0007_merge_0005_seed_subjects_0006_seed_specialities'),
    ]

    operations = [
        migrations.RunPython(
            seed_grade_subjects,
            reverse_code=unseed_grade_subjects,
        ),
    ]