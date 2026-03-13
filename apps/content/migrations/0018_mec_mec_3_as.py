from django.db import migrations
from django.utils.text import slugify


def create_mechanics_content(apps, schema_editor):
    GradeSubject = apps.get_model("curriculum", "GradeSubject")
    Chapter = apps.get_model("content", "Chapter")
    Course = apps.get_model("content", "Course")

    grade_subject_slug = "3as-mec-mec"
    grade_subject = GradeSubject.objects.get(slug=grade_subject_slug)

    # Delete old chapters for this subject to avoid duplicates
    Chapter.objects.filter(grade_subject=grade_subject).delete()

    data = [
        {
            "chapter": "التوجيه الدوراني",
            "courses": [
                "الوحدة 01 : الوصلة المتمحورة",
                "الوحدة 02 : الوصلة المتمحورة بالانزلاق",
                "الوحدة 03 : الوصلة المتمحورة بالتدحرج",
                "الوحدة 04 : تركيب المدحرجات",
            ],
        },
        {
            "chapter": "نقل الاستطاعة",
            "courses": [
                "الوحدة 01 : مفهوم نقل الحركة",
                "الوحدة 02 : البكرات و السيور",
                "الوحدة 03 : المتسننات",
                "الوحدة 04 : تحويل الحركة",
            ],
        },
        {
            "chapter": "مقاومة المواد",
            "courses": [
                "الوحدة 01 : عموميات حول مقاومة المواد",
                "الوحدة 02 : المد البسيط - الانضغاط البسيط",
                "الوحدة 03 : القص البسيط",
                "الوحدة 04 : الالتواء البسيط",
                "الوحدة 05 : الانحناء المستوي البسيط",
            ],
        },
        {
            "chapter": "تحضير الإنتاج",
            "courses": [
                "الوحدة 01 : مكونات الإنتاج",
                "الوحدة 02 : وسائل الإنتاج",
                "الوحدة 03 : القياس و المراقبة",
                "الوحدة 04 : أدوات التحضير",
            ],
        },
        {
            "chapter": "التحكم العددي",
            "courses": [
                "الوحدة 01 : البرمجة على آلة التحكم العددي",
                "الوحدة 02 : محاكاة الصنع",
            ],
        },
        {
            "chapter": "الآليات",
            "courses": [
                "الوحدة 01 : الأجهزة الهوائية",
                "الوحدة 02 : المنطق التوفيقي",
                "الوحدة 03 : المنطق التعاقبي",
                "الوحدة 04 : محاكاة الآليات",
            ],
        },
    ]

    for ch_order, item in enumerate(data, start=1):
        chapter_slug = slugify(f"{grade_subject_slug}-ch{ch_order}-{item['chapter']}")
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

    grade_subject_slug = "3as-mec-mec"
    try:
        gs = GradeSubject.objects.get(slug=grade_subject_slug)
        Chapter.objects.filter(grade_subject=gs).delete()
    except GradeSubject.DoesNotExist:
        pass


class Migration(migrations.Migration):

    dependencies = [
        ("content", "0017_math_sci_3_as"),
    ]

    operations = [
        migrations.RunPython(create_mechanics_content, reverse_func),
    ]
