# Generated by Django 5.1.1 on 2024-12-16 13:41

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('LogsApp', '0001_initial'),
        ('ShiftsApp', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='shiftlog',
            name='calendar_shift',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='ShiftsApp.calendarshift'),
        ),
    ]
