import datetime
import random
from cStringIO import StringIO

from django.db import models
from django.db.models import Q
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from taggit.managers import TaggableManager

#from weave.models import AttributeColumn
from indicators.conversion import school_year_to_year
from indicators.fields import RoundingDecimalField

INDICATOR_TYPES = (
    ('csv', 'csv'),
    ('generated', 'generated'),
)
TIME_CHOICES = (
    ('School Year', 'School Year'),
)
KEY_UNIT_TYPE_CHOICES = (
    ('School', 'School'),
    ('District', 'District'),
)
DATA_TYPE_CHOICES = (
    ('numeric', 'numeric'),
    ('string', 'string'),
)

UNIT_CHOICES = (
    ('percent', 'percent'), # zero decimal places
    ('count', 'count'),     # zero decimal places
    ('rate', 'rate'),       # two decimal places
    ('other', 'other') ,    # two decimal places
)


class DataSource(models.Model): 
    short = models.CharField(max_length=11)
    short_name = models.CharField(max_length=12) # to display in lists, etc
    name = models.CharField(max_length=100)
    url = models.URLField(verify_exists=False)
    icon_file = models.ImageField(upload_to='datasource_icons', blank=True, null=True)
    description = models.TextField(blank=True)
    
    def __unicode__(self):
        return self.name
    
    def icon_path(self):
        return self.icon_file.url

class IndicatorPregenPart(models.Model):
    indicator = models.ForeignKey('Indicator')
    file_name = models.CharField(max_length=100)
    column_name = models.CharField(max_length=100)
    key_type = models.CharField(max_length=100)
    time_type = models.CharField(max_length=100)
    time_value = models.CharField(max_length=100)
    key_column = models.CharField(max_length=100,blank=True)
    
    def __unicode__(self):
        return u"%s in %s" % (self.column_name, self.file_name)

class IndicatorManager(models.Manager):
    def get_for_def(self, indicator_def, using='portal'):
        import re
        name = indicator_def.__name__

        # This might not be an exact reversal of resolve_indicator_def
        # in all cases, but functions well enough
        name = re.sub(r'Num(?=[A-Z0-9])', '#', name)
        name = re.sub(r'Pct(?=[A-Z0-9])', '#', name)

        possible_names = []
        possible_names.append(name)
        possible_names.append(re.sub(r'Indicator$','',name))
        return self.using(using).get(Q(name__iexact=possible_names[0]) | Q(name__iexact=possible_names[1]))
    
class Indicator(models.Model):    
    #qualitative information
    name = models.CharField(max_length=100,blank=False,unique=True) # unique element name, not visible
    file_name = models.CharField(max_length=100, blank=True)
    display_name = models.CharField(max_length=100)   
    short_definition = models.TextField()
    long_definition = models.TextField(help_text="This field is Markdown enabled.")
    purpose = models.TextField(blank=True, help_text="This field is Markdown enabled.") # aka rationale/implications
    universe = models.CharField(max_length=300, blank=True)
    limitations = models.TextField(blank=True)
    routine_use = models.TextField(blank=True)
    last_audited = models.DateTimeField(blank=True, null=True, help_text="Blank or null means it has never been audited")
    
    #quantitative information
    min = models.IntegerField(null=True,blank=True)
    max = models.IntegerField(null=True,blank=True)
    unit = models.CharField(max_length=10, choices=UNIT_CHOICES, default='other')
    #type = models.CharField(max_length=9,choices=INDICATOR_TYPES)
    data_type = models.CharField(max_length=7,choices=DATA_TYPE_CHOICES,blank=False)
    raw_tags = models.TextField() # will be parsed later into actual tag values
    raw_datasources = models.TextField() # will be parsed into datasource relations
    notes = models.TextField(blank=True) # internal use misc notes
    
    
    
    # calculated meta-data and fields
    data_levels_available = models.CharField(max_length=200, blank=True)
    query_level = models.CharField(max_length=100, blank=True)
    suppression_numerator = models.IntegerField(null=True, blank=True)
    suppression_denominator = models.IntegerField(null=True, blank=True)
    years_available_display = models.CharField(max_length=200)
    years_available = models.CommaSeparatedIntegerField(max_length=200)
    datasources = models.ManyToManyField(DataSource)
    
    published = models.BooleanField(default=True)
    retired =models.BooleanField(default=False)
    visible_in_all_lists = models.BooleanField(default=False)
    
    slug = models.SlugField(unique=True,db_index=True,null=False)
    tags = TaggableManager(blank=True)

    load_pending = models.BooleanField(default=False)
    last_load_completed = models.DateTimeField(null=True,blank=True)
    
    objects = IndicatorManager()
    
    class Meta:
        pass
    
    def weave_name(self):
        return self.display_name

    def weave_title(self, time_key):
        return u"%s, %s" % (self.display_name, time_key, )

    def get_time_types_available(self):
        return self.indicatordata_set.values_list('time_type',flat=True).distinct()
    
    def get_key_unit_types_available(self):
        return self.indicatordata_set.values_list('key_unit_type',flat=True).distinct()
    
    def get_years_available(self):
        return map(lambda sy: school_year_to_year(sy), self.get_time_keys_available())

    def get_time_keys_available(self):
        """ Shortcut, since currently indicators don't span time types """
        return self.indicatordata_set.filter(time_key__isnull=False).exclude(numeric__isnull=True,string__isnull=True).values_list('time_key',flat=True).distinct()

    #def get_time_keys_available(self, time_type):
    #    return self.indicatordata_set.values_list('time_key',flat=True).distinct()

    def get_key_values_available(self, key_unit_type):
        return self.indicatordata_set.values_list('key_value',flat=True).distinct()

    def sorted_datasources(self):
        if not hasattr(self, '_sorted_datasources'):
            self._sorted_datasources = self.datasources.all().order_by('short')
        return self._sorted_datasources
    
    def set_years_available(self):
        """ Collapse a list of years into a single string that spans year ranges
        
        2000,2001,2002,2004 --> 2000-02,2004
        """
        years = set()
        for time_type, time_key in self.indicatordata_set.filter(time_key__isnull=False).exclude(numeric__isnull=True,string__isnull=True).values_list('time_type', 'time_key').distinct():
            if time_type == 'School Year':
                years.add(school_year_to_year(time_key))
            if time_type == 'Calendar Year':
                years.add(int(time_key.split('.')[0]))
        self.years_available = list(years)
        # FIXME: done in a rush, could be better
        years = sorted(years)
        ranged_sets = []
        last_year = None
        start = None
        for year in years:
            if not last_year:
                start = year
                last_year = year
            else:
                if year == last_year + 1:
                    last_year = year
                else:
                    if last_year == start:
                        if start:
                            ranged_sets.append(str(start))
                    else:
                        ranged_sets.append("%s-%s" % (start, str(last_year)[2:4]))
                    start = year
                    last_year = year
        
        if last_year == start:
            if start:
                ranged_sets.append(str(start))
        else:
            ranged_sets.append("%s-%s" % (start, str(last_year)[2:4]))
        
        if len(ranged_sets) > 0:
            self.years_available_display = ','.join(ranged_sets)
        else:
            self.years_available_display = ''

    def parse_tags(self):
        from taggit.utils import parse_tags
        self.tags.set(*parse_tags(self.raw_tags))

    def update_metadata(self):
        self.set_years_available()
        #self.parse_tags()
        #self.assign_datasources()
    
    def mark_load_complete(self):
        self.load_pending = False
        self.last_load_completed = datetime.datetime.now()

    def mark_load_pending(self):
        self.load_pending = True

    def assign_datasources(self):
        sources = map(lambda s: s.strip(), self.raw_datasources.split(','))
        self.datasources.clear()
        for source in sources:
            try:
                self.datasources.add(DataSource.objects.get(short__iexact=source))
            except DataSource.DoesNotExist:
                print "Couldn't find datasource to match '%s'" % source
    
    class MultipleDefinitionsFoundException(Exception): pass

    def resolve_indicator_def(self):
        """ Resolve the Indicator definition based on name.
        
        Translations to class names for matching:

            - Some Indicator classes end with "Indicator"
            - # and % might be in object names, but can't appear in class
              names. Translate to 'Num' and 'Pct'
        """
        from core.indicators import indicator_list

        possible_names = []

        translated_name = self.name
        translated_name = translated_name.replace('#', 'Num')
        translated_name = translated_name.replace('%', 'Pct')
        translated_name = translated_name.replace(' ', '')
        translated_name = translated_name.upper()

        possible_names.append(translated_name)
        possible_names.append(translated_name + 'INDICATOR')
        
        resolved_def = None
        for indicator_def in indicator_list(include_new=True):
            if indicator_def.__name__.upper() in possible_names:
                if resolved_def:
                    print "Found multiple definitions for %s:" % self.name
                    print "\t%s" % resolved_def
                    print "\t%s\n\n" % indicator_def
                    raise Indicator.MultipleDefinitionsFoundException("Found multiple definitions for this Indicator")
                resolved_def = indicator_def
        
        return resolved_def

    def save(self, *args, **kwargs):
        from webportal.unique_slugify import unique_slugify
        unique_slugify(self, "%s" % (self.name, ))
        self.update_metadata()
        super(Indicator, self).save(*args, **kwargs)

    def __unicode__(self):
        return self.name

class IndicatorData(models.Model):
    indicator = models.ForeignKey(Indicator)
    #name = models.CharField(max_length=100,db_index=True)
    time_type = models.CharField(max_length=50,choices=TIME_CHOICES,null=True,blank=True,db_index=True)
    time_key = models.CharField(max_length=10,blank=True,null=True,db_index=True)
    key_unit_type = models.CharField(max_length=50,choices=KEY_UNIT_TYPE_CHOICES,db_index=True)
    key_value = models.CharField(max_length=100,db_index=True)
    data_type = models.CharField(max_length=7,choices=DATA_TYPE_CHOICES)
    numeric = RoundingDecimalField(max_digits=20, decimal_places=2, blank=True, null=True)
    string = models.CharField(max_length=100,null=True)
    
    @property
    def value(self):
        # FIXME: why is this still inconsistent? check loading process
        if self.data_type.lower() in ('string', 'text'):
            return self.string
        if self.data_type.lower() in ('numeric',):
            return self.numeric

def _default_ilist_name(user):
    return "%s's Indicators" % user.email

class IndicatorListManager(models.Manager):
    def get_or_create_default_for_user(self, user):
        default_list_name = _default_ilist_name(user)
        list, created = self.get_or_create(owner=user, name=default_list_name)
        return list, created
    
    def create_for_user(self, user, name):
        return self.create(
            owner=user,
            name=name
        )


class IndicatorList(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200,unique=True)
    public = models.BooleanField(default=False)
    visible_in_default = models.BooleanField(default=False)
    owner = models.ForeignKey(User,null=True,blank=True)
    created = models.DateField(auto_now_add=True)
    visible_in_weave = models.BooleanField(default=True)
    indicators = models.ManyToManyField(Indicator)
    
    objects = IndicatorListManager()
    
    @property
    def attribute_column_Q(self):
        return Q(content_type=ContentType.objects.get_for_model(Indicator)) & \
            (
                Q(object_id__in=self.indicators.values_list('id',flat=True)) | \
                Q(object_id__in=Indicator.objects.filter(visible_in_all_lists=True))
            )
   
    @property
    def can_be_deleted(self):
        return self.name != _default_ilist_name(self.owner)

    def save(self, *args, **kwargs):
        from webportal.unique_slugify import unique_slugify
        unique_slugify(self, "%s %s" % (self.owner.username, self.name, ))
        super(IndicatorList, self).save(*args, **kwargs)

    def __unicode__(self):
        return self.name
    
    @models.permalink
    def get_absolute_url(self):
        return ('indicators-indicator_list', [], {'indicator_list_slug': self.slug})

    class Meta:
        unique_together = (
            ('name', 'owner', ),
        )

class AnonymizedEnrollmentManager(models.Manager):
    def _insert_batch(self, cursor, columns, rows):
        copy_contents = StringIO('%s\n\.\n' % '\n'.join(rows))
        cursor.copy_from(
            copy_contents, 
            'indicators_anonymizedenrollment', 
            columns=columns
        )

    def bulk_insert(self, records):
        """ Expects a list of dict-based record definitions """
        from django.db import connections, transaction
        cursor = connections['portal'].cursor()
        
        batch_size = 100000
        row_sqls = []
        count = 0
        columns = ('id', '"school_year"', '"SASID"', '"distCode"', '"grade"', 
                   '"enroll_date"', '"exit_date"', '"exit_type"')
        
        sasid_map = {'max': 0}
        def _munge_SASID(sasid):
            """ Use a simple map to munge SASIDs in the anonymized dataset """
            if not sasid_map.has_key(sasid):
                max_sasid = sasid_map['max'] + 1
                sasid_map[sasid] = max_sasid
                sasid_map['max'] = max_sasid
            return sasid_map[sasid]

        def _prep(val):
            """ Turn None into '\N' so null values are inserted """
            if val is None:
                return '\N'
            return str(val)
        
        for record in records:
            count += 1
            row_sqls.append("%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s" % (
                _prep(count),
                _prep(record[0]),
                _prep(_munge_SASID(record[1])),
                _prep(record[2]),
                _prep(record[3]),
                _prep(record[4]),
                _prep(record[5]),
                _prep(record[6]),
            ))
            
            if count % batch_size == 0:
                self._insert_batch(cursor, columns, row_sqls)
                row_sqls = []
                print "Inserted batch..."
        self._insert_batch(cursor, columns, row_sqls)
        
        connections['portal'].connection.commit()
        print "Complete"

    def list_available_school_years(self):
        """
        Returns a list of possible values for 'school_year'.
        """
        # TODO: This should be high on the list of funtions to cache.
        return self.values_list('school_year', flat=True).distinct()

    def filter_by_year(self, year):
        """
        Returns a filtered QuerySet of records enrolled on Oct. 1st of year.
        """
        # Ensure we're working with an integer.
        year = int(year) # TODO: Catch exceptions here.

        start_enroll_date = datetime.date(year, 8, 1)
        end_enroll_date =   datetime.date(year, 10, 1)

        start_exit_date =   datetime.date(year, 10, 2)
        end_exit_date =     datetime.date(year + 1, 10, 1)
        
        return self.filter(
            enroll_date__range=(start_enroll_date, end_enroll_date)
        ).filter(
            exit_date__range=(start_exit_date, end_exit_date)
        )

class AnonymizedEnrollment(models.Model):
    """
    Provides an anonymized version of enrollment records for the churning chart.

    SASID is scrambled, so they can still be used for churning purposes, but have
    no relation to the original SASID. Only fields currently necessary for the
    churning chart are copied.
    """
    school_year = models.CharField(max_length=9,db_index=True)
    SASID = models.IntegerField(db_index=True)
    distCode = models.CharField(max_length=2,db_index=True)
    grade = models.CharField(max_length=50,db_index=True)
    enroll_date = models.DateField(null=True)
    exit_date = models.DateField(null=True)
    exit_type = models.CharField(max_length=200)
    
    objects = AnonymizedEnrollmentManager()
