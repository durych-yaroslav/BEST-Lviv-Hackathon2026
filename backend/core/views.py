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

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = UserRegistrationSerializer

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 1000

class ReportCreateView(views.APIView):
    permission_classes = (IsAuthenticated,)
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        land_file = request.FILES.get('land_file')
        property_file = request.FILES.get('property_file')

        if not land_file or not property_file:
            return Response(
                {"error": "Both 'land_file' and 'property_file' are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create the report
        report = Report.objects.create()

        # Process the files (stubbed logic)
        records_data = process_excel_files(land_file, property_file)

        # Create Records for the Report
        records_to_create = [
            Record(
                report=report,
                problems=data.get('problems', {}),
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
    filter_backends = [filters.OrderingFilter, filters.SearchFilter]
    ordering_fields = ['id']
    search_fields = ['problems', 'land_data', 'property_data']

    def get_queryset(self):
        report_id = self.kwargs.get('report_id')
        queryset = Record.objects.filter(report_id=report_id)

        # Filtering logic via query parameters
        problem = self.request.query_params.get('problem')
        if problem:
            # Simple fallback SQLite json check (using icontains string representation)
            queryset = queryset.filter(problems__icontains=problem)
            
        location = self.request.query_params.get('location')
        if location:
            queryset = queryset.filter(land_data__icontains=location)

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

    def get(self, request, *args, **kwargs):
        return HttpResponse("GET: PDF Export Stub. (Download PDF)")

    def post(self, request, *args, **kwargs):
        # A POST endpoint variant as requested
        return HttpResponse("POST: PDF Export Stub. (Generate PDF from provided params)")
