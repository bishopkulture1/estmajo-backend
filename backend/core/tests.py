import io, uuid
from unittest.mock import patch, Mock
from django.test import TestCase, override_settings, Client
from django.contrib.auth import get_user_model
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from PIL import Image
from .models import Company, Content, Media, Document, Enquiry
from .media import delivery_url
from .views import notify

@override_settings(SECURE_SSL_REDIRECT=False,ALLOWED_HOSTS=['testserver'],EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',DEFAULT_FROM_EMAIL='website@example.com')
class ApplicationTests(TestCase):
    def setUp(self):
        Company.objects.update_or_create(pk=1,defaults={'data':{},'enquiry_recipient':''})
        self.owner=get_user_model().objects.create_user('owner',password='A-Strong-Testing-Password-738',is_staff=True)
        self.client=APIClient(); self.client.force_authenticate(self.owner)
        self.public=APIClient()
    def asset(self,kind='image'):
        return Media.objects.create(file_id=str(uuid.uuid4()),url='https://ik.imagekit.io/test/file.png',name='file.png',kind=kind,mime='image/png' if kind=='image' else 'application/pdf',size=100)
    def enquiry(self):
        return {'token':str(uuid.uuid4()),'name':'Visitor','email':'visitor@example.com','telephone':'+2348012345678','subject':'Project enquiry','message':'Please discuss our project requirements.','website':''}
    def settings(self,data,recipient=''):
        return self.client.put('/api/owner/settings/',{'data':data,'enquiry_recipient':recipient},format='json')
    def test_all_owner_resources_reject_anonymous(self):
        for path in ['settings/','overview/','content/','media/','documents/','enquiries/']:
            self.assertEqual(self.public.get('/api/owner/'+path).status_code,403)
    def test_non_staff_user_rejected(self):
        regular=get_user_model().objects.create_user('regular',password='strong-pass-123')
        self.public.force_authenticate(regular)
        self.assertEqual(self.public.get('/api/owner/settings/').status_code,403)
    def test_login_csrf_logout_and_password(self):
        c=Client(enforce_csrf_checks=True)
        self.assertEqual(c.post('/api/auth/',{'username':'owner','password':'A-Strong-Testing-Password-738'},content_type='application/json').status_code,403)
        r=c.get('/api/auth/'); token=r.json()['csrf']
        r=c.post('/api/auth/',{'username':'owner','password':'A-Strong-Testing-Password-738'},content_type='application/json',HTTP_X_CSRFTOKEN=token)
        self.assertEqual(r.status_code,200)
        token=r.json()['csrf']; self.assertTrue(c.cookies['sessionid']['httponly'])
        self.assertEqual(c.get('/api/owner/settings/').status_code,200)
        self.assertEqual(c.put('/api/owner/settings/',{'data':{},'enquiry_recipient':''},content_type='application/json').status_code,403)
        r=c.post('/api/password/',{'current_password':'A-Strong-Testing-Password-738','new_password':'Different-Strong-Password-274'},content_type='application/json',HTTP_X_CSRFTOKEN=token)
        self.assertEqual(r.status_code,200)
        self.assertEqual(c.delete('/api/auth/',HTTP_X_CSRFTOKEN=token).status_code,200)
        self.assertEqual(c.get('/api/owner/settings/').status_code,403)
    def test_invalid_login_and_inactive(self):
        self.assertEqual(self.public.post('/api/auth/',{'username':'owner','password':'wrong'},format='json').status_code,400)
        self.owner.is_active=False; self.owner.save()
        self.assertEqual(self.public.post('/api/auth/',{'username':'owner','password':'A-Strong-Testing-Password-738'},format='json').status_code,400)
    def test_login_validation_password_whitespace_and_rate_limit(self):
        for data in [{}, {'username':'owner','password':''}, {'username':'x'*151,'password':'secret'}, {'username':'owner','password':'x'*1025}]:
            self.assertEqual(self.public.post('/api/auth/',data,format='json').status_code,400)
        self.owner.set_password('  Secret-Whitespace-Password-782  '); self.owner.save()
        self.assertEqual(self.public.post('/api/auth/',{'username':'owner','password':'  Secret-Whitespace-Password-782  '},format='json').status_code,200)
        self.public.delete('/api/auth/')
        for _ in range(5):
            self.assertEqual(self.public.post('/api/auth/',{'username':'owner','password':'wrong'},format='json').status_code,400)
        self.assertEqual(self.public.post('/api/auth/',{'username':'owner','password':'wrong'},format='json').status_code,429)

    def test_login_session_rotation_persistence_and_revocation(self):
        c=Client(enforce_csrf_checks=True)
        session=c.session; session['pre_login']='retained'; session.save()
        c.cookies['sessionid']=session.session_key
        old_key=session.session_key
        csrf=c.get('/api/auth/').json()['csrf']
        r=c.post('/api/auth/',{'username':'owner','password':'A-Strong-Testing-Password-738'},content_type='application/json',HTTP_X_CSRFTOKEN=csrf)
        self.assertEqual(r.status_code,200)
        self.assertNotEqual(old_key,c.cookies['sessionid'].value)
        self.assertNotEqual(csrf,r.json()['csrf'])
        # A fresh client with only the server-issued cookie reads the persisted session.
        fresh=Client(enforce_csrf_checks=True); fresh.cookies=c.cookies.copy()
        self.assertTrue(fresh.get('/api/auth/').json()['authenticated'])
        self.assertEqual(fresh.get('/api/owner/settings/').status_code,200)
        token=fresh.get('/api/auth/').json()['csrf']
        self.assertEqual(fresh.delete('/api/auth/',HTTP_X_CSRFTOKEN=token).status_code,200)
        self.assertEqual(c.get('/api/owner/settings/').status_code,403)
        self.assertFalse(fresh.get('/api/auth/').json()['authenticated'])

    def test_password_change_revokes_other_sessions_and_rejects_weak_password(self):
        clients=[Client(enforce_csrf_checks=True),Client(enforce_csrf_checks=True)]
        for c in clients:
            token=c.get('/api/auth/').json()['csrf']
            self.assertEqual(c.post('/api/auth/',{'username':'owner','password':'A-Strong-Testing-Password-738'},content_type='application/json',HTTP_X_CSRFTOKEN=token).status_code,200)
        c=clients[0]; token=c.get('/api/auth/').json()['csrf']
        self.assertEqual(c.post('/api/password/',{'current_password':'A-Strong-Testing-Password-738','new_password':'123'},content_type='application/json',HTTP_X_CSRFTOKEN=token).status_code,400)
        self.assertEqual(c.post('/api/password/',{'current_password':'A-Strong-Testing-Password-738','new_password':'Fresh-Strong-Password-278'},content_type='application/json',HTTP_X_CSRFTOKEN=token).status_code,200)
        self.assertEqual(c.get('/api/owner/settings/').status_code,200)
        self.assertEqual(clients[1].get('/api/owner/settings/').status_code,403)

    def test_add_contact_details_after_setup_persist_and_private_filter(self):
        self.assertEqual(self.settings({}).status_code,200)
        data={'official_name':'Owner supplied name','primary_email':'public@example.com','emails':[{'label':'Sales','email':'sales@example.com','visible':True,'order':2},{'label':'Hidden','email':'private@example.com','visible':False}], 'phones':[{'number':'+2348012345678','primary':True,'visible':True},{'number':'+2348098765432','visible':True}], 'offices':[{'label':'Main','address':'Owner supplied address','city':'Owner supplied city','visible':True},{'label':'Branch','address':'Another supplied address','visible':True}], 'socials':[{'label':'Official','url':'https://example.com/social','visible':True,'verified':True},{'label':'Unverified','url':'https://example.com/no','visible':True,'verified':False}], 'additional':[{'label':'Detail','text':'Approved information','visible':True}]}
        r=self.settings(data,'internal@example.com'); self.assertEqual(r.status_code,200,r.data)
        # Read via a separate anonymous client, without relying on browser state.
        p=self.public.get('/api/public/'); c=p.data['company']
        self.assertEqual(c['official_name'],'Owner supplied name'); self.assertEqual(len(c['phones']),2); self.assertEqual(len(c['offices']),2)
        self.assertEqual(len(c['emails']),1);self.assertEqual(len(c['socials']),1)
        self.assertNotIn('internal@example.com',str(p.data));self.assertNotIn('private@example.com',str(p.data))
        self.assertIn('no-store',p['Cache-Control'])
        self.assertEqual(Company.objects.get(pk=1).enquiry_recipient,'internal@example.com')
    def test_reorder_hide_delete_and_latest_settings(self):
        data={'phones':[{'number':'+2348012345678','order':9,'visible':True},{'number':'+2348098765432','order':0,'visible':True}]}
        self.settings(data);self.assertEqual(self.public.get('/api/public/').data['company']['phones'][0]['number'],'+2348098765432')
        data['phones'][1]['visible']=False;self.settings(data);self.assertEqual(len(self.public.get('/api/public/').data['company']['phones']),1)
        self.settings({'phones':[]});self.assertEqual(self.public.get('/api/public/').data['company']['phones'],[])
    def test_settings_validation_and_no_arbitrary_fields(self):
        for d in [{'primary_email':'bad'},{'phones':[{'number':'08012345678'}]},{'offices':[{'address':'A','map_url':'javascript:alert(1)'}]},{'socials':[{'url':'data:text/html,x'}]},{'timezone':'Not/AZone'},{'phones':[{'number':'+2348012345678','primary':True},{'number':'+2348098765432','primary':True}]}]:
            self.assertEqual(self.settings(d).status_code,400,d)
        self.settings({'injected_script':'alert(1)'})
        self.assertNotIn('injected_script',Company.current().data)
    def test_business_hours_serialized_to_database(self):
        r=self.settings({'timezone':'Africa/Lagos','hours':[{'day':'Monday','closed':False,'opens':'08:00','closes':'17:00'},{'day':'Sunday','closed':True}]})
        self.assertEqual(r.status_code,200,r.data);self.assertEqual(Company.current().data['hours'][0]['opens'],'08:00:00')
        self.assertEqual(self.settings({'hours':[{'day':'Monday','closed':False}]}).status_code,400)
    def test_services_and_project_publish_unpublish_delete(self):
        for kind in ['service','project']:
            r=self.client.post('/api/owner/content/',{'kind':kind,'title':'Approved '+kind,'slug':'approved-'+kind,'body':'Owner supplied text','published':False},format='json')
            self.assertEqual(r.status_code,201,r.data); pk=r.data['id']
            self.assertEqual(len(self.public.get('/api/public/').data['content']),0)
            self.client.patch(f'/api/owner/content/{pk}/',{'published':True},format='json'); self.assertEqual(len(self.public.get('/api/public/').data['content']),1)
            self.client.patch(f'/api/owner/content/{pk}/',{'published':False},format='json'); self.assertEqual(len(self.public.get('/api/public/').data['content']),0)
            self.assertEqual(self.client.delete(f'/api/owner/content/{pk}/').status_code,204)
    def test_private_media_not_public_and_shared_delete_blocked(self):
        m=self.asset(); self.assertEqual(self.public.get('/api/public/').data['gallery'],[])
        self.settings({'logo':m.pk})
        self.assertEqual(self.client.delete(f'/api/owner/media/{m.pk}/').status_code,409)
        self.settings({});m.gallery=True;m.save()
        self.assertEqual(self.client.delete(f'/api/owner/media/{m.pk}/').status_code,409)
    def test_attachment_validation_and_private_documents(self):
        m=self.asset(); d=self.asset('document')
        r=self.client.post('/api/owner/content/',{'kind':'project','title':'Test','slug':'test','attachments':[{'media':m.pk,'cover':True},{'media':m.pk,'cover':True}]},format='json')
        self.assertEqual(r.status_code,400)
        r=self.client.post('/api/owner/documents/',{'title':'Company profile','media':d.pk,'public':False,'profile':True},format='json')
        self.assertEqual(r.status_code,201,r.data);self.assertEqual(self.public.get('/api/public/').data['documents'],[])
        self.client.patch(f'/api/owner/documents/{r.data["id"]}/',{'public':True},format='json')
        self.assertEqual(len(self.public.get('/api/public/').data['documents']),1)
        self.assertEqual(self.client.delete(f'/api/owner/media/{d.pk}/').status_code,409)
    def test_enquiry_saved_and_email_reply_to_and_idempotency(self):
        self.settings({},'recipient@example.com'); data=self.enquiry()
        r=self.public.post('/api/enquire/',data,format='json');self.assertEqual(r.status_code,201,r.data)
        self.assertEqual(r.data['notification_status'],'accepted');self.assertEqual(Enquiry.objects.count(),1)
        self.assertEqual(len(mail.outbox),1);self.assertEqual(mail.outbox[0].reply_to,['visitor@example.com']);self.assertEqual(mail.outbox[0].from_email,'website@example.com')
        self.public.post('/api/enquire/',data,format='json');self.assertEqual(Enquiry.objects.count(),1);self.assertEqual(len(mail.outbox),1)
    def test_missing_recipient_and_retry_without_duplicate_record(self):
        r=self.public.post('/api/enquire/',self.enquiry(),format='json');self.assertEqual(r.data['notification_status'],'failed')
        self.settings({},'recipient@example.com')
        r=self.client.post(f'/api/owner/enquiries/{r.data["id"]}/retry/',{},format='json');self.assertEqual(r.data['status'],'accepted');self.assertEqual(Enquiry.objects.count(),1)
    def test_notification_transport_failure_and_explicit_retry(self):
        self.settings({},'recipient@example.com')
        with patch('core.views.EmailMessage.send',side_effect=TimeoutError):
            r=self.public.post('/api/enquire/',self.enquiry(),format='json')
        self.assertTrue(r.data['saved']);self.assertEqual(r.data['notification_status'],'unknown')
        pk=r.data['id'];self.assertEqual(self.client.post(f'/api/owner/enquiries/{pk}/retry/',{},format='json').status_code,409)
        r=self.client.post(f'/api/owner/enquiries/{pk}/retry/',{'confirm_possible_duplicate':True},format='json');self.assertEqual(r.data['status'],'accepted');self.assertEqual(Enquiry.objects.count(),1)
    def test_spam_invalid_phone_draft_service_and_rate_limit(self):
        data=self.enquiry();data['website']='bot'
        self.assertEqual(self.public.post('/api/enquire/',data,format='json').status_code,400)
        data=self.enquiry();data['telephone']='bad';self.assertEqual(self.public.post('/api/enquire/',data,format='json').status_code,400)
        draft=Content.objects.create(kind='service',title='draft',slug='draft')
        data=self.enquiry();data['service']=draft.pk;self.assertEqual(self.public.post('/api/enquire/',data,format='json').status_code,400)
        for _ in range(2):self.public.post('/api/enquire/',self.enquiry(),format='json')
        self.assertEqual(self.public.post('/api/enquire/',self.enquiry(),format='json').status_code,429)
    def test_public_enquiry_requires_csrf(self):
        c=Client(enforce_csrf_checks=True)
        self.assertEqual(c.post('/api/enquire/',self.enquiry(),content_type='application/json').status_code,403)
    def test_empty_optional_settings_allowed(self):
        self.assertEqual(self.settings({'official_name':'','primary_email':'','whatsapp':'','logo':None,'year_established':None}).status_code,200)
    @override_settings(IMAGEKIT_PRIVATE_KEY='private_test',IMAGEKIT_URL_ENDPOINT='https://ik.imagekit.io/test')
    def test_signed_responsive_delivery_uses_sdk(self):
        m=self.asset();url=delivery_url(m,480)
        self.assertIn('ik-s=',url);self.assertIn('ik-t=',url);self.assertIn('w-480',url)
    @override_settings(IMAGEKIT_PRIVATE_KEY='private_test',IMAGEKIT_URL_ENDPOINT='https://ik.imagekit.io/test')
    @patch('core.media.requests.post')
    @patch('core.media.api')
    def test_verified_upload_for_image_video_pdf(self,api_mock,post_mock):
        im=io.BytesIO();Image.new('RGB',(5,5)).save(im,format='PNG')
        for name,mime,kind,content in [('sample.png','image/png','image',im.getvalue()),('sample.mp4','video/mp4','non-image',b'\x00\x00\x00\x20ftypisom'+b'\0'*24),('profile.pdf','application/pdf','non-image',b'%PDF-1.7\nexample')]:
            file_id=str(uuid.uuid4());post_mock.return_value=Mock(json=lambda:{'fileId':file_id})
            api_mock.return_value={'fileId':file_id,'filePath':'/'+name,'name':name,'size':len(content),'fileType':kind,'mime':mime,'isPrivateFile':True}
            r=self.client.post('/api/owner/media/',{'file':SimpleUploadedFile(name,content,content_type=mime)},format='multipart')
            self.assertEqual(r.status_code,201,r.data)
        self.assertEqual(Media.objects.count(),3)
    @override_settings(IMAGEKIT_PRIVATE_KEY='private_test',IMAGEKIT_URL_ENDPOINT='https://ik.imagekit.io/test')
    @patch('core.media.requests.post')
    @patch('core.media.api')
    def test_failed_metadata_upload_cleans_orphan(self,api_mock,post_mock):
        post_mock.return_value=Mock(json=lambda:{'fileId':'orphan'})
        api_mock.side_effect=[{'filePath':'/bad.pdf','name':'bad.pdf','size':4,'mime':'text/html','isPrivateFile':True},{}]
        r=self.client.post('/api/owner/media/',{'file':SimpleUploadedFile('bad.pdf',b'%PDF-bad')},format='multipart')
        self.assertEqual(r.status_code,400);self.assertEqual(Media.objects.count(),0)
        self.assertEqual(api_mock.call_args.args,('DELETE','files/orphan'))
    def test_unsupported_upload_and_forged_image(self):
        for name,content in [('script.svg',b'<svg/>'),('fake.png',b'<html>bad</html>')]:
            r=self.client.post('/api/owner/media/',{'file':SimpleUploadedFile(name,content)},format='multipart');self.assertEqual(r.status_code,400)
    @patch('core.media.api')
    def test_unused_media_delete(self,api_mock):
        m=self.asset();self.assertEqual(self.client.delete(f'/api/owner/media/{m.pk}/').status_code,204);self.assertFalse(Media.objects.filter(pk=m.pk).exists())

    def test_active_sending_not_retried_until_stale(self):
        import datetime
        from django.utils import timezone
        self.settings({},'recipient@example.com')
        e=Enquiry.objects.create(**{k:v for k,v in self.enquiry().items() if k!='website'},status='sending',notification_started_at=timezone.now())
        r=self.client.post(f'/api/owner/enquiries/{e.pk}/retry/',{'confirm_possible_duplicate':True},format='json')
        self.assertEqual(r.status_code,409)
        e.notification_started_at=timezone.now()-datetime.timedelta(minutes=6);e.save()
        r=self.client.post(f'/api/owner/enquiries/{e.pk}/retry/',{'confirm_possible_duplicate':True},format='json')
        self.assertEqual(r.status_code,200);self.assertEqual(r.data['status'],'accepted')

    @override_settings(IMAGEKIT_PRIVATE_KEY='private_test',IMAGEKIT_URL_ENDPOINT='https://ik.imagekit.io/test')
    @patch('requests.get')
    def test_document_download_visibility_and_attachment(self,get_mock):
        d=Document.objects.create(title='Private profile',media=self.asset('document'))
        self.assertEqual(self.public.get(f'/api/documents/{d.pk}/download/').status_code,404)
        d.public=True;d.save()
        upstream=Mock();upstream.iter_content.return_value=[b'%PDF-test'];get_mock.return_value=upstream
        r=self.public.get(f'/api/documents/{d.pk}/download/')
        self.assertEqual(r.status_code,200);self.assertIn('attachment;',r['Content-Disposition']);self.assertEqual(b''.join(r.streaming_content),b'%PDF-test');upstream.close.assert_called_once()

    def test_confirmed_company_details_and_original_logo(self):
        from importlib import import_module
        from django.apps import apps
        import_module('core.migrations.0003_confirmed_company_details').apply_details(apps,None)
        c=Company.current()
        self.assertEqual(c.enquiry_recipient,'estmajo@hotmail.com')
        result=self.public.get('/api/public/').data
        public=result['company']
        self.assertEqual(public['official_name'],'ESTMAJO ENGINEERING SOLUTIONS LTD')
        self.assertEqual(public['registration_number'],'7810123')
        self.assertEqual(public['primary_email'],'estmajo@hotmail.com')
        self.assertEqual([p['number'] for p in public['phones']],['+2348123834601','+2347065938360'])
        self.assertEqual(public['offices'][0]['city'],'Warri')
        self.assertIn('D5 Edewor Estate',public['offices'][0]['address'])
        self.assertEqual(public['logo']['url'],'/brand/estmajo-logo.jpg')
        self.assertFalse(any(row.get('label')=='Telephone awaiting confirmation' for row in c.data.get('additional',[])))
        self.assertNotIn('enquiry_recipient',str(result))

    def test_supplied_logo_toggle_and_service_seed_preserves_owner_edits(self):
        from django.core.management import call_command
        from io import StringIO
        self.settings({'official_name':'Owner updated company name','use_supplied_logo':False})
        call_command('seed_services',stdout=StringIO())
        self.assertEqual(Company.current().data['official_name'],'Owner updated company name')
        self.assertIsNone(self.public.get('/api/public/').data['company']['logo'])
        self.settings({'use_supplied_logo':True})
        self.assertEqual(self.public.get('/api/public/').data['company']['logo']['url'],'/brand/estmajo-logo.jpg')

    @override_settings(NETLIFY_PROXY_SECRET='proxy-test-secret-at-least-32-characters')
    def test_netlify_signed_proxy_and_cache_boundary(self):
        import hashlib,hmac,time
        client=APIClient()
        path='/api/public/'
        self.assertEqual(client.get(path).status_code,403)
        timestamp=str(int(time.time()));ip='192.0.2.15'
        def headers(ts,ip):
            payload=f'{ts}\n{ip}\nGET\n{path}'
            signature=hmac.new(b'proxy-test-secret-at-least-32-characters',payload.encode(),hashlib.sha256).hexdigest()
            return {'HTTP_X_ESTMAJO_PROXY_TIME':ts,'HTTP_X_ESTMAJO_PROXY_IP':ip,'HTTP_X_ESTMAJO_PROXY_SIGNATURE':signature}
        r=client.get(path,**headers(timestamp,ip))
        self.assertEqual(r.status_code,200);self.assertIn('no-store',r['Cache-Control']);self.assertIn('Cookie',r['Vary']);self.assertEqual(r['X-Estmajo-Proxy-Verified'],'1')
        forged=headers(timestamp,ip);forged['HTTP_X_ESTMAJO_PROXY_IP']='192.0.2.16'
        self.assertEqual(client.get(path,**forged).status_code,403)
        self.assertEqual(client.get(path,**headers(str(int(time.time())-120),ip)).status_code,403)

    def test_discarded_phone_note_removed_from_saved_settings(self):
        from importlib import import_module
        from django.apps import apps
        company=Company.current()
        company.data={'additional':[{'label':'Telephone awaiting confirmation','text':'discard me','visible':False},{'label':'Approved detail','text':'Keep me','visible':True}]};company.save()
        import_module('core.migrations.0004_remove_discarded_phone_note').remove_discarded_note(apps,None)
        self.assertEqual([r['label'] for r in Company.current().data['additional']],['Approved detail'])
