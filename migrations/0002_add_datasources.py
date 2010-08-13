# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'DataSource'
        db.create_table('indicators_datasource', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('short', self.gf('django.db.models.fields.CharField')(max_length=4)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('url', self.gf('django.db.models.fields.URLField')(max_length=200)),
            ('icon_path', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('description', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal('indicators', ['DataSource'])

        # Deleting field 'Indicator.datasource'
        db.delete_column('indicators_indicator', 'datasource')

        # Adding M2M table for field datasources on 'Indicator'
        db.create_table('indicators_indicator_datasources', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('indicator', models.ForeignKey(orm['indicators.indicator'], null=False)),
            ('datasource', models.ForeignKey(orm['indicators.datasource'], null=False))
        ))
        db.create_unique('indicators_indicator_datasources', ['indicator_id', 'datasource_id'])


    def backwards(self, orm):
        
        # Deleting model 'DataSource'
        db.delete_table('indicators_datasource')

        # Adding field 'Indicator.datasource'
        db.add_column('indicators_indicator', 'datasource', self.gf('django.db.models.fields.CharField')(default='', max_length=100), keep_default=False)

        # Removing M2M table for field datasources on 'Indicator'
        db.delete_table('indicators_indicator_datasources')


    models = {
        'indicators.datasource': {
            'Meta': {'object_name': 'DataSource'},
            'description': ('django.db.models.fields.TextField', [], {}),
            'icon_path': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'short': ('django.db.models.fields.CharField', [], {'max_length': '4'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200'})
        },
        'indicators.indicator': {
            'Meta': {'unique_together': "(('name', 'key_unit_type'),)", 'object_name': 'Indicator'},
            'case_restrictions': ('django.db.models.fields.TextField', [], {}),
            'category_four': ('django.db.models.fields.CharField', [], {'max_length': '300', 'null': 'True', 'blank': 'True'}),
            'category_one': ('django.db.models.fields.CharField', [], {'max_length': '300', 'null': 'True', 'blank': 'True'}),
            'category_three': ('django.db.models.fields.CharField', [], {'max_length': '300', 'null': 'True', 'blank': 'True'}),
            'category_two': ('django.db.models.fields.CharField', [], {'max_length': '300', 'null': 'True', 'blank': 'True'}),
            'data_type': ('django.db.models.fields.CharField', [], {'max_length': '7'}),
            'dataset_tag': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'datasources': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['indicators.DataSource']", 'symmetrical': 'False'}),
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
