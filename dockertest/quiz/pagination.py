from rest_framework.pagination import PageNumberPagination

class JobPagination(PageNumberPagination):
    page_size = 10 
    max_page_size = 50

class ApplicationPagination(PageNumberPagination):
    page_size = 5
    max_page_size = 20