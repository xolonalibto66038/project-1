from django.db import migrations
from django.utils.text import slugify


def create_electrical_chapters(apps, schema_editor):
    GradeSubject = apps.get_model("curriculum", "GradeSubject")
    Chapter = apps.get_model("content", "Chapter")

    grade_subject_slug = "3as-elec-elec"

    data = [
        {"chapter": "وظيفة التغذية"},
        {"chapter": "تحويل الطاقة الكهربائية"},
        {"chapter": "وظيفة الاستطاعة"},
        {"chapter": "وظيفة تضخيم الاستطاعة"},
    ]

    grade_subject = GradeSubject.objects.get(slug=grade_subject_slug)

    for order, item in enumerate(data, start=1):

        chapter_slug = slugify(f"{grade_subject_slug}-ch{order}-{item['chapter']}")

        Chapter.objects.create(
            grade_subject=grade_subject,
            title=item["chapter"],
            order=order,
            term="first",  # or TERM_2 depending on your curriculum
            slug=chapter_slug,
        )


def reverse_func(apps, schema_editor):
    GradeSubject = apps.get_model("curriculum", "GradeSubject")
    Chapter = apps.get_model("content", "Chapter")

    try:
        gs = GradeSubject.objects.get(slug="3as-elec-elec")
        Chapter.objects.filter(grade_subject=gs).delete()
    except GradeSubject.DoesNotExist:
        pass


class Migration(migrations.Migration):

    dependencies = [
        ("content", "0011_seed_courses_eco_mgt_3_as"),
    ]

    operations = [
        migrations.RunPython(create_electrical_chapters, reverse_func),
    ]
