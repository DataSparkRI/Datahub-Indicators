# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Deleting field 'Indicator.short_label'
        db.delete_column('indicators_indicator', 'short_label')


    def backwards(self, orm):
        
        # Adding field 'Indicator.short_label'
        db.add_column('indicators_indicator', 'short_label', self.gf('django.db.models.fields.CharField')(default='', max_length=300), keep_default=False)


    models = {
        'indicators.datasource': {
            'Meta': {'object_name': 'DataSource'},
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'icon_path': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'short': ('django.db.models.fields.CharField', [], {'max_length': '4'}),
            'short_name': ('django.db.models.fields.CharField', [], {'max_length': '12'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200'})
        },
        'indicators.indicator': {
            'Meta': {'object_name': 'Indicator'},
            'data_type': ('django.db.models.fields.CharField', [], {'max_length': '7'}),
            'datasources': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['indicators.DataSource']", 'symmetrical': 'False'}),
            'display_name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'file_name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'long_definition': ('django.db.models.fields.TextField', [], {}),
            'max': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'min': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'}),
            'purpose': ('django.db.models.fields.TextField', [], {}),
            'raw_tags': ('django.db.models.fields.TextField', [], {}),
            'short_definition': ('django.db.models.fields.TextField', [], {}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50', 'db_index': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '9'}),
            'unit': ('django.db.models.fields.CharField', [], {'default': "'other'", 'max_length': '10'}),
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
