import json
from django.core.management.base import BaseCommand
from core.models import Media
from core.media import api, in_use
class Command(BaseCommand):
    help='Read-only audit: compare ImageKit /esmajo files with local media records. Never deletes files.'
    def handle(self,*args,**options):
        remote=[];skip=0
        while True:
            batch=api('GET','files',params={'path':'/esmajo','limit':1000,'skip':skip,'fileType':'all'})
            remote.extend(batch)
            if len(batch)<1000: break
            skip+=1000
        local=set(Media.objects.values_list('file_id',flat=True))
        self.stdout.write(json.dumps({'untracked_remote_assets':[{'file_id':r['fileId'],'name':r.get('name')} for r in remote if r.get('fileId') and r['fileId'] not in local],'unused_local_assets':[{'id':m.pk,'file_id':m.file_id,'name':m.name} for m in Media.objects.all() if not in_use(m)]},indent=2))
