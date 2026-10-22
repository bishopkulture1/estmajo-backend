import hashlib, json, datetime
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.middleware.csrf import get_token
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_safe
from django.db import transaction, IntegrityError, DatabaseError
from django.db.models import F
from django.core.mail import EmailMessage
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError, Throttled
from rest_framework.permissions import AllowAny
from .models import *
from .serializers import *
from . import media as imagekit
from .email_backend import email_is_configured, NotificationRejected

@require_safe
def health(request):
    # Outside /api/: Render can probe readiness without the private proxy secret.
    # No company information, credentials or exception text is disclosed.
    try:
        Company.objects.filter(pk=1).exists()
    except DatabaseError:
        response = JsonResponse({'status':'unavailable'}, status=503)
    else:
        response = JsonResponse({'status':'ok'})
    response['Cache-Control'] = 'no-store, private'
    return response

def rate(request, label, limit, seconds=3600):
    # Reverse proxy must overwrite X-Real-IP; direct access to Gunicorn must be blocked.
    ip=getattr(request,'estmajo_client_ip',None) or request.META.get('HTTP_X_REAL_IP') or request.META.get('REMOTE_ADDR','unknown')
    now=timezone.now(); window=int(now.timestamp())//seconds
    key=hashlib.sha256(f'{label}:{ip}:{window}'.encode()).hexdigest()
    with transaction.atomic():
        RateBucket.objects.filter(expires__lt=now).delete()
        b,_=RateBucket.objects.select_for_update().get_or_create(key=key,defaults={'expires':now+datetime.timedelta(seconds=seconds)})
        if b.count>=limit: raise Throttled(detail='Too many attempts. Please try again later.')
        RateBucket.objects.filter(pk=key).update(count=F('count')+1)

@method_decorator(csrf_protect,name='dispatch')
class AuthView(APIView):
    permission_classes=[AllowAny]
    @method_decorator(ensure_csrf_cookie)
    def get(self,request):
        return Response({'authenticated':bool(request.user and request.user.is_active and request.user.is_staff),'username':request.user.username if request.user else '', 'csrf':get_token(request)})
    def post(self,request):
        rate(request,'login',10,900)
        credentials=LoginSerializer(data=request.data)
        credentials.is_valid(raise_exception=True)
        user=authenticate(request,**credentials.validated_data)
        if not user or not user.is_staff or not user.is_active: return Response({'detail':'Incorrect username or password.'},status=400)
        login(request,user)
        return Response({'authenticated':True,'username':user.username,'csrf':get_token(request)})
    def delete(self,request):
        logout(request)
        return Response({'detail':'Logged out.'})
class PasswordView(APIView):
    def post(self,request):
        if not request.user.check_password(request.data.get('current_password','')): raise ValidationError({'current_password':'Current password is incorrect.'})
        new=request.data.get('new_password','')
        try: validate_password(new,request.user)
        except DjangoValidationError as e: raise ValidationError({'new_password':e.messages})
        request.user.set_password(new); request.user.save(); update_session_auth_hash(request,request.user)
        return Response({'detail':'Password updated.'})
class SettingsView(APIView):
    def get(self,request): return Response(CompanySerializer(Company.current()).data)
    def put(self,request):
        obj=Company.current()
        ser=CompanySerializer(obj,data=request.data); ser.is_valid(raise_exception=True); ser.save()
        return Response(ser.data)
class ContentViewSet(viewsets.ModelViewSet):
    queryset=Content.objects.prefetch_related('attachments__media').all()
    serializer_class=ContentSerializer
    def perform_create(self,serializer):
        with transaction.atomic(): serializer.save()
    def perform_update(self,serializer):
        with transaction.atomic(): serializer.save()
class DocumentViewSet(viewsets.ModelViewSet):
    queryset=Document.objects.select_related('media').all()
    serializer_class=DocumentSerializer
class MediaViewSet(viewsets.ModelViewSet):
    queryset=Media.objects.all()
    serializer_class=MediaSerializer
    http_method_names=['get','post','patch','delete','head','options']
    def create(self,request):
        if 'file' not in request.FILES: raise ValidationError('Choose a file to upload.')
        obj=imagekit.upload(request.FILES['file'])
        return Response(MediaSerializer(obj).data,status=201)
    def destroy(self,request,*args,**kwargs):
        obj=self.get_object()
        if imagekit.in_use(obj): return Response({'detail':'This asset is still referenced. Remove its content, settings, document and gallery references first.'},status=409)
        imagekit.api('DELETE',f'files/{obj.file_id}')
        obj.delete()
        return Response(status=204)
    def perform_update(self,serializer):
        if serializer.validated_data.get('gallery') and serializer.instance.kind=='document': raise ValidationError('PDF files belong in company documents.')
        serializer.save()
def notify(enquiry_id, force=False):
    # Claim with a single conditional update: simultaneous retries cannot send twice.
    claimable=['pending','failed']+(['unknown'] if force else [])
    claimed=Enquiry.objects.filter(pk=enquiry_id,status__in=claimable).update(status='sending',attempts=F('attempts')+1,last_error='',notification_started_at=timezone.now())
    if not claimed: return
    e=Enquiry.objects.select_related('service').get(pk=enquiry_id)
    recipient=Company.current().enquiry_recipient
    if not recipient or not email_is_configured():
        Enquiry.objects.filter(pk=e.pk).update(status='failed',last_error='Company enquiry recipient or server email configuration is missing.')
        return
    try:
        mail=EmailMessage(subject=f'Website enquiry #{e.pk}: {e.subject}',body=f'Name: {e.name}\nEmail: {e.email}\nTelephone: {e.telephone}\nService: {e.service.title if e.service else "Not selected"}\n\n{e.message}',from_email=settings.DEFAULT_FROM_EMAIL,to=[recipient],reply_to=[e.email],headers={'Message-ID':f'<esmajo-enquiry-{e.token}@{settings.DEFAULT_FROM_EMAIL.split("@")[-1].strip(">")}> ' .strip()})
        count=mail.send(fail_silently=False)
        if count!=1: raise RuntimeError('Provider did not acknowledge acceptance')
        Enquiry.objects.filter(pk=e.pk).update(status='accepted',notified_at=timezone.now(),last_error='')
    except NotificationRejected:
        Enquiry.objects.filter(pk=e.pk).update(status='failed',last_error='Email provider rejected the notification. Check provider settings and quota before retrying.')
    except Exception:
        # SMTP failures after DATA can be ambiguous. Do not automatically retry.
        Enquiry.objects.filter(pk=e.pk).update(status='unknown',last_error='Email acceptance could not be confirmed. Check the provider before retrying; a retry may send a duplicate notification.')
class EnquiryAdminViewSet(viewsets.ReadOnlyModelViewSet):
    queryset=Enquiry.objects.select_related('service').all()
    serializer_class=EnquirySerializer
    @action(detail=True,methods=['post'])
    def retry(self,request,pk=None):
        e=self.get_object()
        force=request.data.get('confirm_possible_duplicate') is True
        if e.status in ['sending','unknown'] and not force: return Response({'detail':'Check your provider first, then confirm a possible duplicate before retrying.'},status=409)
        if e.status=='sending' and (not e.notification_started_at or timezone.now()-e.notification_started_at < datetime.timedelta(minutes=5)):
            return Response({'detail':'Notification is still in progress. Wait at least five minutes and check the provider before retrying.'},status=409)
        if e.status=='sending' and force: Enquiry.objects.filter(pk=e.pk,status='sending').update(status='unknown')
        notify(e.pk,force=force)
        e.refresh_from_db(); return Response(EnquirySerializer(e).data)
    @action(detail=True,methods=['post'])
    def mark_read(self,request,pk=None):
        e=self.get_object(); e.read=True; e.save(update_fields=['read']); return Response({'read':True})
class OverviewView(APIView):
    def get(self,request):
        return Response({'services':Content.objects.filter(kind='service').count(),'projects':Content.objects.filter(kind='project').count(),'published':Content.objects.filter(published=True).count(),'media':Media.objects.count(),'enquiries':Enquiry.objects.count(),'unread':Enquiry.objects.filter(read=False).count(),'notification_issues':Enquiry.objects.filter(status__in=['failed','unknown','sending']).count(),'imagekit_configured':bool(settings.IMAGEKIT_PRIVATE_KEY and settings.IMAGEKIT_URL_ENDPOINT),'email_configured':bool(email_is_configured() and Company.current().enquiry_recipient)})
def public_asset(obj):
    if not obj: return None
    return {'id':obj.pk,'url':imagekit.delivery_url(obj),'name':obj.name,'kind':obj.kind,'alt':obj.alt,'caption':obj.caption,'width':obj.width,'height':obj.height,'responsive':{str(w):imagekit.delivery_url(obj,w) for w in [480,960,1600]} if obj.kind=='image' else {}}
def public_content(obj):
    return {'id':obj.pk,'kind':obj.kind,'slug':obj.slug,'title':obj.title,'summary':obj.summary,'body':obj.body,'attachments':[{'asset':public_asset(a.media),'alt':a.alt,'caption':a.caption,'cover':a.cover} for a in obj.attachments.select_related('media').all()]}
class PublicView(APIView):
    permission_classes=[AllowAny]
    def get(self,request):
        c=Company.current(); d=dict(c.data)
        for key in ['emails','phones','offices','socials','additional']:
            d[key]=sorted([v for v in d.get(key,[]) if v.get('visible',True) and (key!='socials' or v.get('verified'))],key=lambda x:x.get('order',0))
        for key in ['logo','favicon','ceo_photo','sharing_image']:
            d[key]=public_asset(Media.objects.filter(pk=d[key]).first()) if d.get(key) else None
        if not d.get('logo') and d.get('use_supplied_logo', False):
            d['logo']={'id':0,'name':'Supplied ESTMAJO company logo','kind':'image','url':'/brand/estmajo-logo.jpg','alt':'ESTMAJO ENGINEERING SOLUTIONS LTD','caption':'','width':1536,'height':1536,'responsive':{}}
        result={'company':d,'content':[public_content(obj) for obj in Content.objects.filter(published=True).prefetch_related('attachments__media')],'gallery':[public_asset(m) for m in Media.objects.filter(gallery=True).exclude(kind='document')],'documents':[{'id':doc.pk,'title':doc.title,'profile':doc.profile,'asset':public_asset(doc.media)} for doc in Document.objects.filter(public=True).select_related('media')]}
        response=Response(result); response['Cache-Control']='no-store, private'; return response
@method_decorator(csrf_protect,name='dispatch')
class EnquiryPublicView(APIView):
    permission_classes=[AllowAny]
    def post(self,request):
        rate(request,'enquiry',5,3600)
        ser=EnquirySerializer(data=request.data); ser.is_valid(raise_exception=True)
        token=ser.validated_data['token']
        try:
            with transaction.atomic():
                e=ser.save()
        except IntegrityError:
            e=Enquiry.objects.get(token=token)
            # Do not disclose an existing submission to a different payload.
            if e.email!=ser.validated_data['email'] or e.message!=ser.validated_data['message']: raise ValidationError('Submission reference already used. Reload the form.')
        notify(e.pk); e.refresh_from_db()
        return Response({'id':e.pk,'saved':True,'notification_status':e.status,'detail':'Your enquiry has been saved. Email notification accepted by the mail provider.' if e.status=='accepted' else 'Your enquiry has been saved. Email notification has not been confirmed.'},status=201)

class DocumentDownloadView(APIView):
    permission_classes=[AllowAny]
    def get(self,request,pk):
        from django.http import StreamingHttpResponse
        from django.shortcuts import get_object_or_404
        from django.utils.http import content_disposition_header
        import requests
        qs=Document.objects.select_related('media')
        if not (request.user and request.user.is_active and request.user.is_staff): qs=qs.filter(public=True)
        doc=get_object_or_404(qs,pk=pk)
        url=imagekit.delivery_url(doc.media)
        if not url: return Response({'detail':'Document delivery is not configured.'},status=503)
        try:
            upstream=requests.get(url,stream=True,timeout=45)
            upstream.raise_for_status()
        except requests.RequestException:
            return Response({'detail':'The document is temporarily unavailable. Please try again later.'},status=502)
        def chunks():
            try:
                yield from upstream.iter_content(chunk_size=65536)
            finally: upstream.close()
        response=StreamingHttpResponse(chunks(),content_type='application/pdf')
        response['Content-Disposition']=content_disposition_header(True,doc.media.name)
        response['Cache-Control']='no-store, private'
        return response
