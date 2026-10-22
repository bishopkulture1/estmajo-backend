from django.core.management.base import BaseCommand
from django.utils.text import slugify
from core.models import Content, Company
class Command(BaseCommand):
    help='Add the seven supplied service categories without overwriting any content.'
    def handle(self,*args,**kwargs):
        for index,title in enumerate(['HVAC System Installation and Maintenance','Electrical Installation and Maintenance','Solar Energy System Installation and Maintenance','Logistics, Supply Chain Management and Procurement','Operations and Maintenance','Instrumentation and Control System Installation and Maintenance','Civil Engineering and Construction']):
            Content.objects.get_or_create(slug=slugify(title),defaults={'kind':'service','title':title,'published':True,'order':index})
        self.stdout.write('Service categories initialised. Company information remains managed through the owner dashboard.')
