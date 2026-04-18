from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView
from .views import (
    RegisterView, 
    ReportCreateView, 
    RecordListView,
    RecordDetailView, 
    ExportStubView
)

urlpatterns = [
    # Auth endpoints
    path('auth/register/', RegisterView.as_view(), name='auth_register'),
    path('auth/login/', TokenObtainPairView.as_view(), name='auth_login'),

    # Reports
    path('reports/', ReportCreateView.as_view(), name='report_create'),
    
    # Records
    path('reports/<uuid:report_id>/records/', RecordListView.as_view(), name='record_list'),
    path('reports/<uuid:report_id>/records/<uuid:record_id>/', RecordDetailView.as_view(), name='record_detail'),

    # Export endpoints
    path('reports/export/', ExportStubView.as_view(), name='export_post'),
    path('reports/<uuid:report_id>/export/', ExportStubView.as_view(), name='export_pdf_get'),
]
