from django.db import migrations
from django.utils.text import slugify


def create_law_courses(apps, schema_editor):
    GradeSubject = apps.get_model("curriculum", "GradeSubject")
    Course = apps.get_model("content", "Course")

    grade_subject_slug = "3as-law-mgt"

    data = [
        {"course": "عقد البيع"},
        {"course": "عقد الشركة"},
        {"course": "شركة التضامن"},
        {"course": "شركات المساهمة والشركات ذات المسؤولية المحدودة"},
        {"course": "علاقات العمل الفردية"},
        {"course": "علاقات العمل الجماعية"},
        {"course": "الميزانية العامة للدولة وقانون المالية"},
        {"course": "الضرائب والرسوم"},
        {"course": "الضريبة على الدخل الإجمالي"},
        {"course": "الرسم على القيمة المضافة"},
    ]

    grade_subject = GradeSubject.objects.get(slug=grade_subject_slug)

    # prevent duplicates if migration reruns
    Course.objects.filter(grade_subject=grade_subject).delete()

    for order, item in enumerate(data, start=1):

        course_slug = slugify(f"{grade_subject_slug}-co{order}-{item['course']}")

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

    try:
        gs = GradeSubject.objects.get(slug="3as-law-mgt")
        Course.objects.filter(grade_subject=gs).delete()
    except GradeSubject.DoesNotExist:
        pass


class Migration(migrations.Migration):

    dependencies = [
        ("content", "0013_history_3_as"),
    ]

    operations = [
        migrations.RunPython(create_law_courses, reverse_func),
    ]
