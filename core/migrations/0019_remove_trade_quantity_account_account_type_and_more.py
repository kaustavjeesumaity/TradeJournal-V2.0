# Generated by Django 5.2.1 on 2025-06-03 16:53

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0018_remove_achievement_user_remove_lesson_user_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='trade',
            name='quantity',
        ),
        migrations.AddField(
            model_name='account',
            name='account_type',
            field=models.CharField(choices=[('demo', 'Demo'), ('real', 'Real')], default='real', max_length=10),
        ),
        migrations.AddField(
            model_name='account',
            name='broker',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='account',
            name='equity',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True),
        ),
        migrations.AddField(
            model_name='account',
            name='leverage',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='account',
            name='margin',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True),
        ),
        migrations.AddField(
            model_name='trade',
            name='asset_class',
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.AddField(
            model_name='trade',
            name='direction',
            field=models.CharField(blank=True, choices=[('long', 'Long'), ('short', 'Short')], max_length=10),
        ),
        migrations.AddField(
            model_name='trade',
            name='fees',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True),
        ),
        migrations.AddField(
            model_name='trade',
            name='journal_notes',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='trade',
            name='lessons_learned',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='trade',
            name='order_type',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AddField(
            model_name='trade',
            name='outcome',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AddField(
            model_name='trade',
            name='planned_trade',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='executed_trades', to='core.tradeplan'),
        ),
        migrations.AddField(
            model_name='trade',
            name='psychological_state',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='trade',
            name='r_multiple',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=6, null=True),
        ),
        migrations.AddField(
            model_name='trade',
            name='risk_per_trade',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True),
        ),
        migrations.AddField(
            model_name='trade',
            name='size',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True),
        ),
        migrations.AddField(
            model_name='trade',
            name='slippage',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True),
        ),
        migrations.AddField(
            model_name='trade',
            name='stop_loss',
            field=models.DecimalField(blank=True, decimal_places=4, max_digits=12, null=True),
        ),
        migrations.AddField(
            model_name='trade',
            name='take_profit',
            field=models.DecimalField(blank=True, decimal_places=4, max_digits=12, null=True),
        ),
        migrations.AddField(
            model_name='tradeplan',
            name='actual_execution_price',
            field=models.DecimalField(blank=True, decimal_places=4, max_digits=12, null=True),
        ),
        migrations.AddField(
            model_name='tradeplan',
            name='actual_execution_time',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='tradeplan',
            name='planned_execution_price',
            field=models.DecimalField(blank=True, decimal_places=4, max_digits=12, null=True),
        ),
        migrations.AddField(
            model_name='tradeplan',
            name='planned_execution_time',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='tradeplan',
            name='post_trade_checklist',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='tradeplan',
            name='pre_trade_checklist',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='tradeplan',
            name='setup_type',
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.AddField(
            model_name='user',
            name='preferred_instruments',
            field=models.ManyToManyField(blank=True, related_name='preferred_by_users', to='core.instrument'),
        ),
        migrations.AddField(
            model_name='user',
            name='target_annual_pnl',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='target_monthly_pnl',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='target_win_rate',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True),
        ),
        migrations.CreateModel(
            name='Book',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('author', models.CharField(blank=True, max_length=255)),
                ('completed', models.BooleanField(default=False)),
                ('completion_date', models.DateField(blank=True, null=True)),
                ('notes', models.TextField(blank=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='books', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Course',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('completed', models.BooleanField(default=False)),
                ('completion_date', models.DateField(blank=True, null=True)),
                ('notes', models.TextField(blank=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='courses', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='KeyLesson',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', models.TextField()),
                ('date', models.DateField(blank=True, null=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='key_lessons', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Mistake',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('description', models.TextField()),
                ('date', models.DateField(blank=True, null=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='mistakes', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
