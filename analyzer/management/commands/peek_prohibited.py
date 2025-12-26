from django.core.management.base import BaseCommand
from analyzer.models import ProhibitedIngredient


class Command(BaseCommand):
    help = "Print counts and a sample of ProhibitedIngredient rows"

    def handle(self, *args, **options):
        total = ProhibitedIngredient.objects.count()
        cmr_count = ProhibitedIngredient.objects.filter(is_cmr=True).count()
        self.stdout.write(self.style.SUCCESS(f"Total rows: {total}"))
        self.stdout.write(self.style.SUCCESS(f"CMR rows:   {cmr_count}"))

        self.stdout.write("\nSample (first 10 by name):")
        for obj in ProhibitedIngredient.objects.order_by("name").only(
            "name", "cas_number", "ec_number", "is_cmr", "regulation"
        )[:10]:
            self.stdout.write(
                f"- {obj.name} | CAS: {obj.cas_number or '-'} | EC: {obj.ec_number or '-'} | "
                f"CMR: {'yes' if obj.is_cmr else 'no'} | Reg: {obj.regulation or '-'}"
            )
