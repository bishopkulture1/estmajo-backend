import hashlib, time, logging, io
from urllib.parse import urlencode
from pathlib import Path
import requests
from PIL import Image
from django.conf import settings
from rest_framework.exceptions import ValidationError
from .models import Media, Company
from functools import lru_cache
@lru_cache(maxsize=2)
def _signing_client(key):
    from imagekitio import ImageKit
    return ImageKit(private_key=key)
log=logging.getLogger(__name__)
def delivery_url(asset, width=None):
    if not settings.IMAGEKIT_PRIVATE_KEY or not settings.IMAGEKIT_URL_ENDPOINT: return ''
    from imagekitio import ImageKit
    client=_signing_client(settings.IMAGEKIT_PRIVATE_KEY)
    src=asset.url.removeprefix(settings.IMAGEKIT_URL_ENDPOINT)
    options={'url_endpoint':settings.IMAGEKIT_URL_ENDPOINT,'src':src,'signed':True,'expires_in':3600}
    if width and asset.kind=='image': options['transformation']=[{'width':width,'quality':80,'format':'auto'}]
    return client.helper.build_url(**options)
def references(asset):
    fields=[k for k,v in Company.current().data.items() if k in ['logo','favicon','ceo_photo','sharing_image'] and v==asset.pk]
    return {'content':list(asset.content.values_list('id',flat=True)), 'documents':list(asset.document_set.values_list('id',flat=True)), 'settings':fields}
def in_use(asset):
    r=references(asset)
    return any(r.values()) or asset.gallery

def api(method,path,**kw):
    if not settings.IMAGEKIT_PRIVATE_KEY or not settings.IMAGEKIT_URL_ENDPOINT:
        raise ValidationError('Configure ImageKit credentials and URL endpoint on the server first.')
    try:
        response=requests.request(method,'https://api.imagekit.io/v1/'+path,auth=(settings.IMAGEKIT_PRIVATE_KEY,''),timeout=45,**kw)
        response.raise_for_status()
        return response.json() if response.content else {}
    except requests.RequestException:
        raise ValidationError('ImageKit could not complete the request. Check credentials/connectivity and retry.')

def upload(file):
    ext=Path(file.name).suffix.lower()
    kinds={'.jpg':('image','image/jpeg'),'.jpeg':('image','image/jpeg'),'.png':('image','image/png'),'.webp':('image','image/webp'),'.mp4':('video','video/mp4'),'.webm':('video','video/webm'),'.pdf':('document','application/pdf')}
    if ext not in kinds: raise ValidationError('Supported: JPEG, PNG, WebP, MP4, WebM and PDF. SVG and executable files are not accepted.')
    kind,mime=kinds[ext]
    limit={'image':settings.MAX_IMAGE_BYTES,'video':settings.MAX_VIDEO_BYTES,'document':settings.MAX_DOCUMENT_BYTES}[kind]
    if file.size>limit: raise ValidationError(f'File exceeds the configured {limit//1048576} MB limit.')
    header=file.read(32); file.seek(0)
    if kind=='image':
        try:
            im=Image.open(file); im.verify()
            if im.format not in ['JPEG','PNG','WEBP']: raise ValueError()
        except Exception: raise ValidationError('Invalid image file.')
        finally: file.seek(0)
    if kind=='document' and not header.startswith(b'%PDF-'): raise ValidationError('Invalid PDF file.')
    if kind=='video' and not ((ext=='.mp4' and header[4:8]==b'ftyp') or (ext=='.webm' and header.startswith(b'\x1aE\xdf\xa3'))): raise ValidationError('Invalid video container.')
    if not settings.IMAGEKIT_PRIVATE_KEY or not settings.IMAGEKIT_URL_ENDPOINT: raise ValidationError('ImageKit has not been configured.')
    file_id=None
    try:
        r=requests.post('https://upload.imagekit.io/api/v1/files/upload',auth=(settings.IMAGEKIT_PRIVATE_KEY,''),files={'file':(file.name,file,mime)},data={'fileName':file.name,'folder':'/esmajo','useUniqueFileName':'true','isPrivateFile':'true'},timeout=180)
        r.raise_for_status(); uploaded=r.json(); file_id=uploaded['fileId']
        metadata=api('GET',f'files/{file_id}/details')
        url=settings.IMAGEKIT_URL_ENDPOINT+'/'+metadata['filePath'].lstrip('/')
        if not url.startswith(settings.IMAGEKIT_URL_ENDPOINT+'/'): raise ValueError('Unexpected delivery endpoint')
        if not metadata.get('isPrivateFile') or metadata.get('mime') != mime: raise ValueError('Unexpected MIME type or privacy flag')
        if int(metadata['size'])>limit or metadata.get('fileType') not in {'image':['image'],'video':['non-image','video'],'document':['non-image']}[kind]: raise ValueError('Unexpected asset metadata')
        return Media.objects.create(file_id=file_id,url=url,name=metadata['name'],kind=kind,mime=mime,size=metadata['size'],width=metadata.get('width') or 0,height=metadata.get('height') or 0)
    except Exception:
        if file_id:
            try: api('DELETE',f'files/{file_id}')
            except Exception: log.error('Orphaned ImageKit upload requiring cleanup: %s',file_id)
        raise ValidationError('Upload or metadata verification failed. No asset was attached. Check ImageKit and server logs before retrying.')
