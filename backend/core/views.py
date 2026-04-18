from rest_framework import generics, status, views
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.exceptions import PermissionDenied
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.db.models import Func, IntegerField
from django.db.models.expressions import RawSQL

from .models import Report, Record
from .serializers import UserRegistrationSerializer, RecordSerializer
from .services import process_excel_files
from .pagination import StandardResultsSetPagination

from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken


class JSONArrayLength(Func):
    """SQLite / PostgreSQL compatible JSON array length."""
    function = 'JSON_ARRAY_LENGTH'
    output_field = IntegerField()


# ────────────────────────────── Auth ──────────────────────────────

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = 'email'

    def validate(self, attrs):
        email = attrs.get('email', '')
        password = attrs.get('password', '')

        # Registration stores email as username, so authenticate by username
        self.user = authenticate(
            request=self.context.get('request'),
            username=email,
            password=password,
        )
        if self.user is None or not self.user.is_active:
            raise self.fail('no_active_account')

        refresh = self.get_token(self.user)
        return {
            "access_token": str(refresh.access_token),
            "token_type": "Bearer",
        }


class CustomTokenLoginView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = UserRegistrationSerializer



# ────────────────────────── Reports ───────────────────────────────

class ReportCreateView(views.APIView):
    permission_classes = (IsAuthenticated,)
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        land_file = request.FILES.get('land')
        property_file = request.FILES.get('property')

        if not land_file or not property_file:
            return Response(
                {"error": "Both 'land' and 'property' files are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        report = Report.objects.create(user=request.user)
        try:
            records_data = process_excel_files(land_file, property_file)
        except Exception as e:
            report.delete() # Cleanup
            return Response(
                {"error": f"Invalid Excel file content: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        records_to_create = [

            Record(
                report=report,
                problems=data.get('problems', []),
                land_data=data.get('land_data', {}),
                property_data=data.get('property_data', {}),
            )
            for data in records_data
        ]
        Record.objects.bulk_create(records_to_create)

        return Response({"report_id": str(report.id)}, status=status.HTTP_201_CREATED)


# ────────────────────────── Records ───────────────────────────────

def _check_report_ownership(report_id, user):
    """Return a Report or raise 404 / 403."""
    report = generics.get_object_or_404(Report, id=report_id)
    if report.user is not None and report.user != user:
        raise PermissionDenied("You do not have access to this report.")
    return report


class RecordListView(generics.ListAPIView):
    serializer_class = RecordSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        report_id = self.kwargs.get('report_id')
        report = _check_report_ownership(report_id, self.request.user)
        queryset = Record.objects.filter(report=report)

        # ── Filters ──
        problem = self.request.query_params.get('problem')
        if problem:
            # Quote the value so "land_user" doesn't match "edrpou_of_land_user"
            queryset = queryset.filter(problems__icontains=f'"{problem}"')

        has_problems = self.request.query_params.get('has_problems')
        if has_problems:
            if has_problems.lower() == 'true':
                queryset = queryset.exclude(problems=[])
            elif has_problems.lower() == 'false':
                queryset = queryset.filter(problems=[])

        location = self.request.query_params.get('location')
        if location:
            queryset = queryset.annotate(
                _location=RawSQL("JSON_EXTRACT(land_data, '$.location')", []),
            ).filter(_location__icontains=location)

        cadastral_number = self.request.query_params.get('cadastral_number')
        if cadastral_number:
            queryset = queryset.annotate(
                _cadastral=RawSQL("JSON_EXTRACT(land_data, '$.cadastral_number')", []),
            ).filter(_cadastral__icontains=cadastral_number)

        tax_number_of_pp = self.request.query_params.get('tax_number_of_pp')
        if tax_number_of_pp:
            queryset = queryset.annotate(
                _tax=RawSQL("JSON_EXTRACT(property_data, '$.tax_number_of_pp')", []),
            ).filter(_tax__icontains=tax_number_of_pp)

        koatuu = self.request.query_params.get('koatuu')
        if koatuu:
            queryset = queryset.annotate(
                _koatuu=RawSQL("JSON_EXTRACT(land_data, '$.koatuu')", []),
            ).filter(_koatuu__icontains=koatuu)

        # ── Sorting ──
        sort_by = self.request.query_params.get('sort_by')
        order = self.request.query_params.get('order', 'asc')
        if sort_by:
            prefix = '-' if order.lower() == 'desc' else ''
            if sort_by in ('count_of_problems', 'problems'):
                queryset = queryset.annotate(
                    problem_count=JSONArrayLength('problems'),
                ).order_by(f'{prefix}problem_count')
            else:
                json_path = f'$.{sort_by}'
                queryset = queryset.annotate(
                    sort_key=RawSQL("JSON_EXTRACT(land_data, %s)", [json_path]),
                ).order_by(f'{prefix}sort_key')

        return queryset


class RecordDetailView(generics.RetrieveAPIView):
    serializer_class = RecordSerializer
    permission_classes = (IsAuthenticated,)

    def get_object(self):
        report_id = self.kwargs.get('report_id')
        record_id = self.kwargs.get('record_id')
        report = _check_report_ownership(report_id, self.request.user)
        return generics.get_object_or_404(Record, report=report, id=record_id)


# ────────────────────────── Export ────────────────────────────────

class ExportStubView(views.APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        report_ids = request.data.get('report_ids', [])
        record_ids = request.data.get('record_ids', [])

        response = HttpResponse(
            b"%PDF-1.4\n%Stub PDF Export\n",
            content_type='application/pdf',
        )
        response['Content-Disposition'] = 'attachment; filename="export.pdf"'
        return response
