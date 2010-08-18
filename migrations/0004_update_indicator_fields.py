# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Deleting field 'Indicator.variable_definition'
        db.delete_column('indicators_indicator', 'variable_definition')

        # Deleting field 'Indicator.category_three'
        db.delete_column('indicators_indicator', 'category_three')

        # Deleting field 'Indicator.category_one'
        db.delete_column('indicators_indicator', 'category_one')

        # Deleting field 'Indicator.category_two'
        db.delete_column('indicators_indicator', 'category_two')

        # Deleting field 'Indicator.key_unit_type'
        db.delete_column('indicators_indicator', 'key_unit_type')

        # Deleting field 'Indicator.short_label_prefix'
        db.delete_column('indicators_indicator', 'short_label_prefix')

        # Deleting field 'Indicator.category_four'
        db.delete_column('indicators_indicator', 'category_four')

        # Deleting field 'Indicator.icon'
        db.delete_column('indicators_indicator', 'icon')

        # Deleting field 'Indicator.case_restrictions'
        db.delete_column('indicators_indicator', 'case_restrictions')

        # Deleting field 'Indicator.dataset_tag'
        db.delete_column('indicators_indicator', 'dataset_tag')

        # Deleting field 'Indicator.hover_label'
        db.delete_column('indicators_indicator', 'hover_label')

        # Deleting field 'Indicator.display'
        db.delete_column('indicators_indicator', 'display')

        # Adding field 'Indicator.display_name'
        db.add_column('indicators_indicator', 'display_name', self.gf('django.db.models.fields.CharField')(default='', max_length=100), keep_default=False)

        # Adding field 'Indicator.short_definition'
        db.add_column('indicators_indicator', 'short_definition', self.gf('django.db.models.fields.TextField')(default=''), keep_default=False)

        # Adding field 'Indicator.long_definition'
        db.add_column('indicators_indicator', 'long_definition', self.gf('django.db.models.fields.TextField')(default=''), keep_default=False)

        # Adding field 'Indicator.purpose'
        db.add_column('indicators_indicator', 'purpose', self.gf('django.db.models.fields.TextField')(default=''), keep_default=False)

        # Adding field 'Indicator.raw_tags'
        db.add_column('indicators_indicator', 'raw_tags', self.gf('django.db.models.fields.TextField')(default=''), keep_default=False)

        # Adding field 'Indicator.unit'
        db.add_column('indicators_indicator', 'unit', self.gf('django.db.models.fields.CharField')(default='other', max_length=10), keep_default=False)

        # Adding unique constraint on 'Indicator', fields ['name']
        db.create_unique('indicators_indicator', ['name'])

        # Changing field 'Indicator.file_name'
        db.alter_column('indicators_indicator', 'file_name', self.gf('django.db.models.fields.CharField')(max_length=100, blank=True))

        # Removing unique constraint on 'Indicator', fields ['key_unit_type', 'name']
        #db.delete_unique('indicators_indicator', ['name', 'key_unit_type'])


    def backwards(self, orm):
        
        # Adding field 'Indicator.variable_definition'
        db.add_column('indicators_indicator', 'variable_definition', self.gf('django.db.models.fields.TextField')(default=''), keep_default=False)

        # Adding field 'Indicator.category_three'
        db.add_column('indicators_indicator', 'category_three', self.gf('django.db.models.fields.CharField')(max_length=300, null=True, blank=True), keep_default=False)

        # Adding field 'Indicator.category_one'
        db.add_column('indicators_indicator', 'category_one', self.gf('django.db.models.fields.CharField')(max_length=300, null=True, blank=True), keep_default=False)

        # Adding field 'Indicator.category_two'
        db.add_column('indicators_indicator', 'category_two', self.gf('django.db.models.fields.CharField')(max_length=300, null=True, blank=True), keep_default=False)

        # Adding field 'Indicator.key_unit_type'
        db.add_column('indicators_indicator', 'key_unit_type', self.gf('django.db.models.fields.CharField')(default='', max_length=30), keep_default=False)

        # Adding field 'Indicator.short_label_prefix'
        db.add_column('indicators_indicator', 'short_label_prefix', self.gf('django.db.models.fields.CharField')(default='', max_length=100), keep_default=False)

        # Adding field 'Indicator.category_four'
        db.add_column('indicators_indicator', 'category_four', self.gf('django.db.models.fields.CharField')(max_length=300, null=True, blank=True), keep_default=False)

        # Adding field 'Indicator.icon'
        db.add_column('indicators_indicator', 'icon', self.gf('django.db.models.fields.CharField')(max_length=100, null=True), keep_default=False)

        # Adding field 'Indicator.case_restrictions'
        db.add_column('indicators_indicator', 'case_restrictions', self.gf('django.db.models.fields.TextField')(default=''), keep_default=False)

        # Adding field 'Indicator.dataset_tag'
        db.add_column('indicators_indicator', 'dataset_tag', self.gf('django.db.models.fields.CharField')(default='', max_length=100), keep_default=False)

        # Adding field 'Indicator.hover_label'
        db.add_column('indicators_indicator', 'hover_label', self.gf('django.db.models.fields.TextField')(default=''), keep_default=False)

        # Adding field 'Indicator.display'
        db.add_column('indicators_indicator', 'display', self.gf('django.db.models.fields.BooleanField')(default=True, blank=True), keep_default=False)

        # Deleting field 'Indicator.display_name'
        db.delete_column('indicators_indicator', 'display_name')

        # Deleting field 'Indicator.short_definition'
        db.delete_column('indicators_indicator', 'short_definition')

        # Deleting field 'Indicator.long_definition'
        db.delete_column('indicators_indicator', 'long_definition')

        # Deleting field 'Indicator.purpose'
        db.delete_column('indicators_indicator', 'purpose')

        # Deleting field 'Indicator.raw_tags'
        db.delete_column('indicators_indicator', 'raw_tags')

        # Deleting field 'Indicator.unit'
        db.delete_column('indicators_indicator', 'unit')

        # Removing unique constraint on 'Indicator', fields ['name']
        db.delete_unique('indicators_indicator', ['name'])

        # Changing field 'Indicator.file_name'
        db.alter_column('indicators_indicator', 'file_name', self.gf('django.db.models.fields.CharField')(max_length=100))

        # Adding unique constraint on 'Indicator', fields ['key_unit_type', 'name']
        db.create_unique('indicators_indicator', ['key_unit_type', 'name'])


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
            'short_label': ('django.db.models.fields.CharField', [], {'max_length': '300'}),
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
