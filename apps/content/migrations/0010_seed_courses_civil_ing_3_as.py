from django.db import migrations
from django.utils.text import slugify


def create_civil_content(apps, schema_editor):
    GradeSubject = apps.get_model("curriculum", "GradeSubject")
    Chapter = apps.get_model("content", "Chapter")
    Course = apps.get_model("content", "Course")

    grade_subject_slugs = [
        "3as-civil-civil",
    ]

    data = [
        {
            "chapter": "مقاومة المواد",
            "courses": [
                "الهدف من مقاومة المواد",
                "فرضيات مقاومة المواد",
                "الأفعال",
                "الجهود الداخلية",
                "تعريف التحريضات البسيطة",
                "الإجهادات",
                "تجربة القص البسيط",
                "عموميات (الإجهاد المماسي)",
                "شرط المقاومة",
                "قانون هوك",
                "تجربة الانحناء البسيط المستوي",
            ],
        },
        {
            "chapter": "الخرسانة المسلحة",
            "courses": [
                "عموميات",
                "الحالات النهائية",
                "خصائص المواد",
                "الشد البسيط",
                "الانضغاط البسيط",
            ],
        },
        {
            "chapter": "الطرق",
            "courses": [
                "تعريف",
                "تصنيف الطريق",
                "مكونات الطريق",
                "الوثائق الخطية لملف تقني لجزء طريق",
                "هيكلة القوارع",
                "مختلف أنواع القوارع",
            ],
        },
        {
            "chapter": "الجسور",
            "courses": [
                "عموميات",
                "تصنيف الجسور",
                "العناصر المكونة للجسر",
            ],
        },
        {
            "chapter": "الخرسانة المسبقة الإجهاد",
            "courses": [
                "عموميات",
                "مبدأ سبق الإجهاد",
                "طريقة استعمال سبق الإجهاد",
                "مجال الاستعمال",
            ],
        },
        {
            "chapter": "عناصر المنشآت العلوية",
            "courses": [
                "عموميات",
                "أعمدة",
                "الروافد",
                "الأرضيات",
                "الغطاء",
                "السطوح",
                "الجدران",
                "الفتحات",
                "المدارج المستقيمة",
            ],
        },
        {
            "chapter": "عموميات حول الطبوغرافيا",
            "courses": [
                "السمت الإحداثي",
                "حساب المساحات",
                "المراقبة الشاقولية",
                "المراقبة الأفقية",
            ],
        },
    ]

    for slug in grade_subject_slugs:
        grade_subject = GradeSubject.objects.get(slug=slug)

        for chapter_order, item in enumerate(data, start=1):

            chapter_slug = slugify(f"{slug}-ch{chapter_order}-{item['chapter']}")

            chapter = Chapter.objects.create(
                grade_subject=grade_subject,
                title=item["chapter"],
                order=chapter_order,
                term="first",
                slug=chapter_slug,
            )

            for course_order, course_title in enumerate(item["courses"], start=1):

                course_slug = slugify(
                    f"{slug}-ch{chapter_order}-co{course_order}-{course_title}"
                )

                Course.objects.create(
                    grade_subject=grade_subject,
                    # chapter=chapter,
                    title=course_title,
                    order=course_order,
                    slug=course_slug,
                    term="first",
                )


def reverse_func(apps, schema_editor):
    GradeSubject = apps.get_model("curriculum", "GradeSubject")
    Chapter = apps.get_model("content", "Chapter")

    slugs = ["3as-civil-civil"]

    for slug in slugs:
        try:
            gs = GradeSubject.objects.get(slug=slug)
            Chapter.objects.filter(grade_subject=gs).delete()
        except GradeSubject.DoesNotExist:
            pass


class Migration(migrations.Migration):

    dependencies = [
        ("content", "0009_seed_courses2"),
    ]

    operations = [
        migrations.RunPython(create_civil_content, reverse_func),
    ]
