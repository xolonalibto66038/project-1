# apps/curriculum/migrations/0005_seed_subjects.py

import uuid

from django.db import migrations
from django.utils.text import slugify

# ── Subject definitions per level ──────────────────────────────────────────
# Each subject: (name, short_name, icon)
# Subjects are scoped to a level — same subject name can appear in multiple
# levels as separate rows (unique_together = level + name)

SUBJECTS = {
    "primaire": [
        ("Mathematics", "Math", "fas fa-calculator"),
        ("Arabic", "AR", "fas fa-language"),
        ("French", "FR", "fas fa-flag"),
        ("English", "EN", "fas fa-globe"),
        ("Islamic Studies", "Islam", "fas fa-star-and-crescent"),
        ("Civic Studies", "Civic", "fas fa-landmark"),
        ("Technology", "Tech", "fas fa-microchip"),
        ("Sciences", "Sci", "fas fa-flask"),
        ("Drawing", "Draw", "fas fa-paint-brush"),
        ("History and Geography", "HistGeo", "fas fa-scroll"),
        # ('Geography',      'Geo',     'fas fa-map-marked-alt'),
        ("Music", "Music", "fas fa-music"),
        ("Writing", "Write", "fas fa-pen-nib"),
        ("Amazigh Language", "Amazigh", "fas fa-language"),
    ],
    "moyen": [
        ("Mathematics", "Math", "fas fa-calculator"),
        ("Physics", "Phys", "fas fa-atom"),
        ("Sciences", "Sci", "fas fa-flask"),
        ("Arabic", "AR", "fas fa-language"),
        ("French", "FR", "fas fa-flag"),
        ("English", "EN", "fas fa-globe"),
        ("Islamic Studies", "Islam", "fas fa-star-and-crescent"),
        ("Civic Studies", "Civic", "fas fa-landmark"),
        ("History", "Hist", "fas fa-scroll"),
        ("Geography and Geography", "HistGeo", "fas fa-map-marked-alt"),
        ("Drawing", "Draw", "fas fa-paint-brush"),
        ("Music", "Music", "fas fa-music"),
        ("Amazigh Language", "Amazigh", "fas fa-language"),
        ("Computer science", "CS", "fas fa-laptop"),
    ],
    "secondaire": [
        ("Mathematics", "Math", "fas fa-calculator"),
        ("Physics", "Phys", "fas fa-atom"),
        ("Sciences", "Sci", "fas fa-flask"),
        ("Technology", "Tech", "fas fa-microchip"),
        ("Mechanical Engineering", "Mec", "fas fa-cogs"),
        ("Electrical Engineering", "Elec", "fas fa-bolt"),
        ("Civil Engineering", "Civil", "fas fa-hard-hat"),
        ("Procedural Engineering", "Proc", "fas fa-project-diagram"),
        ("Accounting", "Acc", "fas fa-coins"),
        ("Management and Economy", "Eco", "fas fa-chart-line"),
        ("Arabic", "AR", "fas fa-language"),
        ("French", "FR", "fas fa-flag"),
        ("English", "EN", "fas fa-globe"),
        ("Spanish", "ES", "fas fa-globe-europe"),
        ("German", "DE", "fas fa-globe-europe"),
        ("Italian", "IT", "fas fa-globe-europe"),
        ("Islamic Studies", "Islam", "fas fa-star-and-crescent"),
        ("Philosophy", "Philo", "fas fa-brain"),
        ("Geography and Geography", "HistGeo", "fas fa-map-marked-alt"),
        # ('Geography',               'Geo',     'fas fa-map-marked-alt'),
        ("Civic Studies", "Civic", "fas fa-landmark"),
        ("Law", "Law", "fas fa-gavel"),
        ("Amazigh Language", "Amazigh", "fas fa-language"),
        ("Drawing", "Draw", "fas fa-paint-brush"),
        ("Computer science", "CS", "fas fa-laptop"),
    ],
    "university": [
        ("Mathematics", "Math", "fas fa-calculator"),
        ("Physics", "Phys", "fas fa-atom"),
        ("Sciences", "Sci", "fas fa-flask"),
        ("Mechanical Engineering", "Mec", "fas fa-cogs"),
        ("Electrical Engineering", "Elec", "fas fa-bolt"),
        ("Civil Engineering", "Civil", "fas fa-hard-hat"),
        ("Procedural Engineering", "Proc", "fas fa-project-diagram"),
        ("Accounting", "Acc", "fas fa-coins"),
        ("Management and Economy", "Eco", "fas fa-chart-line"),
        ("Arabic", "AR", "fas fa-language"),
        ("French", "FR", "fas fa-flag"),
        ("English", "EN", "fas fa-globe"),
        ("Philosophy", "Philo", "fas fa-brain"),
        ("History", "Hist", "fas fa-scroll"),
        ("Law", "Law", "fas fa-gavel"),
    ],
}


def seed_subjects(apps, schema_editor):
    Level = apps.get_model("curriculum", "Level")
    Subject = apps.get_model("curriculum", "Subject")

    for level_name, subjects in SUBJECTS.items():
        try:
            level = Level.objects.get(name=level_name)
        except Level.DoesNotExist:
            raise Exception(
                f"Level '{level_name}' not found. " f"Run 0002_seed_levels first."
            )

        for name, short_name, icon in subjects:
            slug = slugify(f"{level_name}-{name}")
            Subject.objects.get_or_create(
                level=level,
                name=name,
                defaults={
                    "id": uuid.uuid4(),
                    "short_name": short_name,
                    "slug": slug,
                    "icon": icon,
                },
            )


def unseed_subjects(apps, schema_editor):
    Level = apps.get_model("curriculum", "Level")
    Subject = apps.get_model("curriculum", "Subject")

    for level_name in SUBJECTS.keys():
        try:
            level = Level.objects.get(name=level_name)
            Subject.objects.filter(level=level).delete()
        except Level.DoesNotExist:
            pass


class Migration(migrations.Migration):

    dependencies = [
        ("curriculum", "0004_seed_grades"),  # adjust if your last migration differs
    ]

    operations = [
        migrations.RunPython(seed_subjects, reverse_code=unseed_subjects),
    ]
