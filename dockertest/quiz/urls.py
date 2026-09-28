from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RegisterView, CompanyViewSet, JobViewSet, TagViewSet, ApplicationViewSet

router = DefaultRouter()
router.register('companies', CompanyViewSet, basename='company')
router.register('jobs', JobViewSet, basename='job')
router.register('tags', TagViewSet, basename='tag')
router.register('applications', ApplicationViewSet, basename='application')


urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('', include(router.urls)),
    path('api-auth/', include('rest_framework.urls')),
]