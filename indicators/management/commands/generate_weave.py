from django.core.management.base import BaseCommand, CommandError
from indicators.util import generate_weave

class Command(BaseCommand):
    def handle(self, *args, **options):
        print "Generating Weave"
        generate_weave(verbose=True)
