from django.db import migrations

def apply_details(apps, schema_editor):
    Company = apps.get_model('core', 'Company')
    company, _ = Company.objects.get_or_create(pk=1)
    data = dict(company.data or {})
    data.update({
        'official_name': 'ESTMAJO ENGINEERING SOLUTIONS LTD',
        'registration_number': '7810123',
        'primary_email': 'estmajo@hotmail.com',
        'use_supplied_logo': True,
        'short_intro': 'Engineering, installation and maintenance services, with logistics, procurement and construction support. Contact our Warri office to discuss your project requirements.',
        'description': 'ESTMAJO ENGINEERING SOLUTIONS LTD is based in Warri, Delta State, Nigeria. Our service areas include HVAC, electrical and solar installation and maintenance; logistics, supply chain management and procurement; operations and maintenance; instrumentation and control systems; and civil engineering and construction.\n\nContact our team with your project location, requirements and preferred schedule to discuss scope and request a quotation.',
        'footer_description': 'Engineering, installation, maintenance, procurement and construction services. Warri, Delta State, Nigeria.',
        'phones': [
            {'label': 'Main telephone', 'number': '+2348123834601', 'extension': '', 'primary': True, 'visible': True, 'order': 0},
            {'label': 'Additional telephone', 'number': '+2347065938360', 'extension': '', 'primary': False, 'visible': True, 'order': 1},
        ],
        'offices': [{
            'label': 'Warri Office',
            'address': 'D5 Edewor Estate, Opposite Shafa Filling Station, By Enerhen Motel',
            'city': 'Warri', 'region': 'Delta State', 'postcode': '',
            'country': 'Nigeria', 'map_url': '', 'directions_url': '',
            'visible': True, 'order': 0,
        }],
        'copyright_owner': 'ESTMAJO ENGINEERING SOLUTIONS LTD',
        'seo_title': 'ESTMAJO Engineering Solutions Ltd | Warri, Delta State',
        'seo_description': 'Contact ESTMAJO Engineering Solutions Ltd in Warri, Delta State, Nigeria for engineering, installation, maintenance, procurement and construction enquiries.',
    })
    company.data = data
    company.enquiry_recipient = 'estmajo@hotmail.com'
    company.save(update_fields=['data', 'enquiry_recipient'])

class Migration(migrations.Migration):
    dependencies = [('core', '0002_enquiry_notification_started_at')]
    operations = [migrations.RunPython(apply_details, migrations.RunPython.noop)]
