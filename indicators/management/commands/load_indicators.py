from django.core.management.base import BaseCommand, CommandError
from optparse import make_option
import sys

class Command(BaseCommand):
    option_list = BaseCommand.option_list# + (
    help = ''
    args = '[indicator_group_name]'

    def handle(self, *args, **options):
        from indicators.load import DataImporter
        from indicators.models import Indicator
        indicator_list = None
        if len(args) == 1:
            indicator_list = Indicator.objects.filter(name=args[0])
        DataImporter().run_all(indicator_list=indicator_list,ignore_celery=False)
