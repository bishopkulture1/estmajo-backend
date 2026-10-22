import re
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from rest_framework import serializers as s
from .models import Company, Media, Content, Attachment, Document, Enquiry
class LoginSerializer(s.Serializer):
    username = s.CharField(max_length=150, trim_whitespace=True)
    password = s.CharField(max_length=1024, trim_whitespace=False, write_only=True)

class WebURL(s.URLField):
    def __init__(self, **kw):
        super().__init__(allow_blank=True, required=False, max_length=2000, **kw)
    def to_internal_value(self, value):
        value = super().to_internal_value(value)
        if value and not value.startswith(('https://','http://')):
            raise s.ValidationError('Use a complete http:// or https:// link.')
        return value
class PhoneField(s.CharField):
    def to_internal_value(self, value):
        value = super().to_internal_value(value)
        if value and not re.fullmatch(r'\+[1-9]\d{6,14}', value):
            raise s.ValidationError('Use international format, for example +234 followed by the national number without its leading zero (7–15 digits total).')
        return value
class Entry(s.Serializer):
    label = s.CharField(max_length=100, required=False, allow_blank=True, default='')
    visible = s.BooleanField(default=True)
    order = s.IntegerField(default=0)
class EmailEntry(Entry):
    email = s.EmailField()
class PhoneEntry(Entry):
    number = PhoneField()
    extension = s.RegexField(r'^\d{0,8}$', allow_blank=True, required=False, default='')
    primary = s.BooleanField(default=False)
class OfficeEntry(Entry):
    address = s.CharField(max_length=1000)
    city = s.CharField(max_length=100, allow_blank=True, required=False, default='')
    region = s.CharField(max_length=100, allow_blank=True, required=False, default='')
    postcode = s.CharField(max_length=40, allow_blank=True, required=False, default='')
    country = s.CharField(max_length=100, allow_blank=True, required=False, default='')
    map_url = WebURL()
    directions_url = WebURL()
class LinkEntry(Entry):
    url = WebURL()
    verified = s.BooleanField(default=False)
class DetailEntry(Entry):
    text = s.CharField(max_length=2000, allow_blank=True, required=False, default='')
    url = WebURL()
class Hour(s.Serializer):
    day = s.ChoiceField(choices=['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'])
    closed = s.BooleanField(default=True)
    opens = s.TimeField(required=False, allow_null=True)
    closes = s.TimeField(required=False, allow_null=True)
    def validate(self, d):
        if not d['closed'] and (not d.get('opens') or not d.get('closes') or d['opens'] >= d['closes']):
            raise s.ValidationError('An open day needs opening and closing times; closing must be later on the same day.')
        return d
class CompanyData(s.Serializer):
    use_supplied_logo = s.BooleanField(required=False)
    official_name = s.CharField(max_length=200, required=False, allow_blank=True)
    trading_name = s.CharField(max_length=200, required=False, allow_blank=True)
    tagline = s.CharField(max_length=250, required=False, allow_blank=True)
    registration_number = s.CharField(max_length=100, required=False, allow_blank=True)
    short_intro = s.CharField(max_length=1000, required=False, allow_blank=True)
    description = s.CharField(max_length=20000, required=False, allow_blank=True)
    mission = s.CharField(max_length=5000, required=False, allow_blank=True)
    vision = s.CharField(max_length=5000, required=False, allow_blank=True)
    values = s.CharField(max_length=5000, required=False, allow_blank=True)
    year_established = s.IntegerField(min_value=1800, max_value=2100, required=False, allow_null=True)
    primary_email = s.EmailField(required=False, allow_blank=True)
    emails = EmailEntry(many=True, required=False)
    phones = PhoneEntry(many=True, required=False)
    offices = OfficeEntry(many=True, required=False)
    socials = LinkEntry(many=True, required=False)
    additional = DetailEntry(many=True, required=False)
    whatsapp = PhoneField(required=False, allow_blank=True)
    whatsapp_message = s.CharField(max_length=1000, required=False, allow_blank=True)
    timezone = s.CharField(required=False, allow_blank=True)
    hours = Hour(many=True, required=False)
    holiday_notice = s.CharField(max_length=1000, required=False, allow_blank=True)
    ceo_name = s.CharField(max_length=200, required=False, allow_blank=True)
    ceo_position = s.CharField(max_length=200, required=False, allow_blank=True)
    ceo_bio = s.CharField(max_length=10000, required=False, allow_blank=True)
    ceo_message = s.CharField(max_length=10000, required=False, allow_blank=True)
    footer_description = s.CharField(max_length=1000, required=False, allow_blank=True)
    copyright_owner = s.CharField(max_length=200, required=False, allow_blank=True)
    seo_title = s.CharField(max_length=250, required=False, allow_blank=True)
    seo_description = s.CharField(max_length=500, required=False, allow_blank=True)
    privacy_text = s.CharField(max_length=20000, required=False, allow_blank=True)
    logo = s.IntegerField(required=False, allow_null=True)
    favicon = s.IntegerField(required=False, allow_null=True)
    ceo_photo = s.IntegerField(required=False, allow_null=True)
    sharing_image = s.IntegerField(required=False, allow_null=True)
    def validate_timezone(self, value):
        if value:
            try: ZoneInfo(value)
            except ZoneInfoNotFoundError: raise s.ValidationError('Use an IANA timezone such as Africa/Lagos.')
        return value
    def validate(self, d):
        for field in ['logo','favicon','ceo_photo','sharing_image']:
            if d.get(field) and not Media.objects.filter(pk=d[field],kind='image').exists():
                raise s.ValidationError({field:'Choose an uploaded image.'})
        if sum(p.get('primary',False) for p in d.get('phones',[])) > 1:
            raise s.ValidationError({'phones':'Select only one primary telephone number.'})
        days=[h['day'] for h in d.get('hours',[])]
        if len(days)!=len(set(days)): raise s.ValidationError({'hours':'Each day may appear only once.'})
        for key in ['emails','phones','offices','socials','additional']:
            if len(d.get(key,[]))>50: raise s.ValidationError({key:'Maximum 50 entries.'})
        return d
class CompanySerializer(s.ModelSerializer):
    data = CompanyData()
    def validate_data(self,value):
        return CompanyData(value).data
    class Meta:
        model = Company
        fields = ['data','enquiry_recipient','updated_at']
        read_only_fields = ['updated_at']
class MediaSerializer(s.ModelSerializer):
    references = s.SerializerMethodField()
    url = s.SerializerMethodField()
    class Meta:
        model=Media
        fields=['id','name','kind','mime','size','width','height','alt','caption','gallery','order','url','references','created_at']
        read_only_fields=['id','name','kind','mime','size','width','height','url','references','created_at']
    def get_url(self, obj):
        from .media import delivery_url
        return delivery_url(obj)
    def get_references(self,obj):
        from .media import references
        return references(obj)
class AttachmentSerializer(s.ModelSerializer):
    media = s.PrimaryKeyRelatedField(queryset=Media.objects.all())
    asset = MediaSerializer(source='media', read_only=True)
    class Meta:
        model=Attachment
        fields=['media','asset','caption','alt','order','cover']
class ContentSerializer(s.ModelSerializer):
    attachments = AttachmentSerializer(many=True, required=False)
    class Meta:
        model=Content
        fields=['id','kind','title','slug','summary','body','published','order','attachments','updated_at']
        read_only_fields=['id','updated_at']
    def validate_attachments(self, rows):
        if len({r['media'].pk for r in rows})!=len(rows): raise s.ValidationError('Do not attach the same asset twice.')
        if sum(r.get('cover',False) for r in rows)>1: raise s.ValidationError('Select only one cover.')
        if any(r['media'].kind=='document' for r in rows): raise s.ValidationError('Use company documents for PDF files.')
        if any(r.get('cover') and r['media'].kind!='image' for r in rows): raise s.ValidationError('The cover must be an image.')
        return rows
    def create(self,d):
        rows=d.pop('attachments',[])
        obj=Content.objects.create(**d)
        for row in rows: Attachment.objects.create(content=obj,**row)
        return obj
    def update(self,obj,d):
        rows=d.pop('attachments',None)
        obj=super().update(obj,d)
        if rows is not None:
            obj.attachments.all().delete()
            for row in rows: Attachment.objects.create(content=obj,**row)
        return obj
class DocumentSerializer(s.ModelSerializer):
    asset = MediaSerializer(source='media',read_only=True)
    class Meta:
        model=Document
        fields=['id','title','media','asset','public','profile','order']
    def validate_media(self,value):
        if value.kind!='document': raise s.ValidationError('Choose an uploaded PDF.')
        return value
class EnquirySerializer(s.ModelSerializer):
    telephone = PhoneField(required=False,allow_blank=True)
    service = s.PrimaryKeyRelatedField(queryset=Content.objects.filter(kind='service',published=True),required=False,allow_null=True)
    website = s.CharField(required=False,allow_blank=True,write_only=True)
    class Meta:
        model=Enquiry
        fields=['id','token','name','email','telephone','service','subject','message','website','status','attempts','last_error','read','created_at','notified_at']
        read_only_fields=['id','status','attempts','last_error','read','created_at','notified_at']
        extra_kwargs={'message':{'max_length':10000,'min_length':10},'token':{'validators':[]}}
    def validate_website(self,v):
        if v: raise s.ValidationError('Unable to submit this form.')
        return v
    def create(self,d):
        d.pop('website',None)
        return super().create(d)
