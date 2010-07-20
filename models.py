from django.db import models

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

# Create your models here.
class Indicator(models.Model):
    name = models.CharField(max_length=100,blank=False)
    file_name = models.CharField(max_length=100)
    #key_field_name = models.CharField(max_length=100)
    #category = models.ForeignKey('Category',null=True,blank=True,related_name='indicators')
    key_unit_type = models.CharField(max_length=30) # FIXME: should go away
    
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
    # outlier index
    # match rate
    # possible values
    # etc etc
    
    class Meta:
        unique_together = (
            ('name', 'key_unit_type', ),
        )

    def weave_name(self, data_filter=None, year=None):
        if not self.short_label:
            basic_name = self.name
        else:
            basic_name = self.short_label
            if self.short_label_prefix:
                basic_name = u"%s %s" % (self.short_label_prefix, basic_name)
        if data_filter and year:
            return u"%s (%s) (%s)" % (basic_name, data_filter.name, year)
        if data_filter and not year:
            return u"%s (%s)" % (basic_name, data_filter.name)
        if not data_filter and year:
            return u"%s (%s)" % (basic_name, year)
        return basic_name 
            

    def get_time_types_available(self):
        return self.indicatordata_set.values_list('time_type',flat=True).distinct()
    
    def get_key_unit_types_available(self):
        return self.values_list('key_unit_type',flat=True).distinct()
    
    def get_time_keys_available(self, time_type):
        return self.indicatordata_set.values_list('time_key',flat=True).distinct()

    def get_key_values_available(self, key_unit_type):
        return self.indicatordata_set.values_list('key_value',flat=True).distinct()

    def save(self, *args, **kwargs):
        from webportal.unique_slugify import unique_slugify
        unique_slugify(self, "%s %s" % (self.short_label, self.key_unit_type))
        super(Indicator, self).save(*args, **kwargs)

class IndicatorData(models.Model):
    indicator = models.ForeignKey(Indicator)
    name = models.CharField(max_length=100,db_index=True)
    time_type = models.CharField(max_length=50,choices=TIME_CHOICES,null=True,blank=True,db_index=True)
    time_key = models.CharField(max_length=10,blank=True,null=True,db_index=True)
    key_unit_type = models.CharField(max_length=50,choices=KEY_UNIT_TYPE_CHOICES,db_index=True)
    key_value = models.CharField(max_length=100,db_index=True)
    data_type = models.CharField(max_length=7,choices=DATA_TYPE_CHOICES)
    numeric = models.FloatField(null=True)
    string = models.CharField(max_length=100,null=True)
