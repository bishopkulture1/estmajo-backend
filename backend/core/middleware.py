import hashlib
import hmac
import ipaddress
import time
from django.conf import settings
from django.http import JsonResponse
from django.utils.cache import patch_vary_headers

class ApiBoundaryMiddleware:
    def __init__(self,get_response):
        self.get_response=get_response
    def __call__(self,request):
        is_api=request.path.startswith('/api/')
        secret=settings.NETLIFY_PROXY_SECRET
        if is_api and secret:
            timestamp=request.headers.get('X-Estmajo-Proxy-Time','')
            ip=request.headers.get('X-Estmajo-Proxy-IP','')
            signature=request.headers.get('X-Estmajo-Proxy-Signature','')
            payload=f'{timestamp}\n{ip}\n{request.method}\n{request.path}'
            expected=hmac.new(secret.encode(),payload.encode(),hashlib.sha256).hexdigest()
            try:
                valid_time=abs(time.time()-int(timestamp))<=60
                ipaddress.ip_address(ip)
                valid=valid_time and hmac.compare_digest(signature,expected)
            except (ValueError,TypeError): valid=False
            if not valid:
                response=JsonResponse({'detail':'Use the authorised website to access this API.'},status=403)
                response['Cache-Control']='no-store, private'
                return response
            request.estmajo_client_ip=ip
        response=self.get_response(request)
        if is_api:
            if hasattr(request,'estmajo_client_ip'): response['X-Estmajo-Proxy-Verified']='1'
            response['Cache-Control']='no-store, private'
            patch_vary_headers(response,['Cookie'])
        return response
