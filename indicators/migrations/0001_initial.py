# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
import taggit_autosuggest.managers


class Migration(migrations.Migration):

    dependencies = [
        ('taggit', '0002_auto_20150616_2121'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='AnonymizedEnrollment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('school_year', models.CharField(max_length=9, db_index=True)),
                ('SASID', models.IntegerField(db_index=True)),
                ('distCode', models.CharField(max_length=2, db_index=True)),
                ('grade', models.CharField(max_length=50, db_index=True)),
                ('enroll_date', models.DateField(null=True)),
                ('exit_date', models.DateField(null=True)),
                ('exit_type', models.CharField(max_length=200)),
            ],
        ),
        migrations.CreateModel(
            name='DataSource',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('short', models.CharField(max_length=11)),
                ('short_name', models.CharField(max_length=12)),
                ('name', models.CharField(max_length=100)),
                ('url', models.URLField()),
                ('icon_file', models.ImageField(null=True, upload_to=b'datasource_icons', blank=True)),
                ('description', models.TextField(blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='DefaultIndicatorList',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=200)),
                ('slug', models.SlugField(unique=True, max_length=200, blank=True)),
                ('public', models.BooleanField(default=False)),
                ('visible_in_default', models.BooleanField(default=False)),
                ('created', models.DateField(auto_now_add=True)),
                ('visible_in_weave', models.BooleanField(default=True)),
                ('description', models.TextField(blank=True)),
            ],
            options={
                'verbose_name': 'Recommended Indicator List',
            },
        ),
        migrations.CreateModel(
            name='DefaultListSubscription',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('visible_in_weave', models.BooleanField(default=True)),
                ('ilist', models.ForeignKey(to='indicators.DefaultIndicatorList')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Indicator',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=100)),
                ('file_name', models.CharField(max_length=100, blank=True)),
                ('display_name', models.CharField(max_length=100)),
                ('short_definition', models.TextField()),
                ('long_definition', models.TextField(help_text=b'This field is Markdown enabled.')),
                ('purpose', models.TextField(help_text=b'This field is Markdown enabled.', blank=True)),
                ('universe', models.CharField(max_length=300, blank=True)),
                ('limitations', models.TextField(help_text=b'This field is Markdown enabled.', blank=True)),
                ('routine_use', models.TextField(blank=True)),
                ('last_audited', models.DateTimeField(help_text=b'Blank or null means it has never been audited', null=True, blank=True)),
                ('min', models.IntegerField(null=True, blank=True)),
                ('max', models.IntegerField(null=True, blank=True)),
                ('unit', models.CharField(default=b'other', max_length=10, choices=[(b'percent', b'percent'), (b'count', b'count'), (b'rate', b'rate'), (b'other', b'other')])),
                ('data_type', models.CharField(max_length=7, choices=[(b'numeric', b'numeric'), (b'string', b'string')])),
                ('raw_tags', models.TextField()),
                ('raw_datasources', models.TextField()),
                ('notes', models.TextField(blank=True)),
                ('data_levels_available', models.CharField(max_length=200, blank=True)),
                ('query_level', models.CharField(max_length=100, blank=True)),
                ('suppression_numerator', models.IntegerField(help_text=b'Cells < value are suppressed. Cells >= value appear in output.', null=True, blank=True)),
                ('suppression_denominator', models.IntegerField(help_text=b'Cells < value are suppressed. Cells >= value appear in output.', null=True, blank=True)),
                ('years_available_display', models.CharField(max_length=200)),
                ('years_available', models.CommaSeparatedIntegerField(max_length=200)),
                ('published', models.BooleanField(default=True)),
                ('retired', models.BooleanField(default=False)),
                ('visible_in_all_lists', models.BooleanField(default=False)),
                ('slug', models.SlugField(unique=True)),
                ('load_pending', models.BooleanField(default=False, help_text=b'Weave attribute column regen pending')),
                ('last_load_completed', models.DateTimeField(help_text=b'Date/Time data last loaded into database', null=True, blank=True)),
                ('datasources', models.ManyToManyField(to='indicators.DataSource', verbose_name=b'Data Sources')),
            ],
        ),
        migrations.CreateModel(
            name='IndicatorData',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('time_type', models.CharField(blank=True, max_length=50, null=True, db_index=True, choices=[(b'School Year', b'School Year')])),
                ('time_key', models.CharField(db_index=True, max_length=10, null=True, blank=True)),
                ('key_unit_type', models.CharField(db_index=True, max_length=50, choices=[(b'School', b'School'), (b'District', b'District')])),
                ('key_value', models.CharField(max_length=100, db_index=True)),
                ('data_type', models.CharField(max_length=7, choices=[(b'numeric', b'numeric'), (b'string', b'string')])),
                ('numeric', models.DecimalField(null=True, max_digits=20, decimal_places=2, blank=True)),
                ('string', models.CharField(max_length=100, null=True)),
                ('indicator', models.ForeignKey(to='indicators.Indicator')),
            ],
        ),
        migrations.CreateModel(
            name='IndicatorList',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=200)),
                ('slug', models.SlugField(unique=True, max_length=200)),
                ('public', models.BooleanField(default=False)),
                ('visible_in_default', models.BooleanField(default=False)),
                ('created', models.DateField(auto_now_add=True)),
                ('visible_in_weave', models.BooleanField(default=True)),
                ('indicators', models.ManyToManyField(to='indicators.Indicator')),
                ('owner', models.ForeignKey(blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='IndicatorPregenPart',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('file_name', models.CharField(max_length=100)),
                ('column_name', models.CharField(max_length=100)),
                ('key_type', models.CharField(max_length=100)),
                ('time_type', models.CharField(max_length=100)),
                ('time_value', models.CharField(max_length=100)),
                ('key_column', models.CharField(max_length=100, blank=True)),
                ('indicator', models.ForeignKey(related_name='pregenparts', to='indicators.Indicator')),
            ],
        ),
        migrations.CreateModel(
            name='Permission',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('indicator', models.ForeignKey(to='indicators.Indicator')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='SubDataSourceDisclaimer',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=100)),
                ('title', models.CharField(max_length=100)),
                ('content', models.TextField(help_text=b'This field is Markdown enabled.')),
            ],
        ),
        migrations.CreateModel(
            name='TypeIndicatorLookup',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=100)),
                ('key_unit_type', models.CharField(max_length=100)),
                ('indicator_id', models.CharField(max_length=10)),
            ],
        ),
        migrations.CreateModel(
            name='SubDataSource',
            fields=[
                ('short', models.CharField(max_length=11)),
                ('short_name', models.CharField(max_length=12)),
                ('name', models.CharField(max_length=100)),
                ('url', models.URLField(blank=True)),
                ('icon_file', models.ImageField(null=True, upload_to=b'datasource_icons', blank=True)),
                ('description', models.TextField(blank=True)),
                ('disclaimer', models.OneToOneField(primary_key=True, serialize=False, to='indicators.SubDataSourceDisclaimer')),
            ],
        ),
        migrations.AddField(
            model_name='indicator',
            name='permissions',
            field=models.ForeignKey(related_name='indicator_permission', blank=True, to='indicators.Permission', null=True),
        ),
        migrations.AddField(
            model_name='indicator',
            name='tags',
            field=taggit_autosuggest.managers.TaggableManager(to='taggit.Tag', through='taggit.TaggedItem', blank=True, help_text='A comma-separated list of tags.', verbose_name='Tags'),
        ),
        migrations.AddField(
            model_name='defaultindicatorlist',
            name='indicators',
            field=models.ManyToManyField(to='indicators.Indicator'),
        ),
        migrations.AddField(
            model_name='defaultindicatorlist',
            name='users',
            field=models.ManyToManyField(to=settings.AUTH_USER_MODEL, through='indicators.DefaultListSubscription'),
        ),
        migrations.AlterUniqueTogether(
            name='indicatorlist',
            unique_together=set([('name', 'owner')]),
        ),
        migrations.AddField(
            model_name='datasource',
            name='sub_datasources',
            field=models.ManyToManyField(to='indicators.SubDataSource', null=True, blank=True),
        ),
    ]
