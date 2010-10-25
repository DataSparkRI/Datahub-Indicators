from django.db import models
from django.db.models import Q
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from taggit.managers import TaggableManager

#from weave.models import AttributeColumn
from indicators.conversion import school_year_to_year

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
    ('percent', 'percent'),
    ('count', 'count'),
    ('rate', 'rate'),
    ('other', 'other') ,
)


class DataSource(models.Model):
    short = models.CharField(max_length=11)
    short_name = models.CharField(max_length=12) # to display in lists, etc
    name = models.CharField(max_length=100)
    url = models.URLField(verify_exists=False)
    icon_path = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    
    def __unicode__(self):
        return self.name

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
    pass

class Indicator(models.Model):    
    name = models.CharField(max_length=100,blank=False,unique=True) # unique element name, not visible
    file_name = models.CharField(max_length=100, blank=True)
    min = models.IntegerField(null=True,blank=True)
    max = models.IntegerField(null=True,blank=True)
    display_name = models.CharField(max_length=100)   
    short_definition = models.TextField()
    long_definition = models.TextField()
    purpose = models.TextField(blank=True) # aka rationale/implications    
    unit = models.CharField(max_length=10, choices=UNIT_CHOICES, default='other')
    #type = models.CharField(max_length=9,choices=INDICATOR_TYPES)
    data_type = models.CharField(max_length=7,choices=DATA_TYPE_CHOICES,blank=False)
    notes = models.TextField(blank=True) # internal use misc notes
    raw_tags = models.TextField() # will be parsed later into actual tag values
    raw_datasources = models.TextField() # will be parsed into datasource relations
    published = models.BooleanField(default=True)
    
    # calculated meta-data and fields
    slug = models.SlugField(unique=True,db_index=True,null=False)
    years_available_display = models.CharField(max_length=200)
    years_available = models.CommaSeparatedIntegerField(max_length=200)
    datasources = models.ManyToManyField(DataSource)
    
    visible_in_all_lists = models.BooleanField(default=False)
    
    tags = TaggableManager()     
    
    objects = IndicatorManager()
    
    class Meta:
        pass
    
    def weave_name(self):
        return self.display_name
    
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
        return self.datasources.all().order_by('short')
    
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

    def assign_datasources(self):
        sources = map(lambda s: s.strip(), self.raw_datasources.split(','))
        self.datasources.clear()
        for source in sources:
            try:
                self.datasources.add(DataSource.objects.get(short__iexact=source))
            except DataSource.DoesNotExist:
                print "Couldn't find datasource to match '%s'" % source
    
    def save(self, *args, **kwargs):
        from webportal.unique_slugify import unique_slugify
        unique_slugify(self, "%s" % (self.name, ))
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
    numeric = models.FloatField(null=True)
    string = models.CharField(max_length=100,null=True)
    
    @property
    def value(self):
        # FIXME: why is this still inconsistent? check loading process
        if self.data_type.lower() in ('string', 'text'):
            return self.string
        if self.data_type.lower() in ('numeric',):
            return self.numeric

class IndicatorListManager(models.Manager):
    def get_or_create_default_for_user(self, user):
        default_list_name = "%s's Indicators" % user.email
        list, created = self.get_or_create(owner=user, name=default_list_name)
        user.get_profile().indicator_lists.add(list)
        return list, created


class IndicatorList(models.Model):
    name = models.CharField(max_length=200,unique=True)
    slug = models.SlugField(max_length=200,unique=True)
    public = models.BooleanField(default=False)
    visible_in_default = models.BooleanField(default=False)
    owner = models.ForeignKey(User,null=True,blank=True)
    created = models.DateField(auto_now_add=True)
    indicators = models.ManyToManyField(Indicator)
    
    objects = IndicatorListManager()
    
    @property
    def attribute_column_Q(self):
        return Q(content_type=ContentType.objects.get_for_model(Indicator)) & \
            (
                Q(object_id__in=self.indicators.values_list('id',flat=True)) | \
                Q(object_id__in=Indicator.objects.filter(visible_in_all_lists=True))
            )
   

    def save(self, *args, **kwargs):
        from webportal.unique_slugify import unique_slugify
        unique_slugify(self, "%s" % (self.name, ))
        super(IndicatorList, self).save(*args, **kwargs)

    def __unicode__(self):
        return self.name
    
    @models.permalink
    def get_absolute_url(self):
        return ('indicators-list_hierarchy', [], {'indicator_list_slug': self.slug})
