from django.db import migrations
from django.utils.text import slugify


def populate_slugs(apps, schema_editor):
    GradeSubject = apps.get_model("curriculum", "GradeSubject")

    for gs in GradeSubject.objects.select_related(
        "grade", "subject", "specialty"
    ).all():
        grade = gs.grade.short_name
        subject = gs.subject.short_name
        specialty = gs.specialty.short_name if gs.specialty else None

        if specialty:
            slug = slugify(f"{grade}-{subject}-{specialty}")
        else:
            slug = slugify(f"{grade}-{subject}")

        gs.slug = slug
        gs.save(update_fields=["slug"])


def reverse_func(apps, schema_editor):
    GradeSubject = apps.get_model("curriculum", "GradeSubject")
    GradeSubject.objects.all().update(slug=None)


class Migration(migrations.Migration):

    dependencies = [
        ("curriculum", "0011_gradesubject_slug_and_more"),
    ]

    operations = [
        migrations.RunPython(populate_slugs, reverse_func),
    ]
