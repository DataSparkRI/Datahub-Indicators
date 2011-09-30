# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Indicator'
        db.create_table('indicators_indicator', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('file_name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('key_unit_type', self.gf('django.db.models.fields.CharField')(max_length=30)),
            ('min', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('max', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('slug', self.gf('django.db.models.fields.SlugField')(unique=True, max_length=50, db_index=True)),
            ('display', self.gf('django.db.models.fields.BooleanField')(default=True, blank=True)),
            ('dataset_tag', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('icon', self.gf('django.db.models.fields.CharField')(max_length=100, null=True)),
            ('short_label_prefix', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('short_label', self.gf('django.db.models.fields.CharField')(max_length=300)),
            ('hover_label', self.gf('django.db.models.fields.TextField')()),
            ('variable_definition', self.gf('django.db.models.fields.TextField')()),
            ('case_restrictions', self.gf('django.db.models.fields.TextField')()),
            ('category_one', self.gf('django.db.models.fields.CharField')(max_length=300, null=True, blank=True)),
            ('category_two', self.gf('django.db.models.fields.CharField')(max_length=300, null=True, blank=True)),
            ('category_three', self.gf('django.db.models.fields.CharField')(max_length=300, null=True, blank=True)),
            ('category_four', self.gf('django.db.models.fields.CharField')(max_length=300, null=True, blank=True)),
            ('type', self.gf('django.db.models.fields.CharField')(max_length=9)),
            ('data_type', self.gf('django.db.models.fields.CharField')(max_length=7)),
            ('years_available', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('datasource', self.gf('django.db.models.fields.CharField')(max_length=100)),
        ))
        db.send_create_signal('indicators', ['Indicator'])

        # Adding unique constraint on 'Indicator', fields ['name', 'key_unit_type']
        db.create_unique('indicators_indicator', ['name', 'key_unit_type'])

        # Adding model 'IndicatorData'
        db.create_table('indicators_indicatordata', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('indicator', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['indicators.Indicator'])),
            ('time_type', self.gf('django.db.models.fields.CharField')(db_index=True, max_length=50, null=True, blank=True)),
            ('time_key', self.gf('django.db.models.fields.CharField')(db_index=True, max_length=10, null=True, blank=True)),
            ('key_unit_type', self.gf('django.db.models.fields.CharField')(max_length=50, db_index=True)),
            ('key_value', self.gf('django.db.models.fields.CharField')(max_length=100, db_index=True)),
            ('data_type', self.gf('django.db.models.fields.CharField')(max_length=7)),
            ('numeric', self.gf('django.db.models.fields.FloatField')(null=True)),
            ('string', self.gf('django.db.models.fields.CharField')(max_length=100, null=True)),
        ))
        db.send_create_signal('indicators', ['IndicatorData'])


    def backwards(self, orm):
        
        # Deleting model 'Indicator'
        db.delete_table('indicators_indicator')

        # Removing unique constraint on 'Indicator', fields ['name', 'key_unit_type']
        db.delete_unique('indicators_indicator', ['name', 'key_unit_type'])

        # Deleting model 'IndicatorData'
        db.delete_table('indicators_indicatordata')


    models = {
        'indicators.indicator': {
            'Meta': {'unique_together': "(('name', 'key_unit_type'),)", 'object_name': 'Indicator'},
            'case_restrictions': ('django.db.models.fields.TextField', [], {}),
            'category_four': ('django.db.models.fields.CharField', [], {'max_length': '300', 'null': 'True', 'blank': 'True'}),
            'category_one': ('django.db.models.fields.CharField', [], {'max_length': '300', 'null': 'True', 'blank': 'True'}),
            'category_three': ('django.db.models.fields.CharField', [], {'max_length': '300', 'null': 'True', 'blank': 'True'}),
            'category_two': ('django.db.models.fields.CharField', [], {'max_length': '300', 'null': 'True', 'blank': 'True'}),
            'data_type': ('django.db.models.fields.CharField', [], {'max_length': '7'}),
            'dataset_tag': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'datasource': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'display': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'file_name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'hover_label': ('django.db.models.fields.TextField', [], {}),
            'icon': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key_unit_type': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'max': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'min': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'short_label': ('django.db.models.fields.CharField', [], {'max_length': '300'}),
            'short_label_prefix': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50', 'db_index': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '9'}),
            'variable_definition': ('django.db.models.fields.TextField', [], {}),
            'years_available': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        'indicators.indicatordata': {
            'Meta': {'object_name': 'IndicatorData'},
            'data_type': ('django.db.models.fields.CharField', [], {'max_length': '7'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'indicator': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['indicators.Indicator']"}),
            'key_unit_type': ('django.db.models.fields.CharField', [], {'max_length': '50', 'db_index': 'True'}),
            'key_value': ('django.db.models.fields.CharField', [], {'max_length': '100', 'db_index': 'True'}),
            'numeric': ('django.db.models.fields.FloatField', [], {'null': 'True'}),
            'string': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True'}),
            'time_key': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '10', 'null': 'True', 'blank': 'True'}),
            'time_type': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '50', 'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['indicators']
