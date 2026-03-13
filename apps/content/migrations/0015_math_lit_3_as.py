from django.db import migrations
from django.utils.text import slugify


def create_math_courses(apps, schema_editor):
    GradeSubject = apps.get_model("curriculum", "GradeSubject")
    Course = apps.get_model("content", "Course")

    grade_subject_slugs = [
        "3as-math-lp",
        "3as-math-lang",
    ]

    data = [
        {"course": "القسمة الإقليدية في Z"},
        {"course": "المتتاليات العددية"},
        {"course": "اتجاه تغير دالة"},
        {"course": "الدوال كثيرات الحدود"},
        {"course": "الدوال التناظرية"},
        {"course": "الإحصاء و الاحتمالات"},
    ]

    for slug in grade_subject_slugs:

        grade_subject = GradeSubject.objects.get(slug=slug)

        # prevent duplicates if migration reruns
        Course.objects.filter(grade_subject=grade_subject).delete()

        for order, item in enumerate(data, start=1):

            course_slug = slugify(f"{slug}-co{order}-{item['course']}")

            Course.objects.create(
                grade_subject=grade_subject,
                title=item["course"],
                order=order,
                slug=course_slug,
                term="first",  # required for standalone courses
            )


def reverse_func(apps, schema_editor):
    GradeSubject = apps.get_model("curriculum", "GradeSubject")
    Course = apps.get_model("content", "Course")

    slugs = [
        "3as-math-lp",
        "3as-math-lang",
    ]

    for slug in slugs:
        try:
            gs = GradeSubject.objects.get(slug=slug)
            Course.objects.filter(grade_subject=gs).delete()
        except GradeSubject.DoesNotExist:
            pass


class Migration(migrations.Migration):

    dependencies = [
        ("content", "0014_law_mgt_3_as"),
    ]

    operations = [
        migrations.RunPython(create_math_courses, reverse_func),
    ]
