# Generated by Django 5.1.1 on 2024-12-02 11:38

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('ShiftsApp', '0001_initial'),
        ('UsersApp', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ShiftLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('change_type', models.CharField(max_length=50)),
                ('change_date', models.DateTimeField(auto_now_add=True)),
                ('description', models.TextField()),
                ('calendar_shift', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='ShiftsApp.calendarshift')),
                ('changed_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='UsersApp.user')),
            ],
        ),
    ]