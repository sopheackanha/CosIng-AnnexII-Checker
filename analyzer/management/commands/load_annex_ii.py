import csv
import re
from django.core.management.base import BaseCommand
from analyzer.models import ProhibitedIngredient
from analyzer.services.normalizer import normalize_name


class Command(BaseCommand):
    help = 'Load Annex II prohibited ingredients from CSV'

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='Path to CSV file')

    def handle(self, *args, **options):
        file_path = options['file_path']

        # Clear existing data
        ProhibitedIngredient.objects.all().delete()

        # Load CSV
        self.load_csv(file_path)

        # Report result
        count = ProhibitedIngredient.objects.count()
        self.stdout.write(
            self.style.SUCCESS(f'SUCCESS: Loaded {count} prohibited ingredients')
        )

    def normalize_name(self, name: str) -> str:
        # Delegate to shared normalizer for consistency
        return normalize_name(name)

    def load_csv(self, file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            for row in reader:
                raw_name = row.get('Chemical name / INN', '').strip()
                cmr_raw = row.get('CMR', '').strip()

                if not raw_name:
                    continue

                ProhibitedIngredient.objects.create(
                    name=raw_name,
                    name_normalized=self.normalize_name(raw_name),
                    cas_number=row.get('CAS Number', '').strip(),
                    ec_number=row.get('EC Number', '').strip(),
                    regulation=row.get('Regulation', '').strip(),
                    is_cmr=bool(cmr_raw),
                    cmr_note=cmr_raw
                )
