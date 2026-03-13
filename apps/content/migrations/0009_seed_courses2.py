from django.db import migrations
from django.utils.text import slugify


def create_arabic_content(apps, schema_editor):
    GradeSubject = apps.get_model("curriculum", "GradeSubject")
    Chapter = apps.get_model("content", "Chapter")
    Course = apps.get_model("content", "Course")

    # New grade subjects
    grade_subject_slugs = ["3as-ar-lp", "3as-ar-lang"]

    # New data
    data = [
        {
            "chapter": "الوحدة 01 : الأدب في عهد المماليك",
            "courses": [
                "في مدح الرسول (ص)",
                "في الزهد",
                "الإعراب اللفظي والإعراب التقديري",
                "الشعر في عهد المماليك",
            ],
        },
        {
            "chapter": "الوحدة 02 : النثر والحركة العلمية",
            "courses": [
                "خواص القصر وتأثيراته",
                "علم التاريخ",
                "معاني حروف الجر والعطف",
                "حركة التأليف في عصر المماليك",
            ],
        },
        {
            "chapter": "الوحدة 03 : الآلام والاغتراب في الشعر",
            "courses": [
                "آلام الاغتراب",
                "من وحي المنفى",
                "المضاف إلى ياء المتكلم",
                "احتلال البلاد العربية وآثاره في الشعر والأدب",
            ],
        },
        {
            "chapter": "الوحدة 04 : الأدب المهجري",
            "courses": [
                "أنا (إيليا أبو ماضي)",
                "هنا وهناك",
                "الجمل التي لها محل من الإعراب",
                "الشعر مفهومه وغايته",
            ],
        },
        {
            "chapter": "الوحدة 05 : الالتزام في الشعر العربي الحديث",
            "courses": [
                "منشورات فدائية",
                "حالة حصار",
                "الجمل التي لا محل لها من الإعراب",
                "الالتزام في الشعر العربي الحديث",
            ],
        },
        {
            "chapter": "الوحدة 06 : الأدب الجزائري والهوية الوطنية",
            "courses": [
                "الإنسان الكبير",
                "جميلة",
                "أحكام التمييز والحال",
                "الأوراس في الشعر العربي",
            ],
        },
        {
            "chapter": "الوحدة 07 : قضايا اجتماعية معاصرة",
            "courses": [
                "أغنيات للألم",
                "أحزان الغربة",
                "صيغ منتهى الجموع",
                "الإحساس بالألم عند الشعراء المعاصرين",
            ],
        },
        {
            "chapter": "الوحدة 08 : الرمز والتاريخ",
            "courses": [
                "أبو تمام",
                "خطاب غير تاريخي على قبر صلاح الدين",
                "البدل وعطف البيان",
                "الرمز الشعري",
            ],
        },
        {
            "chapter": "الوحدة 09 : التجديد والتقليد",
            "courses": [
                "منزلة المثقفين في الأمة",
                "الصراع بين التقليد والتجديد",
                "لو، لولا، لوما",
                "المقالة والصحافة ودورهما في نهضة الفكر",
            ],
        },
        {
            "chapter": "الوحدة 10 : الفن القصصي",
            "courses": [
                "الجرح والأمل",
                "الطريق إلى قرية الطوب",
                "الأحرف المشبهة بالفعل",
                "صورة الاحتلال في القصة الجزائرية",
            ],
        },
        {
            "chapter": "الوحدة 11 : الفن المسرحي",
            "courses": [
                "من مسرحية شهرزاد",
                "كابوس في الظهيرة",
                "إعراب المتعدي إلى أكثر من مفعول",
                "المسرح في الأدب العربي",
            ],
        },
        {
            "chapter": "الوحدة 12 : الفكر النقدي الجزائري الحديث",
            "courses": [
                "لآلة فاطمة نسومر",
                "من مسرحية المغص",
                "نونا التوكيد",
                "المسرح الجزائري: الواقع والآفاق",
            ],
        },
    ]

    for grade_slug in grade_subject_slugs:
        grade_subject = GradeSubject.objects.get(slug=grade_slug)

        for chapter_order, item in enumerate(data, start=1):
            # Ensure chapter slug is unique
            chapter_slug = slugify(f"{grade_slug}-ch{chapter_order}-{item['chapter']}")
            chapter = Chapter.objects.create(
                grade_subject=grade_subject,
                title=item["chapter"],
                order=chapter_order,
                term="first",
                slug=chapter_slug,
            )

            for course_order, course_title in enumerate(item["courses"], start=1):
                # Ensure course slug is unique
                course_slug = slugify(
                    f"{grade_slug}-ch{chapter_order}-co{course_order}-{course_title}"
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

    slugs = ["3as-ar-lp", "3as-ar-lang"]

    for slug in slugs:
        try:
            gs = GradeSubject.objects.get(slug=slug)
            Chapter.objects.filter(grade_subject=gs).delete()
        except GradeSubject.DoesNotExist:
            pass


class Migration(migrations.Migration):
    dependencies = [("content", "0008_seed_courses")]

    operations = [migrations.RunPython(create_arabic_content, reverse_func)]
