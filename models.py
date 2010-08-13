from django.db import models
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

class IndicatorManager(models.Manager):
    pass

class Indicator(models.Model):
    name = models.CharField(max_length=100,blank=False)
    file_name = models.CharField(max_length=100)
    #key_field_name = models.CharField(max_length=100)
    #category = models.ForeignKey('Category',null=True,blank=True,related_name='indicators')
    key_unit_type = models.CharField(max_length=30) # FIXME: should go away
    
    #attributecolumns = generic.GenericRelation(AttributeColumn)
    
    min = models.IntegerField(null=True,blank=True)
    max = models.IntegerField(null=True,blank=True)

    # from Variable
    slug = models.SlugField(unique=True,db_index=True,null=False)
    display = models.BooleanField(default=True)
    dataset_tag = models.CharField(max_length=100)
    icon = models.CharField(max_length=100,null=True)
    short_label_prefix = models.CharField(max_length=100)
    short_label = models.CharField(max_length=300)
    hover_label = models.TextField()
    variable_definition = models.TextField()
    case_restrictions = models.TextField()
    category_one = models.CharField(max_length=300,null=True,blank=True)
    category_two = models.CharField(max_length=300,null=True,blank=True)
    category_three = models.CharField(max_length=300,null=True,blank=True)
    category_four = models.CharField(max_length=300,null=True,blank=True)
    
    type = models.CharField(max_length=9,choices=INDICATOR_TYPES)
    data_type = models.CharField(max_length=7,choices=DATA_TYPE_CHOICES,blank=False)
    # data type choices (percent, number, $, etc etc)
    
    # calculated meta-data

    years_available = models.CharField(max_length=200)
    datasource = models.CharField(max_length=200)
    
    # outlier index
    # match rate
    # possible values
    # etc etc

    objects = IndicatorManager()
    
    class Meta:
        unique_together = (
            ('name', 'key_unit_type', ),
        )

    def weave_name(self):
        return self.name
        if not self.short_label:
            basic_name = self.name
        else:
            basic_name = self.short_label
            if self.short_label_prefix:
                basic_name = u"%s %s" % (self.short_label_prefix, basic_name)
        return basic_name 
    
    def display_name(self):
        if self.short_label and self.short_label_prefix:
            return u"%s %s" % (self.short_label_prefix, self.short_label)
        if self.short_label:
            return self.short_label
        return self.name
    
    def get_time_types_available(self):
        return self.indicatordata_set.values_list('time_type',flat=True).distinct()
    
    def get_key_unit_types_available(self):
        return self.values_list('key_unit_type',flat=True).distinct()
    
    def get_years_available(self):
        return map(lambda sy: school_year_to_year(sy), self.get_time_keys_available())

    def get_time_keys_available(self):
        """ Shortcut, since currently indicators don't span time types """
        return self.indicatordata_set.filter(time_key__isnull=False).values_list('time_key',flat=True).distinct()

    #def get_time_keys_available(self, time_type):
    #    return self.indicatordata_set.values_list('time_key',flat=True).distinct()

    def get_key_values_available(self, key_unit_type):
        return self.indicatordata_set.values_list('key_value',flat=True).distinct()

    def calculate_metadata(self):
        self.years_available = ','.join(sorted(map(
            lambda sy: str(school_year_to_year(sy)), 
            self.get_time_keys_available()
        )))
    
    def save(self, *args, **kwargs):
        from webportal.unique_slugify import unique_slugify
        unique_slugify(self, "%s %s" % (self.short_label, self.key_unit_type))
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
