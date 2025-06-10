from django.db import migrations, models

def set_default_checklists(apps, schema_editor):
    TradePlan = apps.get_model('core', 'TradePlan')
    # Set empty string as default for existing records
    TradePlan.objects.filter(pre_trade_checklist__isnull=True).update(pre_trade_checklist='')
    TradePlan.objects.filter(post_trade_checklist__isnull=True).update(post_trade_checklist='')

def reverse_default_checklists(apps, schema_editor):
    # No need to do anything in reverse as fields will be recreated with defaults
    pass

class Migration(migrations.Migration):
    dependencies = [
        ('core', '0020_remove_tradeplan_post_trade_checklist_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='tradeplan',
            name='pre_trade_checklist',
            field=models.TextField(blank=True, default='', help_text='Pre-trade checklist items'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='tradeplan',
            name='post_trade_checklist',
            field=models.TextField(blank=True, default='', help_text='Post-trade checklist items'),
            preserve_default=True,
        ),
        migrations.RunPython(set_default_checklists, reverse_code=reverse_default_checklists),
        migrations.RemoveField(
            model_name='tradeplan',
            name='pre_trade_checklist',
        ),
        migrations.RemoveField(
            model_name='tradeplan',
            name='post_trade_checklist',
        ),
    ]
