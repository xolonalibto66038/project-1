from django.db import migrations
from django.utils.text import slugify


def create_science_content(apps, schema_editor):
    GradeSubject = apps.get_model("curriculum", "GradeSubject")
    Chapter = apps.get_model("content", "Chapter")
    Course = apps.get_model("content", "Course")

    grade_subject_slugs = [
        "3as-sci-se",
        "3as-sci-math",
    ]

    data = [
        {
            "chapter": "تركيب البروتين",
            "courses": [
                "تذكير بالمكتسبات",
                "مقر تركيب البروتين",
                "استنساخ المعلومات الوراثية الموجودة على مستوى ADN",
                "الترجمة",
                "مراحل الترجمة",
            ],
        },
        {
            "chapter": "العلاقة بين بنية ووظيفة البروتين",
            "courses": [
                "تمثيل البنية الفراغية للبروتين",
                "مستويات البنية الفراغية للبروتينات",
                "العلاقة بين بنية ووظيفة البروتين",
            ],
        },
        {
            "chapter": "النشاط الإنزيمي للبروتينات",
            "courses": [
                "مفهوم الإنزيم وأهميته",
                "النشاط الإنزيمي وعلاقته ببنية الإنزيم",
                "دراسة تأثير تغير درجة pH الوسط على نشاط الإنزيم",
                "دراسة تأثير تغيرات درجة الحرارة على نشاط الإنزيم",
            ],
        },
        {
            "chapter": "دور البروتينات في الدفاع عن الذات",
            "courses": [
                "تذكير بالمكتسبات",
                "الذات واللاذات",
                "الجزيئات الدفاعية في الحالة الأولى",
                "المعقد المناعي",
                "مصدر الأجسام المضادة",
                "العناصر الدفاعية في الحالة الثانية",
                "طرق تأثير اللمفاويات LTc",
                "مصدر اللمفاويات LTc",
                "تحفيز الخلايا LB و LB",
                "اختيار نمط الاستجابة المناعية",
                "سبب فقدان المناعة المكتسبة",
            ],
        },
        {
            "chapter": "دور البروتينات في الاتصال العصبي",
            "courses": [
                "تذكير بالمكتسبات",
                "النقل المشبكي (الكمون الغشائي)",
                "آلية النقل المشبكي",
                "كمون الراحة",
                "كمون العمل",
                "آلية الإدماج العصبي",
                "تأثير المخدرات على مستوى المشابك",
            ],
        },
        {
            "chapter": "آليات تحويل الطاقة الضوئية إلى طاقة كيميائية كامنة",
            "courses": [
                "تذكير بالمكتسبات (شروط عملية التركيب الضوئي ومظاهره)",
                "مقر عملية التركيب الضوئي - ما فوق البنية الخلوية للصانعة الخضراء",
                "تفاعلات المرحلة الكيموضوئية",
                "تفاعلات المرحلة الكيموحيوية",
            ],
        },
        {
            "chapter": "آليات تحويل الطاقة الكيميائية الكامنة في الجزيئات العضوية إلى ATP",
            "courses": [
                "تذكير بالمكتسبات",
                "مقر الأكسدة التنفسية",
                "التحلل السكري",
                "مراحل تفكك حمض البيروفيك (تفاعلات حلقة كريبس)",
                "الفسفرة التأكسدية",
                "آليات تحويل الطاقة الكيميائية الكامنة في وسط لا هوائي",
            ],
        },
        {
            "chapter": "تحويل الطاقة على المستوى ما فوق البنية الخلوية",
            "courses": ["التحولات الطاقوية على المستوى الخلوي"],
        },
        {
            "chapter": "النشاط التكتوني للصفائح",
            "courses": [
                "تحديد الصفائح التكتونية",
                "حركات الصفائح التكتونية",
                "الطاقة الداخلية للكرة الأرضية",
            ],
        },
        {
            "chapter": "بنية الكرة الأرضية",
            "courses": [
                "الموجات الزلزالية",
                "التركيب الكيميائي لصخور القشرة الأرضية والمعطف (البرنس)",
                "نمذجة البنية الداخلية للكرة الأرضية",
            ],
        },
        {
            "chapter": "النشاط التكتوني والبنيات الجيولوجية المرتبطة به",
            "courses": [
                "الظواهر المرتبطة بالبناء (خصائص الظهرات وسط محيطية)",
                "المغماتية وتشكل اللوح المحيطي",
                "تشكل الصخور المميزة للظهرة وسط محيطية",
                "الظواهر المرتبطة بالغوص",
                "اختفاء اللوح المحيطي والظواهر المرتبطة بالغوص",
                "التضاريس الناجمة عن التصادم",
                "شواهد التقلص",
                "شواهد محيط قديم",
            ],
        },
    ]

    for grade_subject_slug in grade_subject_slugs:
        grade_subject = GradeSubject.objects.get(slug=grade_subject_slug)
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


def reverse_science_content(apps, schema_editor):
    GradeSubject = apps.get_model("curriculum", "GradeSubject")
    Chapter = apps.get_model("content", "Chapter")

    slugs = ["3as-sci-se", "3as-sci-math"]
    for slug in slugs:
        try:
            gs = GradeSubject.objects.get(slug=slug)
            Chapter.objects.filter(grade_subject=gs).delete()
        except GradeSubject.DoesNotExist:
            pass


class Migration(migrations.Migration):

    dependencies = [
        ("content", "0022_phy_sci_3_as"),
    ]

    operations = [
        migrations.RunPython(create_science_content, reverse_science_content),
    ]
