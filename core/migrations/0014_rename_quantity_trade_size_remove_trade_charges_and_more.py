# Generated by Django 5.2.1 on 2025-05-29 17:56

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0013_remove_tradeplanevent_attachment_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='trade',
            old_name='quantity',
            new_name='size',
        ),
        migrations.RemoveField(
            model_name='trade',
            name='charges',
        ),
        migrations.RemoveField(
            model_name='tradeattachment',
            name='trade',
        ),
        migrations.AddField(
            model_name='account',
            name='account_type',
            field=models.CharField(choices=[('real', 'Real'), ('demo', 'Demo')], default='real', max_length=16),
        ),
        migrations.AddField(
            model_name='account',
            name='api_key',
            field=models.CharField(blank=True, max_length=128, null=True),
        ),
        migrations.AddField(
            model_name='account',
            name='broker',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='account',
            name='equity',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12),
        ),
        migrations.AddField(
            model_name='account',
            name='leverage',
            field=models.CharField(blank=True, max_length=16, null=True),
        ),
        migrations.AddField(
            model_name='instrument',
            name='asset_class',
            field=models.CharField(blank=True, max_length=32, null=True),
        ),
        migrations.AddField(
            model_name='trade',
            name='attachments',
            field=models.ManyToManyField(blank=True, to='core.tradeattachment'),
        ),
        migrations.AddField(
            model_name='trade',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='trade',
            name='direction',
            field=models.CharField(choices=[('long', 'Long'), ('short', 'Short')], default='long', max_length=8),
        ),
        migrations.AddField(
            model_name='trade',
            name='execution_quality',
            field=models.CharField(blank=True, max_length=32, null=True),
        ),
        migrations.AddField(
            model_name='trade',
            name='fees',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=8),
        ),
        migrations.AddField(
            model_name='trade',
            name='lessons',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='trade',
            name='mistakes',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='trade',
            name='order_type',
            field=models.CharField(blank=True, max_length=16, null=True),
        ),
        migrations.AddField(
            model_name='trade',
            name='plan',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='core.tradeplan'),
        ),
        migrations.AddField(
            model_name='trade',
            name='plan_adherence',
            field=models.CharField(blank=True, max_length=32, null=True),
        ),
        migrations.AddField(
            model_name='trade',
            name='psychological_state',
            field=models.CharField(blank=True, max_length=64, null=True),
        ),
        migrations.AddField(
            model_name='trade',
            name='r_multiple',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=6, null=True),
        ),
        migrations.AddField(
            model_name='trade',
            name='risk_per_trade',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True),
        ),
        migrations.AddField(
            model_name='trade',
            name='slippage',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=8),
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
            model_name='trade',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AlterField(
            model_name='trade',
            name='instrument',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.instrument'),
        ),
        migrations.CreateModel(
            name='Achievement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField(blank=True)),
                ('achieved_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Lesson',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', models.TextField()),
                ('source', models.CharField(blank=True, max_length=255)),
                ('learned_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Milestone',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('description', models.CharField(max_length=255)),
                ('achieved_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Review',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('period', models.CharField(max_length=32)),
                ('summary', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('avatar', models.ImageField(blank=True, null=True, upload_to='avatars/')),
                ('timezone', models.CharField(blank=True, max_length=64, null=True)),
                ('country', models.CharField(blank=True, max_length=64, null=True)),
                ('trading_style', models.CharField(blank=True, max_length=32, null=True)),
                ('experience_level', models.CharField(blank=True, max_length=32, null=True)),
                ('risk_profile', models.CharField(blank=True, max_length=32, null=True)),
                ('goals', models.TextField(blank=True)),
                ('motivational_quote', models.CharField(blank=True, max_length=255)),
                ('review_frequency', models.CharField(blank=True, max_length=32, null=True)),
                ('default_account', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='core.account')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='profile', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
