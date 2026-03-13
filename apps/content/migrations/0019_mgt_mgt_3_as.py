from django.db import migrations
from django.utils.text import slugify


def create_eco_mgt_content(apps, schema_editor):
    GradeSubject = apps.get_model("curriculum", "GradeSubject")
    Chapter = apps.get_model("content", "Chapter")
    Course = apps.get_model("content", "Course")

    grade_subject_slug = "3as-eco-mgt"
    grade_subject = GradeSubject.objects.get(slug=grade_subject_slug)

    # Remove old chapters to avoid duplicates
    Chapter.objects.filter(grade_subject=grade_subject).delete()

    data = [
        {
            "chapter": "أعمال نهاية السنة - التسويات",
            "courses": [
                "1. تقديم أعمال نهاية السنة",
                "2. الاهتلاكات و نقص قيمة التثبيتات",
                "3. تسوية المخزونات",
                "4. تسويات عناصر الأصول الأخرى",
                "5. مؤونات حسابات الخصوم غير الجارية",
                "6. تسوية الأعباء و المنتوجات",
            ],
        },
        {
            "chapter": "إعداد الكشوف المالية و تحليلها",
            "courses": [
                "7. إعداد حساب النتائج والميزانية الختامية",
                "8. تحليل النتائج حسب الطبيعة",
                "9. تحليل النتائج حسب الوظيفة",
                "10. إعداد و تحليل الميزانية الوظيفية",
            ],
        },
        {
            "chapter": "تمويل و اختيار المشاريع الاستثمارية",
            "courses": [
                "11. مدخل لتمويل التثبيتات",
                "12. القروض العادية المسددة على دفعات ثابتة بفوائد مركبة",
                "13. اختيار المشاريع الاستثمارية",
            ],
        },
        {
            "chapter": "حساب و تحليل التكاليف الكلية",
            "courses": [
                "14. معالجة الأعباء المحملة للتكاليف",
                "15. حساب التكاليف و النتيجة التحليلية",
            ],
        },
        {
            "chapter": "التكاليف الجزئية",
            "courses": [
                "16. طريقة التكاليف المتغيرة",
                "17. طريقة التحميل العقلاني للأعباء الثابتة",
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

    try:
        gs = GradeSubject.objects.get(slug="3as-eco-mgt")
        Chapter.objects.filter(grade_subject=gs).delete()
    except GradeSubject.DoesNotExist:
        pass


class Migration(migrations.Migration):

    dependencies = [
        ("content", "0018_mec_mec_3_as"),
    ]

    operations = [
        migrations.RunPython(create_eco_mgt_content, reverse_func),
    ]
