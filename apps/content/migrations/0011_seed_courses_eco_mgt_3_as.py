from django.db import migrations
from django.utils.text import slugify


def create_management_courses(apps, schema_editor):
    GradeSubject = apps.get_model("curriculum", "GradeSubject")
    Course = apps.get_model("content", "Course")

    grade_subject_slug = "3as-eco-mgt"

    data = [
        {"course": "النقود"},
        {"course": "السوق والأسعار"},
        {"course": "النظام المصرفي"},
        {"course": "التجارة الخارجية"},
        {"course": "الصرف"},
        {"course": "البطالة"},
        {"course": "التضخم"},
        {"course": "القيادة"},
        {"course": "الاتصال"},
        {"course": "الرقابة"},
        {"course": "التمويل"},
        {"course": "الإنتاج"},
        {"course": "التقييس"},
        {"course": "الموارد البشرية"},
    ]

    grade_subject = GradeSubject.objects.get(slug=grade_subject_slug)

    for order, item in enumerate(data, start=1):

        course_slug = slugify(f"{grade_subject_slug}-co{order}-{item['course']}")

        Course.objects.create(
            grade_subject=grade_subject,
            title=item["course"],
            order=order,
            slug=course_slug,
            term="first",  # REQUIRED because there is no chapter
        )


def reverse_func(apps, schema_editor):
    GradeSubject = apps.get_model("curriculum", "GradeSubject")
    Course = apps.get_model("content", "Course")

    try:
        gs = GradeSubject.objects.get(slug="3as-eco-mgt")
        Course.objects.filter(grade_subject=gs).delete()
    except GradeSubject.DoesNotExist:
        pass


class Migration(migrations.Migration):

    dependencies = [
        ("content", "0010_seed_courses_civil_ing_3_as"),
    ]

    operations = [
        migrations.RunPython(create_management_courses, reverse_func),
    ]
