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

    def test_calendar_year(self):
        """
        Tests that "Calendar Year 2005" gets turned into "2005" in weave.
        """
        from indicators.models import Indicator, IndicatorData
        from indicators.load import WeaveExporter
        from weave.models import AttributeColumn
        
        i = Indicator.objects.create(
            name='test',
            display_name='test'
        )
        IndicatorData.objects.create(indicator=i, time_type='Calendar Year', time_key = "2005", key_unit_type = "School", key_value = "00001", data_type = 'numeric', numeric = 100)
        
        WeaveExporter().run()

        self.failUnlessEqual(AttributeColumn.objects.all().count(), 1)
        self.failUnlessEqual(AttributeColumn.objects.all()[0].year, '2005')

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


