from django.db import migrations
from django.utils.text import slugify


def create_philo_remaining_content(apps, schema_editor):
    GradeSubject = apps.get_model("curriculum", "GradeSubject")
    Chapter = apps.get_model("content", "Chapter")
    Course = apps.get_model("content", "Course")

    grade_subject_slugs = [
        "3as-philo-elec",
        "3as-philo-civil",
        "3as-philo-proc",
        "3as-philo-math",
        "3as-philo-se",
        "3as-philo-mgt",
        "3as-philo-mec",
    ]

    data = [
        {
            "chapter": "السؤال بين المشكلة والإشكالية",
            "courses": [
                "1- المشكلة الأولى: السؤال والمشكلة",
                "2- المشكلة الثانية: المشكلة والإشكالية",
            ],
        },
        {
            "chapter": "الفكر بين المبدأ والواقع",
            "courses": [
                "3- المشكلة الأولى: انطباق الفكر مع نفسه",
                "4- المشكلة الثانية: انطباق الفكر مع الواقع",
            ],
        },
        {
            "chapter": "المذاهب الفلسفية بين الشكل والمضمون",
            "courses": [
                "5- المشكلة الأولى: المذهب العقلاني والمذهب التجريبي",
                "6- المشكلة الثانية: المذهب البراغماتي والمذهب الوجودي",
            ],
        },
        {
            "chapter": "فلسفة العلوم",
            "courses": [
                "7- المشكلة الأولى: الحقيقة العلمية والحقيقة الفلسفية المطلقة",
                "8- المشكلة الثانية: الرياضيات والمطلقية",
                "9- المشكلة الثالثة: العلوم التجريبية والعلوم البيولوجية",
                "10- المشكلة الرابعة: علوم الإنسان والعلوم المعيارية",
                "11- المشكلة الخامسة: الإبستيمولوجيا وقيمة العلم",
            ],
        },
        {
            "chapter": "الحياة بين التنافر والتجاذب",
            "courses": [
                "12- المشكلة الأولى: الشعور بالأنا والشعور بالغير",
                "13- المشكلة الثانية: الحرية والمسؤولية",
                "14- المشكلة الثالثة: العنف والتسامح",
                "15- العولمة والتنوع الثقافي",
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


def reverse_philo_remaining(apps, schema_editor):
    GradeSubject = apps.get_model("curriculum", "GradeSubject")
    Chapter = apps.get_model("content", "Chapter")

    slugs = [
        "3as-philo-elec",
        "3as-philo-civil",
        "3as-philo-proc",
        "3as-philo-math",
        "3as-philo-se",
        "3as-philo-mgt",
        "3as-philo-mec",
    ]

    for slug in slugs:
        try:
            gs = GradeSubject.objects.get(slug=slug)
            Chapter.objects.filter(grade_subject=gs).delete()
        except GradeSubject.DoesNotExist:
            pass


class Migration(migrations.Migration):

    dependencies = [
        ("content", "0020_philo_lit_3_as"),
    ]

    operations = [
        migrations.RunPython(create_philo_remaining_content, reverse_philo_remaining),
    ]
