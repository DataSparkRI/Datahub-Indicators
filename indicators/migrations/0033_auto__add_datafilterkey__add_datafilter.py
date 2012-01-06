# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'DataFilterKey'
        db.create_table('indicators_datafilterkey', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('data_filter', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['indicators.DataFilter'])),
            ('key_value', self.gf('django.db.models.fields.CharField')(max_length=100)),
        ))
        db.send_create_signal('indicators', ['DataFilterKey'])

        # Adding model 'DataFilter'
        db.create_table('indicators_datafilter', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('file', self.gf('django.db.models.fields.files.FileField')(max_length=100, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=100)),
            ('display', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('key_unit_type', self.gf('django.db.models.fields.CharField')(max_length=256)),
        ))
        db.send_create_signal('indicators', ['DataFilter'])


    def backwards(self, orm):
        
        # Deleting model 'DataFilterKey'
        db.delete_table('indicators_datafilterkey')

        # Deleting model 'DataFilter'
        db.delete_table('indicators_datafilter')


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'indicators.anonymizedenrollment': {
            'Meta': {'object_name': 'AnonymizedEnrollment'},
            'SASID': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'}),
            'distCode': ('django.db.models.fields.CharField', [], {'max_length': '2', 'db_index': 'True'}),
            'enroll_date': ('django.db.models.fields.DateField', [], {'null': 'True'}),
            'exit_date': ('django.db.models.fields.DateField', [], {'null': 'True'}),
            'exit_type': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'grade': ('django.db.models.fields.CharField', [], {'max_length': '50', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'school_year': ('django.db.models.fields.CharField', [], {'max_length': '9', 'db_index': 'True'})
        },
        'indicators.datafilter': {
            'Meta': {'object_name': 'DataFilter'},
            'display': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'file': ('django.db.models.fields.files.FileField', [], {'max_length': '100', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key_unit_type': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'})
        },
        'indicators.datafilterkey': {
            'Meta': {'object_name': 'DataFilterKey'},
            'data_filter': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['indicators.DataFilter']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key_value': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'indicators.datasource': {
            'Meta': {'object_name': 'DataSource'},
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'icon_path': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'short': ('django.db.models.fields.CharField', [], {'max_length': '11'}),
            'short_name': ('django.db.models.fields.CharField', [], {'max_length': '12'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200'})
        },
        'indicators.indicator': {
            'Meta': {'object_name': 'Indicator'},
            'data_levels_available': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'data_type': ('django.db.models.fields.CharField', [], {'max_length': '7'}),
            'datasources': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['indicators.DataSource']", 'symmetrical': 'False'}),
            'display_name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'file_name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_audited': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'last_load_completed': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'limitations': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'load_pending': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'long_definition': ('django.db.models.fields.TextField', [], {}),
            'max': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'min': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'}),
            'notes': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'published': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'purpose': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'query_level': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'raw_datasources': ('django.db.models.fields.TextField', [], {}),
            'raw_tags': ('django.db.models.fields.TextField', [], {}),
            'routine_use': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'short_definition': ('django.db.models.fields.TextField', [], {}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50', 'db_index': 'True'}),
            'suppression_denominator': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'suppression_numerator': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'unit': ('django.db.models.fields.CharField', [], {'default': "'other'", 'max_length': '10'}),
            'universe': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
            'visible_in_all_lists': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'years_available': ('django.db.models.fields.CommaSeparatedIntegerField', [], {'max_length': '200'}),
            'years_available_display': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        'indicators.indicatordata': {
            'Meta': {'object_name': 'IndicatorData'},
            'data_type': ('django.db.models.fields.CharField', [], {'max_length': '7'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'indicator': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['indicators.Indicator']"}),
            'key_unit_type': ('django.db.models.fields.CharField', [], {'max_length': '50', 'db_index': 'True'}),
            'key_value': ('django.db.models.fields.CharField', [], {'max_length': '100', 'db_index': 'True'}),
            'numeric': ('indicators.fields.RoundingDecimalField', [], {'null': 'True', 'max_digits': '20', 'decimal_places': '2', 'blank': 'True'}),
            'string': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True'}),
            'time_key': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '10', 'null': 'True', 'blank': 'True'}),
            'time_type': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '50', 'null': 'True', 'blank': 'True'})
        },
        'indicators.indicatorlist': {
            'Meta': {'unique_together': "(('name', 'owner'),)", 'object_name': 'IndicatorList'},
            'created': ('django.db.models.fields.DateField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'indicators': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['indicators.Indicator']", 'symmetrical': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True', 'blank': 'True'}),
            'public': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '200', 'db_index': 'True'}),
            'visible_in_default': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'visible_in_weave': ('django.db.models.fields.BooleanField', [], {'default': 'True'})
        },
        'indicators.indicatorpregenpart': {
            'Meta': {'object_name': 'IndicatorPregenPart'},
            'column_name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'file_name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'indicator': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['indicators.Indicator']"}),
            'key_column': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'key_type': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'time_type': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'time_value': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        }
    }

    complete_apps = ['indicators']
