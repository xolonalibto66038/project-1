from django.db import migrations
from django.utils.text import slugify


def create_histgeo_content(apps, schema_editor):
    GradeSubject = apps.get_model("curriculum", "GradeSubject")
    Chapter = apps.get_model("content", "Chapter")
    Course = apps.get_model("content", "Course")

    grade_subject_slugs = [
        "3as-histgeo-se",
        "3as-histgeo-math",
        "3as-histgeo-mec",
        "3as-histgeo-elec",
        "3as-histgeo-civil",
        "3as-histgeo-proc",
        "3as-histgeo-lp",
        "3as-histgeo-lang",
        "3as-histgeo-mgt",
    ]

    data = [
        {
            "chapter": "بروز الصراع وتشكل العالم بعد الحرب العالمية الثانية",
            "courses": [
                "معايير تشكل العالم (تاريخية، سياسية، اقتصادية، اجتماعية)",
                "طبيعة العلاقة بين الكتلتين",
            ],
        },
        {
            "chapter": "إستراتيجيات الصراع وسباق التسلح",
            "courses": [
                "الإستراتيجيات الخاصة بكل كتلة (سياسيا، اقتصاديا وعسكريا)",
                "مشروع هاري ترومان ومبدأ جدا نوف",
                "الاستقطاب ومشروع مارشال",
                "الأحلاف العسكرية والقواعد العسكرية",
                "التسابق نحو التسلح",
            ],
        },
        {
            "chapter": "الأزمات الدولية في ظل الحرب الباردة",
            "courses": [
                "أزمة برلين الأولى والثانية",
                "أزمة كوريا",
                "أزمة السويس",
                "أزمة كوبا",
            ],
        },
        {
            "chapter": "مساعي الانفراج والتعايش السلمي",
            "courses": [
                "مفهوم التعايش السلمي والانفراج الدولي",
                "عوامل الجنوح إلى السلم",
                "الظروف الدولية السائدة",
            ],
        },
        {
            "chapter": "من الثنائية إلى الأحادية القطبية",
            "courses": [
                "عوامل تفكك الكتلة الشرقية وسقوط الاتحاد السوفياتي",
                "ملامح النظام الدولي الجديد وأهدافه",
            ],
        },
        {
            "chapter": "من تبلور الوعي إلى العمل الوطني",
            "courses": [
                "نضال الحركة الوطنية خلال الحرب العالمية الثانية",
                "إعادة بناء الحركة الوطنية بعد 1945",
                "أزمة حركة انتصار الحريات الديمقراطية 1953",
            ],
        },
        {
            "chapter": "العمل الثوري المسلح",
            "courses": [
                "تحضير الثورة واندلاعها",
                "شمولية الثورة وتنظيمها (مؤتمر الصومام)",
                "المخططات الاستعمارية (العسكرية، السياسية والاقتصادية)",
                "المفاوضات واستعادة السيادة الوطنية",
            ],
        },
        {
            "chapter": "استعادة السيادة وبناء الدولة",
            "courses": [
                "الاختيارات الكبرى لبناء الدولة الجزائرية (ميثاق طرابلس)",
                "التطور السياسي لبناء الدولة من 1962 إلى 1989",
            ],
        },
        {
            "chapter": "تأثير الجزائر وإسهامها في حركة التحرر العالمي",
            "courses": [
                "الجزائر والقضايا العادلة (فلسطين)",
                "الجزائر والمنظمات الدولية",
            ],
        },
    ]

    for slug in grade_subject_slugs:
        grade_subject = GradeSubject.objects.get(slug=slug)

        # Prevent duplicates if migration re-runs
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

            for co_order, title in enumerate(item["courses"], start=1):

                course_slug = slugify(f"{slug}-ch{ch_order}-co{co_order}-{title}")

                Course.objects.create(
                    grade_subject=grade_subject,
                    title=title,
                    order=co_order,
                    slug=course_slug,
                    term="first",
                )


def reverse_func(apps, schema_editor):
    GradeSubject = apps.get_model("curriculum", "GradeSubject")
    Chapter = apps.get_model("content", "Chapter")

    slugs = [
        "3as-histgeo-se",
        "3as-histgeo-math",
        "3as-histgeo-mec",
        "3as-histgeo-elec",
        "3as-histgeo-civil",
        "3as-histgeo-proc",
        "3as-histgeo-lp",
        "3as-histgeo-lang",
        "3as-histgeo-mgt",
    ]

    for slug in slugs:
        try:
            gs = GradeSubject.objects.get(slug=slug)
            Chapter.objects.filter(grade_subject=gs).delete()
        except GradeSubject.DoesNotExist:
            pass


class Migration(migrations.Migration):

    dependencies = [
        ("content", "0012_gen_elec_elec_3_as"),
    ]

    operations = [
        migrations.RunPython(create_histgeo_content, reverse_func),
    ]
