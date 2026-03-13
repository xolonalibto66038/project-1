from django.db import migrations
from django.utils.text import slugify


def create_physics_content(apps, schema_editor):
    GradeSubject = apps.get_model("curriculum", "GradeSubject")
    Chapter = apps.get_model("content", "Chapter")
    Course = apps.get_model("content", "Course")
    # Tag = apps.get_model("content", "Tag")

    grade_subject_slugs = [
        "3as-phys-mec",
        "3as-phys-elec",
        "3as-phys-proc",
        "3as-phys-math",
        "3as-phys-se",
        "3as-phys-civil",
    ]

    data = [
        {
            "chapter": "تطور كميات المتفاعلات والنواتج خلال تحول كيميائي في محلول مائي",
            "courses": [
                "المدة المستغرقة في تحول جملة كيميائية",
                "المتابعة الزمنية لتحول كيميائي",
                "العوامل الحركية",
                "أهمية العوامل الحركية",
            ],
            "tags": [
                "التحولات السريعة",
                "التحولات البطيئة",
                "التحول الكيميائي البطيء جدًا",
                "المتابعة عن طريق قياس الناقلية",
                "المتابعة عن طريق المعايرة",
                "سرعة التفاعل",
                "زمن نصف التفاعل",
                "درجة الحرارة",
                "التركيز الابتدائي للمتفاعل",
                "التفسير المجهري",
                "الوساطة",
                "تأثير درجة الحرارة",
                "تأثير التركيز المولي للمتفاعلات",
                "أهمية الوسيط",
            ],
        },
        {
            "chapter": "التحولات النووية",
            "courses": [
                "البنية النووية",
                "النشاط الإشعاعي",
                "التناقص الإشعاعي",
                "التفاعلات النووية",
                "الانشطار والاندماج",
            ],
            "tags": [
                "النموذج النووي",
                "النظائر",
                "القوة النووية القوية",
                "الاستقرار النووي",
                "الخواص النووية",
                "أنواع التفكك α β γ",
                "الطابع العشوائي للتناقص",
                "وحدة النشاط الإشعاعي Bq",
                "نصف العمر",
                "قانون التناقص الإشعاعي",
                "تطبيق الإشعاع للتأريخ",
                "التفاعلات التلقائية والمفتعلة",
                "المظهر الطاقوي للتفاعلات النووية",
                "طاقة الربط",
                "الانشطار",
                "الاندماج",
            ],
        },
        {
            "chapter": "دراسة ظواهر كهربائية",
            "courses": [
                "المكثفات وثنائي القطب RC",
                "الوشيعة وثنائي القطب RL",
                "الطاقة المخزنة في وشيعة",
            ],
            "tags": [
                "خصائص المكثفة",
                "شحن وتفريغ مكثفة",
                "تطور التوتر الكهربائي",
                "الطاقة المخزنة في مكثفة",
                "وصف الوشيعة",
                "تطور التيار في وشيعة",
                "الطاقة المخزنة في وشيعة",
            ],
        },
        {
            "chapter": "تطور حالة جملة كيميائية خلال تحول كيميائي نحو حالة التوازن",
            "courses": [
                "pH محلول مائي",
                "محلول حمضي ومحلول أساسي",
                "تطور جملة نحو التوازن",
                "التحولات حمض-أساس",
            ],
            "tags": [
                "تعريف pH",
                "تعيين pH",
                "حمض قوي وضعيف",
                "أساس قوي وضعيف",
                "مقارنة التقدم النهائي والأعظمي",
                "مفهوم حالة التوازن",
                "تأثير الحالة الابتدائية",
                "حالة التوازن الديناميكي",
                "المحاليل المائية",
                "ثوابت Ka و Kb و pKa",
                "تطبيق الكاشف اللوني",
                "المعايرة pH مترية",
            ],
        },
        {
            "chapter": "تطور جملة ميكانيكية",
            "courses": [
                "مقارنة تاريخية لميكانيك نيوتن",
                "شرح حركة كوكب أو قمر إصطناعي",
                "دراسة حركة السقوط الشاقولي",
                "تطبيقات",
                "حدود ميكانيك نيوتن",
            ],
            "tags": [
                "نظرة تاريخية",
                "بعض المفاهيم الأساسية",
                "القوانين الثلاثة لنيوتن",
                "خصائص الحركة الدائرية المنتظمة",
                "حركة الكواكب والأقمار الاصطناعية",
                "قوانين كبلر",
                "السقوط الشاقولي",
                "السقوط الحقيقي",
                "السقوط الحر",
                "تطبيق القانون الثاني لنيوتن",
                "مبدأ انحفاظ الطاقة",
                "النسبية",
                "التطور الكمي",
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
                course = Course.objects.create(
                    # chapter=chapter,
                    grade_subject=grade_subject,
                    title=course_title,
                    order=co_order,
                    slug=course_slug,
                    term="first",
                )

                # create tags for course
                # for tag_name in item.get("tags", []):
                #     Tag.objects.get_or_create(course=course, title=tag_name)


def reverse_physics_content(apps, schema_editor):
    GradeSubject = apps.get_model("curriculum", "GradeSubject")
    Chapter = apps.get_model("content", "Chapter")

    slugs = [
        "3as-phys-mec",
        "3as-phys-elec",
        "3as-phys-proc",
        "3as-phys-math",
        "3as-phys-se",
        "3as-phys-civil",
    ]

    for slug in slugs:
        try:
            gs = GradeSubject.objects.get(slug=slug)
            Chapter.objects.filter(grade_subject=gs).delete()
        except GradeSubject.DoesNotExist:
            pass


class Migration(migrations.Migration):

    dependencies = [
        ("content", "0021_philo_sci_3_as"),
    ]

    operations = [
        migrations.RunPython(create_physics_content, reverse_physics_content),
    ]
