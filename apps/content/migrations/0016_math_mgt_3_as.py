from django.db import migrations
from django.utils.text import slugify


def create_math_mgt_courses(apps, schema_editor):
    GradeSubject = apps.get_model("curriculum", "GradeSubject")
    Course = apps.get_model("content", "Course")

    grade_subject_slug = "3as-math-mgt"

    data = [
        {"course": "المتتاليات"},
        {"course": "الاستمرارية و النهايات"},
        {"course": "الاشتقاقية"},
        {"course": "الدوال الأصلية"},
        {"course": "الحساب التكاملي"},
        {"course": "الدالة اللوغاريتمية النيبيرية"},
        {"course": "الدالة الأسية"},
        {"course": "التزايد المقارن"},
        {"course": "الإحصاء"},
        {"course": "الاحتمالات"},
    ]

    grade_subject = GradeSubject.objects.get(slug=grade_subject_slug)

    # avoid duplicates if migration runs twice
    Course.objects.filter(grade_subject=grade_subject).delete()

    for order, item in enumerate(data, start=1):

        course_slug = slugify(f"{grade_subject_slug}-co{order}-{item['course']}")

        Course.objects.create(
            grade_subject=grade_subject,
            title=item["course"],
            order=order,
            slug=course_slug,
            term="TERM_1",  # required for standalone courses
        )


def reverse_func(apps, schema_editor):
    GradeSubject = apps.get_model("curriculum", "GradeSubject")
    Course = apps.get_model("content", "Course")

    try:
        gs = GradeSubject.objects.get(slug="3as-math-mgt")
        Course.objects.filter(grade_subject=gs).delete()
    except GradeSubject.DoesNotExist:
        pass


class Migration(migrations.Migration):

    dependencies = [
        ("content", "0015_math_lit_3_as"),
    ]

    operations = [
        migrations.RunPython(create_math_mgt_courses, reverse_func),
    ]
