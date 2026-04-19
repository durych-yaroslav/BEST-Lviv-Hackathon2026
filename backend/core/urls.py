from django.urls import path
from .views import (
    RegisterView,
    CustomTokenLoginView,
    ReportCreateView, 
    RecordListView,
    RecordDetailView, 
    ReportExportView,
    AIAnalysisView,
)

urlpatterns = [
    # Auth endpoints
    path('auth/register/', RegisterView.as_view(), name='auth_register'),
    path('auth/login/', CustomTokenLoginView.as_view(), name='auth_login'),

    # Reports
    path('reports/', ReportCreateView.as_view(), name='report_create'),
    
    # Records
    path('reports/<uuid:report_id>/records/', RecordListView.as_view(), name='record_list'),
    path('reports/<uuid:report_id>/records/<uuid:record_id>/', RecordDetailView.as_view(), name='record_detail'),

    # Export endpoints — both handled by ReportExportView
    path('reports/export/', ReportExportView.as_view(), name='export_post'),
    path('reports/<uuid:report_id>/export/', ReportExportView.as_view(), name='export_pdf_get'),

    # AI Analysis
    path('reports/ai-analysis', AIAnalysisView.as_view(), name='ai_analysis'),
]
