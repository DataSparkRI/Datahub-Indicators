from django.core.management.base import BaseCommand, CommandError
from indicators.models import *
from weave.models import *


class Command(BaseCommand):
    def handle(self, *args, **options):
        for wmp in WeaveMetaPublic.objects.filter(meta_name="object_id"):
            ind = Indicator.objects.get(pk=wmp.meta_value)
            ind_key_type = ind.indicatordata_set.all()[:1][0].key_unit_type
            # we need to insert a keyType meta data asociated with each entity
            WeaveMetaPublic.objects.create(entity_id=wmp.entity_id, meta_name="keyType", meta_value=ind_key_type)

        print "Job Done."



