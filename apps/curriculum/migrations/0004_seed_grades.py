# apps/curriculum/migrations/0004_seed_grades.py

import uuid

from django.db import migrations

GRADES = {
    "primaire": [
        {"order": 1, "name": "1st Year Primary", "short_name": "1AP"},
        {"order": 2, "name": "2nd Year Primary", "short_name": "2AP"},
        {"order": 3, "name": "3rd Year Primary", "short_name": "3AP"},
        {"order": 4, "name": "4th Year Primary", "short_name": "4AP"},
        {"order": 5, "name": "5th Year Primary", "short_name": "5AP"},
    ],
    "moyen": [
        {"order": 1, "name": "1st Year Middle", "short_name": "1AM"},
        {"order": 2, "name": "2nd Year Middle", "short_name": "2AM"},
        {"order": 3, "name": "3rd Year Middle", "short_name": "3AM"},
        {"order": 4, "name": "4th Year Middle", "short_name": "4AM"},
    ],
    "secondaire": [
        {"order": 1, "name": "1st Year Secondary", "short_name": "1AS"},
        {"order": 2, "name": "2nd Year Secondary", "short_name": "2AS"},
        {"order": 3, "name": "3rd Year Secondary", "short_name": "3AS"},
    ],
}


def seed_grades(apps, schema_editor):
    Level = apps.get_model("curriculum", "Level")
    Grade = apps.get_model("curriculum", "Grade")

    for level_name, grades in GRADES.items():
        try:
            level = Level.objects.get(name=level_name)
        except Level.DoesNotExist:
            raise Exception(
                f"Level '{level_name}' not found. " f"Run 0002_seed_levels first."
            )

        for grade in grades:
            Grade.objects.get_or_create(
                level=level,
                order=grade["order"],
                defaults={
                    "id": uuid.uuid4(),
                    "name": grade["name"],
                    "short_name": grade["short_name"],
                    "slug": grade["short_name"].lower(),
                },
            )


def unseed_grades(apps, schema_editor):
    Level = apps.get_model("curriculum", "Level")
    Grade = apps.get_model("curriculum", "Grade")

    for level_name in GRADES.keys():
        try:
            level = Level.objects.get(name=level_name)
            Grade.objects.filter(level=level).delete()
        except Level.DoesNotExist:
            pass


class Migration(migrations.Migration):

    dependencies = [
        ("curriculum", "0003_seed_levels"),
    ]

    operations = [
        migrations.RunPython(seed_grades, reverse_code=unseed_grades),
    ]
