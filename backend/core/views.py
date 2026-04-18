from rest_framework import generics, status, views, filters
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser
from django.contrib.auth.models import User
from django.http import HttpResponse

from .models import Report, Record
from .serializers import UserRegistrationSerializer, RecordSerializer
from .services import process_excel_files
from rest_framework.pagination import PageNumberPagination
from collections import OrderedDict

from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        return {
            "access_token": data.pop('access'),
            "token_type": "Bearer"
        }

class CustomTokenLoginView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    # No auth required for registration
    permission_classes = (AllowAny,)
    serializer_class = UserRegistrationSerializer

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = 'size'
    page_query_param = 'page'
    max_page_size = 1000

    def get_paginated_response(self, data):
        return Response(OrderedDict([
            ('items', data),
            ('total', self.page.paginator.count),
            ('page', self.page.number),
            ('size', len(data)),
        ]))

class ReportCreateView(views.APIView):
    permission_classes = (IsAuthenticated,)
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        land_file = request.FILES.get('land')
        property_file = request.FILES.get('property')

        if not land_file or not property_file:
            return Response(
                {"error": "Both 'land' and 'property' files are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        report = Report.objects.create()
        records_data = process_excel_files(land_file, property_file)

        records_to_create = [
            Record(
                report=report,
                problems=data.get('problems', []),
                land_data=data.get('land_data', {}),
                property_data=data.get('property_data', {})
            )
            for data in records_data
        ]
        Record.objects.bulk_create(records_to_create)

        return Response({"report_id": str(report.id)}, status=status.HTTP_201_CREATED)

class RecordListView(generics.ListAPIView):
    serializer_class = RecordSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        report_id = self.kwargs.get('report_id')
        queryset = Record.objects.filter(report_id=report_id)

        # Filters
        problem = self.request.query_params.get('problem')
        if problem:
            queryset = queryset.filter(problems__icontains=problem)
        
        has_problems = self.request.query_params.get('has_problems')
        if has_problems:
            if has_problems.lower() == 'true':
                queryset = queryset.exclude(problems="[]").exclude(problems=[])
            elif has_problems.lower() == 'false':
                queryset = queryset.filter(problems="[]") | queryset.filter(problems=[])
            
        location = self.request.query_params.get('location')
        if location:
            queryset = queryset.filter(land_data__icontains=location)
            
        cadastral_number = self.request.query_params.get('cadastral_number')
        if cadastral_number:
            queryset = queryset.filter(land_data__icontains=cadastral_number)
            
        tax_number_of_pp = self.request.query_params.get('tax_number_of_pp')
        if tax_number_of_pp:
            queryset = queryset.filter(property_data__icontains=tax_number_of_pp)
            
        koatuu = self.request.query_params.get('koatuu')
        if koatuu:
            queryset = queryset.filter(land_data__icontains=koatuu)

        # Sort
        sort_by = self.request.query_params.get('sort_by')
        order = self.request.query_params.get('order', 'asc')
        if sort_by:
            prefix = '-' if order.lower() == 'desc' else ''
            if sort_by == 'count_of_problems':
                # length of problems array; relies on python if sqlite fails
                queryset = sorted(list(queryset), key=lambda x: len(x.problems) if isinstance(x.problems, list) else 0, reverse=(order.lower() == 'desc'))
            else:
                # Basic fields fallback
                pass # Sorting nested JSON in SQLite is restricted, would need custom approach
        return queryset

class RecordDetailView(generics.RetrieveAPIView):
    serializer_class = RecordSerializer
    permission_classes = (IsAuthenticated,)
    
    def get_object(self):
        report_id = self.kwargs.get('report_id')
        record_id = self.kwargs.get('record_id')
        return generics.get_object_or_404(Record, report_id=report_id, id=record_id)

class ExportStubView(views.APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        report_ids = request.data.get('report_ids', [])
        record_ids = request.data.get('record_ids', [])
        
        response = HttpResponse(b"%PDF-1.4\n%Stub PDF Export\n", content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="export.pdf"'
        return response
