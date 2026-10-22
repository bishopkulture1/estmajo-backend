from django.db import migrations

def remove_discarded_note(apps, schema_editor):
    Company=apps.get_model('core','Company')
    for company in Company.objects.all():
        data=dict(company.data or {})
        if 'additional' in data:
            data['additional']=[row for row in data['additional'] if row.get('label')!='Telephone awaiting confirmation']
            company.data=data
            company.save(update_fields=['data'])

class Migration(migrations.Migration):
    dependencies=[('core','0003_confirmed_company_details')]
    operations=[migrations.RunPython(remove_discarded_note,migrations.RunPython.noop)]
