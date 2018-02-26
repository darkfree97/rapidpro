# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-02-28 08:37
from __future__ import absolute_import, division, print_function, unicode_literals

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('airtime', '0006_reset_4'),
    ]

    operations = [
        migrations.AlterField(
            model_name='airtimetransfer',
            name='created_on',
            field=models.DateTimeField(blank=True, default=django.utils.timezone.now, editable=False, help_text='When this item was originally created'),
        ),
        migrations.AlterField(
            model_name='airtimetransfer',
            name='modified_on',
            field=models.DateTimeField(blank=True, default=django.utils.timezone.now, editable=False, help_text='When this item was last modified'),
        ),
    ]
