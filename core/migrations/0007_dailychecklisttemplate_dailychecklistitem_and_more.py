# Generated by Django 5.2.1 on 2025-05-27 14:52

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_checklistitem_negative_positive_session_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='DailyChecklistTemplate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(default='Default', max_length=100)),
                ('effective_date', models.DateField(help_text='Checklist applies from this date (inclusive)')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['-effective_date'],
            },
        ),
        migrations.CreateModel(
            name='DailyChecklistItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.CharField(max_length=255)),
                ('order', models.PositiveIntegerField(default=0)),
                ('template', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='core.dailychecklisttemplate')),
            ],
            options={
                'ordering': ['order', 'id'],
            },
        ),
        migrations.CreateModel(
            name='UserDailyChecklistProgress',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('checked', models.BooleanField(default=False)),
                ('checked_at', models.DateTimeField(blank=True, null=True)),
                ('item', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.dailychecklistitem')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'unique_together': {('user', 'date', 'item')},
            },
        ),
    ]
