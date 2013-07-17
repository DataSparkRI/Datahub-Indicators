from django.test import TestCase
from indicators.models import *
from django.contrib.auth.models import User, AnonymousUser
import uuid

class IndicatorTest(TestCase):

    def setUp(self):
        self.testuser = User.objects.create(username="test", email="test@test.com", password="test")
        self.testuser2 = User.objects.create(username="test2", email="test2@test.com", password="test2")

    def create_indicator(self, published=True):
        ind = Indicator(name=uuid.uuid4())
        ind.display_name = "test indicator"
        ind.short_definition = "Short definition"
        ind.long_definition = "This is the Long Def"
        ind.unit = "percent"
        ind.published = published
        ind.save()
        return ind

    def test_user_perms(self):
        ind1 = self.create_indicator()
        ind2 = self.create_indicator(published=False)
        # create perms
        Permission.objects.create(user=self.testuser, indicator=ind2)

        self.assertEqual(Indicator.objects.get_for_user().count(), 1)

        for_user = Indicator.objects.get_for_user(self.testuser)
        self.assertEqual(for_user.count(), 2)
        self.assertFalse(for_user[1].published)

    def test_user_perms_single(self):
        ind1 = self.create_indicator()
        ind2 = self.create_indicator(published=False)
        # create perms
        Permission.objects.create(user=self.testuser, indicator=ind2)

        self.assertTrue(ind2.user_can_view(self.testuser))
        self.assertFalse(ind2.user_can_view(self.testuser2))
        self.assertTrue(ind1.user_can_view(self.testuser2)) #published indicator
        # annonymous users
        anon_user = AnonymousUser()
        self.assertFalse(ind2.user_can_view(anon_user))


    def test_indicator_get_time_types(self):
        #TODO this test is incomplete
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



