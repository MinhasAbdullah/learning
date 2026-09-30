from .serializers import RegisterSerializer, UserSerializer, CompanySerializer, JobSerializer, TagsSerializer   , ApplicationSerializer
from rest_framework import generics, permissions, viewsets
from .models import Job, Company, Application, Tag
from django.contrib.auth import get_user_model
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.filters import SearchFilter, OrderingFilter
from .pagination import JobPagination, ApplicationPagination
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from .exceptions import AlreadyAplliedException


User = get_user_model()

class LoginThrottle(TokenObtainPairView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'login'


class IsOwnerOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        owner = getattr(obj, 'owner', getattr(obj, 'applicant', None))
        return owner == request.user

class IsCompanyOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.company.owner == request.user
    

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'register'

class CompanyViewSet(viewsets.ModelViewSet):
    queryset = Company.objects.select_related('owner').all()
    serializer_class = CompanySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class JobViewSet(viewsets.ModelViewSet):
    queryset = Job.objects.select_related('company', 'company__owner').prefetch_related('tags').all()
    serializer_class = JobSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsCompanyOwner]
    filterset_fields = ['company', 'tags', 'salary']
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['title', 'description']
    ordering_fields = ['salary', 'created_at']
    pagination_class = JobPagination

    def perform_create(self, serializer):
        company = serializer.validated_data.get('company')
        if company.owner != self.request.user:
            raise PermissionDenied("You do not have permission to create a job for this company.")
        serializer.save()

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def apply(self, request, pk=None):
        job = self.get_object()
        if Application.objects.filter(job=job, applicant=request.user).exists():
            raise AlreadyAplliedException()
        application = Application.objects.create(job=job, applicant=request.user)
        return Response({'status': 'application submitted', 'application_id': application.id})

    @action(detail=True, methods=['get'], permission_classes=[IsOwnerOrReadOnly])
    def applications(self, request, pk=None):
        job = self.get_object()
        if job.company.owner != request.user:
            raise PermissionDenied("Only the company owner can view applications for this job.")
        applications = job.applications.select_related('applicant', 'job').all()
        serializer = ApplicationSerializer(applications, many=True)
        return Response(serializer.data)

class ApplicationViewSet(viewsets.ModelViewSet):
    serializer_class = ApplicationSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = ApplicationPagination
    def get_queryset(self):
        user = self.request.user
        # Shows applications user submitted, OR applications for jobs belonging to companies user owns
        return Application.objects.select_related('job', 'applicant', 'job__company').filter(
            applicant=user
        ) | Application.objects.select_related('job', 'applicant', 'job__company').filter(
            job__company__owner=user
        )

class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagsSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]