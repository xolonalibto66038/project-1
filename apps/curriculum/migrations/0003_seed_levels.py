# apps/curriculum/migrations/0003_seed_levels.py

import uuid

from django.db import migrations
from django.utils.text import slugify

LEVELS = [
    {'name': 'primaire',   'slug': 'primaire',   'order': 1},
    {'name': 'moyen',      'slug': 'moyen',      'order': 2},
    {'name': 'secondaire', 'slug': 'secondaire', 'order': 3},
    {'name': 'university', 'slug': 'university', 'order': 4},
]


def seed_levels(apps, schema_editor):
    Level = apps.get_model('curriculum', 'Level')
    for data in LEVELS:
        Level.objects.get_or_create(
            name=data['name'],
            defaults={
                # 'id':    uuid.uuid4(),
                'slug':  data['slug'],
                'order': data['order'],
            }
        )


def unseed_levels(apps, schema_editor):
    Level = apps.get_model('curriculum', 'Level')
    Level.objects.filter(
        name__in=[d['name'] for d in LEVELS]
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('curriculum', '0002_specialty_created_at_specialty_updated_at_and_more'),
    ]

    operations = [
        migrations.RunPython(seed_levels, reverse_code=unseed_levels),
    ]