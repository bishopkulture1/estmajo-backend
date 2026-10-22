from django.db import models
class Media(models.Model):
    file_id = models.CharField(max_length=255, unique=True)
    url = models.URLField(max_length=2000)
    name = models.CharField(max_length=255)
    kind = models.CharField(max_length=16)
    mime = models.CharField(max_length=100)
    size = models.PositiveBigIntegerField()
    width = models.PositiveIntegerField(default=0)
    height = models.PositiveIntegerField(default=0)
    alt = models.CharField(max_length=500, blank=True)
    caption = models.TextField(blank=True)
    gallery = models.BooleanField(default=False)
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ['order','id']
class Company(models.Model):
    data = models.JSONField(default=dict)
    enquiry_recipient = models.EmailField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    @classmethod
    def current(cls):
        return cls.objects.get_or_create(pk=1)[0]
class Content(models.Model):
    kind = models.CharField(max_length=12, choices=[('service','Service'),('project','Project')])
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True)
    summary = models.TextField(blank=True)
    body = models.TextField(blank=True)
    published = models.BooleanField(default=False)
    order = models.IntegerField(default=0)
    media = models.ManyToManyField(Media, through='Attachment', related_name='content')
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        ordering = ['order','id']
class Attachment(models.Model):
    content = models.ForeignKey(Content, on_delete=models.CASCADE, related_name='attachments')
    media = models.ForeignKey(Media, on_delete=models.PROTECT)
    caption = models.CharField(max_length=1000, blank=True)
    alt = models.CharField(max_length=500, blank=True)
    order = models.IntegerField(default=0)
    cover = models.BooleanField(default=False)
    class Meta:
        ordering = ['order','id']
        constraints = [models.UniqueConstraint(fields=['content','media'], name='unique_attachment')]
class Document(models.Model):
    title = models.CharField(max_length=200)
    media = models.ForeignKey(Media, on_delete=models.PROTECT)
    public = models.BooleanField(default=False)
    profile = models.BooleanField(default=False)
    order = models.IntegerField(default=0)
    class Meta:
        ordering = ['order','id']
class Enquiry(models.Model):
    token = models.UUIDField(unique=True)
    name = models.CharField(max_length=200)
    email = models.EmailField()
    telephone = models.CharField(max_length=40, blank=True)
    service = models.ForeignKey(Content, null=True, blank=True, on_delete=models.SET_NULL)
    subject = models.CharField(max_length=200)
    message = models.TextField()
    status = models.CharField(max_length=20, default='pending')
    attempts = models.PositiveIntegerField(default=0)
    last_error = models.CharField(max_length=500, blank=True)
    notification_started_at = models.DateTimeField(null=True, blank=True)
    notified_at = models.DateTimeField(null=True, blank=True)
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ['-created_at']
class RateBucket(models.Model):
    key = models.CharField(max_length=100, primary_key=True)
    count = models.PositiveIntegerField(default=0)
    expires = models.DateTimeField()
