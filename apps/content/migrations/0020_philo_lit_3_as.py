from django.db import migrations
from django.utils.text import slugify


def create_philo_content(apps, schema_editor):
    GradeSubject = apps.get_model("curriculum", "GradeSubject")
    Chapter = apps.get_model("content", "Chapter")
    Course = apps.get_model("content", "Course")

    grade_subject_slugs = ["3as-philo-lang", "3as-philo-lp"]

    data = [
        {
            "chapter": "في إدراك العالم الخارجي",
            "courses": [
                "1. المشكلة الأولى : في الإحساس والإدراك",
                "2. المشكلة الثانية : في اللغة والفكر",
                "3. المشكلة الثالثة : في الشعور واللاشعور",
                "4. المشكلة الرابعة : في الذاكرة والخيال",
                "5. المشكلة الخامسة : في العادة والإرادة",
            ],
        },
        {
            "chapter": "في الأخلاق الموضوعية والأخلاق النسبية",
            "courses": [
                "6. المشكلة الأولى : في الأخلاق بين النسبي والمطلق",
                "7. المشكلة الثانية : في الحقوق والواجبات والعدل",
                "8. المشكلة الثالثة : في العلاقات الأسرية والنظم الاقتصادية والسياسية",
                "9. المشكلة الرابعة : في الشخصية الجماعية والشخصية الفردية وكرامة الإنسان",
            ],
        },
        {
            "chapter": "في فلسفة العلوم",
            "courses": [
                "10. المشكلة الأولى : في الحقيقة العلمية والحقيقة الفلسفية المطلقة",
                "11. المشكلة الثانية : في الرياضيات والمطلقية",
                "12. المشكلة الثالثة : في العلوم التجريبية والعلوم البيولوجية",
                "13. المشكلة الرابعة : في علوم الإنسان والعلوم المعيارية",
                "14. المشكلة الخامسة : في الإبستيمولوجيا وقيمة العلم",
            ],
        },
        {
            "chapter": "في الفن والتصوف بين النسبي والمطلق",
            "courses": [
                "15. المشكلة الأولى : في الآثار الفنية والتجربة الذوقية",
                "16. المشكلة الثانية : في التصوف بين النسبي والمطلق",
            ],
        },
    ]

    for grade_subject_slug in grade_subject_slugs:
        grade_subject = GradeSubject.objects.get(slug=grade_subject_slug)
        # Remove existing chapters to avoid duplicates
        Chapter.objects.filter(grade_subject=grade_subject).delete()

        for ch_order, item in enumerate(data, start=1):
            chapter_slug = slugify(
                f"{grade_subject_slug}-ch{ch_order}-{item['chapter']}"
            )
            chapter = Chapter.objects.create(
                grade_subject=grade_subject,
                title=item["chapter"],
                order=ch_order,
                term="first",
                slug=chapter_slug,
            )

            for co_order, course_title in enumerate(item.get("courses", []), start=1):
                course_slug = slugify(
                    f"{grade_subject_slug}-ch{ch_order}-co{co_order}-{course_title}"
                )
                Course.objects.create(
                    # chapter=chapter,
                    grade_subject=grade_subject,
                    title=course_title,
                    order=co_order,
                    slug=course_slug,
                    term="first",
                )


def reverse_func(apps, schema_editor):
    GradeSubject = apps.get_model("curriculum", "GradeSubject")
    Chapter = apps.get_model("content", "Chapter")

    for slug in ["3as-philo-lang", "3as-philo-lp"]:
        try:
            gs = GradeSubject.objects.get(slug=slug)
            Chapter.objects.filter(grade_subject=gs).delete()
        except GradeSubject.DoesNotExist:
            pass


class Migration(migrations.Migration):

    dependencies = [
        ("content", "0019_mgt_mgt_3_as"),
    ]

    operations = [
        migrations.RunPython(create_philo_content, reverse_func),
    ]
