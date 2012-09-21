from django.test import TestCase
from indicators.models import *


class IndicatorTest(TestCase):

    def setUp(self):
        """ Put stuff here to happen before the tests run
            Ex: self.test_indicator = Indicator(bleh=1, blah="12")
        """
        pass

    def test_indicator_get_time_types(self):
        ind = Indicator(name="Test Indicator")
        ind.display_name = "test indicator"
        ind.short_definition = "Short definition"
        ind.long_definition = "This is the Long Def"
        ind.unit = "percent"
        ind.save()

        ind_data = IndicatorData(indicator=ind)
        ind_data.time_type = 'Multi-Year, '
        ind_data.time_key = '2009-2010'
        ind_data.string = "1"
        ind_data.save()

        ind_data = IndicatorData(indicator=ind)
        ind_data.time_type = 'Calendar Year, '
        ind_data.time_key = '2000.0'
        ind_data.string = "1"
        ind_data.save()

        ind_data = IndicatorData(indicator=ind)
        ind_data.time_type = 'School Year, '
        ind_data.time_key = '2006'
        ind_data.string = "1"
        ind_data.save()

        result = ind.get_types_and_times()
        print result
        #compare_to = {u'Multi-Year': [u'2009-10']}

        #self.assertEqual(result, compare_to)



