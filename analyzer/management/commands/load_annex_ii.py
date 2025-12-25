import csv
from django.core.management.base import BaseCommand
from analyzer.models import ProhibitedIngredient

class Command(BaseCommand):
    help = 'Load Annex II prohibited ingredients from CSV'
    
    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='Path to CSV file')

    def handle(self, *args, **options):
        file_path = options['file_path']

        ProhibitedIngredient.objects.all().delete() #clear existing

        count = ProhibitedIngredient.objects.count()
        self.stdout.write(self.style.SUCCESS(f'SUCESS: Loaded {count} prohibited ingredients'))

    def load_csv(self, file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            # add the data from the csv file to the database (need check with the names)
            for row in reader:
                ProhibitedIngredient.objects.create(
                    name=row['ingredient_name'],
                    name_normalized=row['ingredient_name'].lower().strip(),
                    cas_number=row.get('cas_number', ''),
                    annex_ref=row.get('annex_reference', 'Annex II'),
                    is_cmr=row.get('is_cmr', 'false').lower() == 'true'
                )