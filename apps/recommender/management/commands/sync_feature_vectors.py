# recommendations/management/commands/sync_feature_vectors.py

from django.core.management.base import BaseCommand

from ...signals import _upsert_vector

MODELS_TO_SYNC = [
    {
        "app_label": "content",
        "model_name": "Course",
        "select_related": [
            "chapter__grade_subject__grade__level",
            "chapter__grade_subject__subject",
            "chapter__grade_subject__specialty",
            "grade_subject__grade__level",
            "grade_subject__subject",
            "grade_subject__specialty",
        ],
    },
    {
        "app_label": "content",
        "model_name": "Resource",
        "select_related": [
            "course__chapter__grade_subject__grade__level",
            "course__chapter__grade_subject__subject",
            "course__chapter__grade_subject__specialty",
            "course__grade_subject__grade__level",
            "course__grade_subject__subject",
            "course__grade_subject__specialty",
            "grade_subject__grade__level",
            "grade_subject__subject",
            "grade_subject__specialty",
        ],
    },
]


class Command(BaseCommand):
    help = (
        "Backfill or repair ItemFeatureVector rows for all existing "
        "Resources and Courses. Safe to re-run — uses update_or_create."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--model",
            choices=[m["model_name"].lower() for m in MODELS_TO_SYNC],
            default=None,
            help="Limit sync to a single model (default: all).",
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=200,
            help="QuerySet iterator chunk size (default: 200).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Walk all objects and run extractors but do not write to the DB.",
        )

    def handle(self, *args, **options):
        # ensure extractors are registered before we start

        target = options["model"]
        batch = options["batch_size"]
        dry_run = options["dry_run"]

        if dry_run:
            self.stdout.write(self.style.WARNING("Dry-run mode — no DB writes."))

        models = (
            [m for m in MODELS_TO_SYNC if m["model_name"].lower() == target]
            if target
            else MODELS_TO_SYNC
        )

        grand_ok = grand_errors = 0

        for config in models:
            ok, errors = self._sync_model(config, batch, dry_run)
            grand_ok += ok
            grand_errors += errors

        summary = f"Finished — {grand_ok} synced, {grand_errors} errors."
        style = self.style.SUCCESS if grand_errors == 0 else self.style.WARNING
        self.stdout.write(style(summary))

    # ── Private ────────────────────────────────────────────────────────────────

    def _sync_model(self, config: dict, batch_size: int, dry_run: bool):
        from django.apps import apps

        model_name = config["model_name"]
        app_label = config["app_label"]

        model_class = apps.get_model(app_label, model_name)
        qs = model_class.objects.select_related(*config["select_related"]).iterator(
            chunk_size=batch_size
        )

        ok = errors = count = 0

        self.stdout.write(f"\nSyncing {app_label}.{model_name} ...")

        for instance in qs:
            count += 1
            try:
                if not dry_run:
                    success = _upsert_vector(instance)
                else:
                    from ...registry import get_features

                    success = get_features(instance) is not None

                if success:
                    ok += 1
                else:
                    errors += 1
                    self.stderr.write(
                        f"  [SKIP] {model_name} pk={instance.pk} "
                        "(no extractor or extraction failed — see logs)"
                    )
            except Exception as exc:
                errors += 1
                self.stderr.write(f"  [ERROR] {model_name} pk={instance.pk}: {exc}")

            if count % 100 == 0:
                self.stdout.write(f"  processed {count} ...")

        self.stdout.write(
            self.style.SUCCESS(
                f"  {model_name}: {ok} ok, {errors} errors ({count} total)."
            )
        )
        return ok, errors
