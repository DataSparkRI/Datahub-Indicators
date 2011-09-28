from django.test import TestCase

class TimeTranslationTest(TestCase):
    def test_school_year(self):
        """
        Tests that "School Year 2005-2006" gets turned into "SY05-06" in weave.
        """
        from indicators.models import Indicator, IndicatorData
        from indicators.load import WeaveExporter
        from weave.models import AttributeColumn
        
        i = Indicator.objects.create(
            name='test',
            display_name='test'
        )
        IndicatorData.objects.create(indicator=i, time_type='School Year', time_key = "2005-2006", key_unit_type = "School", key_value = "00001", data_type = 'numeric', numeric = 100)
        
        WeaveExporter().run()

        self.failUnlessEqual(AttributeColumn.objects.all().count(), 1)
        self.failUnlessEqual(AttributeColumn.objects.all()[0].year, 'SY05-06')

    def test_blank_time_type(self):
        """
        Tests that blank time types can pass through type conversion.
        """
        from indicators.models import Indicator, IndicatorData
        from indicators.load import WeaveExporter
        from weave.models import AttributeColumn
        
        i = Indicator.objects.create(
            name='test',
            display_name='test'
        )
        IndicatorData.objects.create(indicator=i, time_type=None, time_key = None, key_unit_type = "School", key_value = "00001", data_type = 'numeric', numeric = 100)
        
        WeaveExporter().run()

        self.failUnlessEqual(AttributeColumn.objects.all().count(), 1)
        self.failUnlessEqual(AttributeColumn.objects.all()[0].year, '')

class RoundingDecimalTest(TestCase):
    def test_float_accepted(self):
        from django.core import exceptions
        from indicators.models import Indicator, IndicatorData
        i = Indicator.objects.create(name='test')
        try:
            data = IndicatorData.objects.create(indicator=i,numeric=1.123123123)
        except (TypeError, exceptions.ValidationError):
            self.fail("Float could not be used for the numeric field")
