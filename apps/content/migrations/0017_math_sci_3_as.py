from django.db import migrations
from django.utils.text import slugify


def create_advanced_math_content(apps, schema_editor):
    GradeSubject = apps.get_model("curriculum", "GradeSubject")
    Chapter = apps.get_model("content", "Chapter")
    Course = apps.get_model("content", "Course")

    grade_subject_slugs = [
        "3as-math-proc",
        "3as-math-elec",
        "3as-math-se",
        "3as-math-mec",
        "3as-math-math",
        "3as-math-civil",
    ]

    data = [
        {
            "chapter": "النهايات والاستمرارية",
            "courses": [
                "النهاية المحدودة أو غير المحدودة عند ما لا نهاية أو ناقص لا نهاية",
                "النهاية عند عدد حقيقي",
                "تكملات على النهايات",
                "نهاية الدوال المركبة",
                "الاستمرارية",
                "نظرية القيمة المتوسطة",
                "دوال تربيعية ودوال أحادية التزايد",
            ],
        },
        {
            "chapter": "الاشتقاقية",
            "courses": [
                "الاشتقاق",
                "الاشتقاقات والعمليات",
                "اتجاه تغير الدالة",
                "اشتقاق الدوال المركبة",
                "التقريب الخطي",
                "طريقة أويلر",
                "دراسة الدوال المثلثية",
            ],
        },
        {
            "chapter": "الدوال الأسية واللوغاريتمية",
            "courses": [
                "الدالة الأسية",
                "الدوال الأسية: x -> exp(kx)",
                "دراسة الدالة الأسية",
                "دراسة الدالة: exp°u",
                "الدالة اللوغاريتمية النيبيرية",
                "الخواص الجبرية",
                "دراسة الدالة اللوغاريتمية النيبيرية",
                "الدالة اللوغاريتمية العشرية",
                "دراسة الدالة: ln°u",
            ],
        },
        {
            "chapter": "التزايد المقارن",
            "courses": [
                "أسس عدد حقيقي موجب",
                "دراسة الدوال: القوى والجذر",
                "التزايد المقارن",
            ],
        },
        {
            "chapter": "الدوال الأصلية",
            "courses": ["الدوال الأصلية", "حساب الدوال الأصلية", "المعادلات التفاضلية"],
        },
        {
            "chapter": "الحساب التكاملي",
            "courses": [
                "تكامل الدالة",
                "خواص التكامل",
                "القيمة المتوسطة",
                "تمديد على دالة ذات إشارة",
                "كيفية استخدام التكامل لحساب القيمة الأصلية",
                "بعض تطبيقات التكامل",
            ],
        },
        {
            "chapter": "الاحتمالات الشرطية",
            "courses": [
                "العد والترتيبات والتبديلات",
                "التوافيق، صيغة ثنائية الحد",
                "نمذجة تجربة عشوائية",
                "المتغير العشوائي",
                "الاحتمالات الشرطية",
                "الأحداث المستقلة",
            ],
        },
        {
            "chapter": "قوانين الاحتمالات",
            "courses": [
                "قانون برنولي",
                "قوانين الاحتمالات المستمرة",
                "قياس تلائم سلسله مشاهده ونموذج احتمالي",
                "القانون الاسي",
            ],
        },
    ]

    for slug in grade_subject_slugs:
        grade_subject = GradeSubject.objects.get(slug=slug)

        # Delete old chapters to avoid duplicates
        Chapter.objects.filter(grade_subject=grade_subject).delete()

        for ch_order, item in enumerate(data, start=1):
            chapter_slug = slugify(f"{slug}-ch{ch_order}-{item['chapter']}")
            chapter = Chapter.objects.create(
                grade_subject=grade_subject,
                title=item["chapter"],
                order=ch_order,
                term="first",
                slug=chapter_slug,
            )

            for co_order, course_title in enumerate(item.get("courses", []), start=1):
                course_slug = slugify(
                    f"{slug}-ch{ch_order}-co{co_order}-{course_title}"
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

    slugs = [
        "3as-math-proc",
        "3as-math-elec",
        "3as-math-se",
        "3as-math-mec",
        "3as-math-math",
        "3as-math-civil",
    ]

    for slug in slugs:
        try:
            gs = GradeSubject.objects.get(slug=slug)
            Chapter.objects.filter(grade_subject=gs).delete()
        except GradeSubject.DoesNotExist:
            pass


class Migration(migrations.Migration):

    dependencies = [
        ("content", "0016_math_mgt_3_as"),
    ]

    operations = [
        migrations.RunPython(create_advanced_math_content, reverse_func),
    ]
