from django.db import migrations
from django.utils.text import slugify


def create_arabic_content(apps, schema_editor):
    GradeSubject = apps.get_model("curriculum", "GradeSubject")
    Chapter = apps.get_model("content", "Chapter")
    Course = apps.get_model("content", "Course")

    grade_subject_slugs = [
        "3as-ar-math",
        "3as-ar-proc",
        "3as-ar-mec",
        "3as-ar-mgt",
        "3as-ar-elec",
        "3as-ar-se",
        "3as-ar-civil",
    ]

    data = [
        {
            "chapter": "الوحدة 01 : نشأة الشعر التعليمي",
            "courses": [
                "وصايا وتوجيهات",
                "معاني حروف الجر",
                "بلاغة المجاز العقلي والمجاز المرسل",
                "نشأة الشعر التعليمي",
            ],
        },
        {
            "chapter": "الوحدة 02 : حركة التأليف في عصر المماليك",
            "courses": [
                "علم التاريخ",
                "معاني حروف العطف",
                "تصريف الأجوف",
                "حركة التأليف في عصر المماليك",
            ],
        },
        {
            "chapter": "الوحدة 03 : النزعة الإنسانية في الشعر العربي المعاصر",
            "courses": [
                "أنا",
                "إذ، وإذاً",
                "التسامح الديني مطلب إنساني",
                "النزعة الإنسانية في الشعر العربي المعاصر",
            ],
        },
        {
            "chapter": "الوحدة 04 : الثقافة العربية",
            "courses": [
                "أخي",
                "إذ، حينئذ",
                "تصريف الناقص",
                "الثقافة العربية",
            ],
        },
        {
            "chapter": "الوحدة 05 : الالتزام في الشعر العربي الحديث",
            "courses": [
                "ثورة الشرفاء",
                "الخبر: مفرد، جملة، شبه جملة",
                "الجمل التي لها محل من الإعراب",
                "الالتزام في الشعر العربي الحديث",
            ],
        },
        {
            "chapter": "الوحدة 06 : فلسطين في الشعر الجزائري",
            "courses": [
                "حالة حصار",
                "الجمل التي لا محل لها من الإعراب",
                "بلاغة التشبيه",
                "فلسطين في الشعر الجزائري",
            ],
        },
        {
            "chapter": "الوحدة 07 : الأوراس في الشعر العربي",
            "courses": [
                "الإنسان الكبير",
                "أحكام التمييز والحال",
                "البدل وعطف البيان",
                "الأوراس في الشعر العربي",
            ],
        },
        {
            "chapter": "الوحدة 08 : الأدب وقضايا المجتمع المعاصر",
            "courses": [
                "الفراغ",
                "المجرد والمزيد بحرف",
                "بلاغة الاستعارة",
                "الأدب وقضايا المجتمع المعاصر",
            ],
        },
        {
            "chapter": "الوحدة 09 : المقالة والصحافة ودورهما في تطور الفكر",
            "courses": [
                "منزلة المثقفين في الأمة",
                "لو، لولا، لوما",
                "المزيد بحرفين وثلاثة",
                "المقالة والصحافة ودورهما في تطور الفكر والأدب",
            ],
        },
        {
            "chapter": "الوحدة 10 : القص الفني القصير في مواجهة التغيير الاجتماعي",
            "courses": [
                "الطريق إلى قرية الطوب",
                "اسم الجمع واسم الجنس الإفرادي والجمعي",
                "الكناية وبلاغتها",
                "القص الفني القصير في مواجهة التغيير الاجتماعي",
            ],
        },
        {
            "chapter": "الوحدة 11 : المسرح في الأدب العربي",
            "courses": [
                "كابوس في الظهيرة",
                "المتعدي إلى مفعولين وثلاثة مفاعيل",
                "اللغة والشخصية",
                "المسرح في الأدب العربي",
            ],
        },
        {
            "chapter": "الوحدة 12 : المسرح الجزائري: الواقع والآفاق",
            "courses": [
                "لآلة فاطمة نسومر",
                "نونا التوكيد ونون الوقاية",
                "العلامة محمد أبوشنب",
                "المسرح الجزائري: الواقع والآفاق",
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
                term="first",  # adjust depending on your Term choices
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

    slugs = [
        "3as-ar-math",
        "3as-ar-proc",
        "3as-ar-mec",
        "3as-ar-mgt",
        "3as-ar-elec",
        "3as-ar-se",
        "3as-ar-civil",
    ]

    for slug in slugs:
        try:
            gs = GradeSubject.objects.get(slug=slug)
            Chapter.objects.filter(grade_subject=gs).delete()
        except GradeSubject.DoesNotExist:
            pass


class Migration(migrations.Migration):

    dependencies = [
        ("content", "0007_resource_content"),
    ]

    operations = [
        migrations.RunPython(create_arabic_content, reverse_func),
    ]
