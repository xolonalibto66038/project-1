# apps/curriculum/migrations/0004_seed_specialties.py

import uuid

from django.db import migrations
from django.utils.text import slugify

# ── Specialties per secondaire grade ──────────────────────────────────────
# Structure: { short_name: [(name, short_name), ...] }

SPECIALTIES = {
    '1AS': [
        ('Common Core Science and Technology', 'CCST'),
        ('Common Core Literatures and Philosophy', 'CCLP'),
    ],
    '2AS': [
        ('Experimental Sciences',   'SE'),
        ('Mathematics',             'Math'),
        ('Mechanical Engineering',  'Mec'),
        ('Electrical Engineering',  'Elec'),
        ('Civil Engineering',       'Civil'),
        ('Procedural Engineering',  'Proc'),
        ('Literatures and Philosophy', 'LP'),
        ('Languages',               'Lang'),
        ('Management',              'Mgt'),
    ],
    '3AS': [
        ('Experimental Sciences',   'SE'),
        ('Mathematics',             'Math'),
        ('Mechanical Engineering',  'Mec'),
        ('Electrical Engineering',  'Elec'),
        ('Civil Engineering',       'Civil'),
        ('Procedural Engineering',  'Proc'),
        ('Literatures and Philosophy', 'LP'),
        ('Languages',               'Lang'),
        ('Management',              'Mgt'),
    ],
}


def seed_specialties(apps, schema_editor):
    Level     = apps.get_model('curriculum', 'Level')
    Grade     = apps.get_model('curriculum', 'Grade')
    Specialty = apps.get_model('curriculum', 'Specialty')

    try:
        secondaire = Level.objects.get(name='secondaire')
    except Level.DoesNotExist:
        raise Exception(
            "Level 'secondaire' not found. "
            "Run 0002_seed_levels first."
        )

    for grade_short_name, specialties in SPECIALTIES.items():
        try:
            grade = Grade.objects.get(
                level=secondaire,
                short_name=grade_short_name,
            )
        except Grade.DoesNotExist:
            raise Exception(
                f"Grade '{grade_short_name}' not found under 'secondaire'. "
                f"Run 0003_seed_grades first."
            )

        for name, short_name in specialties:
            slug = slugify(f"{grade_short_name}-{short_name}")
            Specialty.objects.get_or_create(
                grade=grade,
                name=name,
                defaults={
                    'id':         uuid.uuid4(),
                    'short_name': short_name,
                    'slug':       slug,
                },
            )


def unseed_specialties(apps, schema_editor):
    Level     = apps.get_model('curriculum', 'Level')
    Grade     = apps.get_model('curriculum', 'Grade')
    Specialty = apps.get_model('curriculum', 'Specialty')

    try:
        secondaire = Level.objects.get(name='secondaire')
        grades     = Grade.objects.filter(
            level=secondaire,
            short_name__in=SPECIALTIES.keys(),
        )
        Specialty.objects.filter(grade__in=grades).delete()
    except Level.DoesNotExist:
        pass


class Migration(migrations.Migration):

    dependencies = [
        ('curriculum', '0004_seed_grades'),
    ]

    operations = [
        migrations.RunPython(seed_specialties, reverse_code=unseed_specialties),
    ]