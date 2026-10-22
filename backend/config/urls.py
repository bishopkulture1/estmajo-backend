from django.urls import path,include
from rest_framework.routers import DefaultRouter
from core.views import *
router=DefaultRouter()
router.register('content',ContentViewSet)
router.register('media',MediaViewSet)
router.register('documents',DocumentViewSet)
router.register('enquiries',EnquiryAdminViewSet)
urlpatterns=[path('_health/',health),path('api/documents/<int:pk>/download/',DocumentDownloadView.as_view()),path('api/auth/',AuthView.as_view()),path('api/password/',PasswordView.as_view()),path('api/public/',PublicView.as_view()),path('api/enquire/',EnquiryPublicView.as_view()),path('api/owner/settings/',SettingsView.as_view()),path('api/owner/overview/',OverviewView.as_view()),path('api/owner/',include(router.urls))]
