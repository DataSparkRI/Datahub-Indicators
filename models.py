from django.db import models
from django.db.models import Q
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic

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
    short = models.CharField(max_length=4)
    short_name = models.CharField(max_length=12) # to display in lists, etc
    name = models.CharField(max_length=100)
    url = models.URLField(verify_exists=False)
    icon_path = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    
    def __unicode__(self):
        return self.name

class IndicatorManager(models.Manager):
    pass

class Indicator(models.Model):    
    name = models.CharField(max_length=100,blank=False,unique=True) # unique element name, not visible
    file_name = models.CharField(max_length=100, blank=True)
    
    min = models.IntegerField(null=True,blank=True)
    max = models.IntegerField(null=True,blank=True)
    display_name = models.CharField(max_length=100)   
    short_label = models.CharField(max_length=300)
    short_definition = models.TextField()
    long_definition = models.TextField()
    purpose = models.TextField() # aka rationale/implications    
    raw_tags = models.TextField() # will be parsed later into actual tag values
    unit = models.CharField(max_length=10, choices=UNIT_CHOICES, default='other')
    
    
    type = models.CharField(max_length=9,choices=INDICATOR_TYPES)
    data_type = models.CharField(max_length=7,choices=DATA_TYPE_CHOICES,blank=False)
    
    # calculated meta-data and fields
    slug = models.SlugField(unique=True,db_index=True,null=False)
    years_available = models.CharField(max_length=200)
    datasources = models.ManyToManyField(DataSource)
    
    objects = IndicatorManager()
    
    class Meta:
        pass
    
    def weave_name(self):
        return self.display_name
    
    def get_time_types_available(self):
        return self.indicatordata_set.values_list('time_type',flat=True).distinct()
    
    def get_key_unit_types_available(self):
        return self.values_list('key_unit_type',flat=True).distinct()
    
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
    
    def calculate_metadata(self):
        self.years_available = ','.join(sorted(map(
            lambda sy: str(school_year_to_year(sy)), 
            self.get_time_keys_available()
        )))
    
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
