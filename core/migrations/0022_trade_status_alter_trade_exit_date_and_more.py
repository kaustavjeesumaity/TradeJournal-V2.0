# Generated by Django 5.2.1 on 2025-06-04 18:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0021_fix_trade_plan_checklists'),
    ]

    operations = [
        migrations.AddField(
            model_name='trade',
            name='status',
            field=models.CharField(choices=[('open', 'Open'), ('closed', 'Closed')], default='closed', max_length=10),
        ),
        migrations.AlterField(
            model_name='trade',
            name='exit_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='trade',
            name='exit_price',
            field=models.DecimalField(blank=True, decimal_places=4, max_digits=12, null=True),
        ),
    ]
