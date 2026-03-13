from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify

from ...models import GradeSubject


class Command(BaseCommand):
    help = "Populate missing slugs for GradeSubject objects"

    @transaction.atomic
    def handle(self, *args, **options):
        queryset = GradeSubject.objects.select_related("grade", "subject", "specialty")

        updated = 0

        for obj in queryset:
            if obj.slug:
                continue

            spec = obj.specialty.short_name if obj.specialty else "all"

            obj.slug = slugify(
                f"{obj.grade.short_name}-{obj.subject.short_name}-{spec}"
            )

            obj.save(update_fields=["slug"])
            updated += 1

        self.stdout.write(
            self.style.SUCCESS(f"Successfully updated {updated} GradeSubject slugs.")
        )
