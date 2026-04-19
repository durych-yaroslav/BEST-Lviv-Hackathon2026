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
from .pdf_service import PDFGenerator, FONT_PATH, register_fonts
from .pagination import StandardResultsSetPagination

import io
from django.template.loader import get_template
from django.utils import timezone
from django.shortcuts import get_object_or_404
from xhtml2pdf import pisa

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
            "username": self.user.first_name or self.user.username,
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

class ReportExportView(views.APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        # Simply call the post logic for GET requests too
        return self.post(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        report_id = self.kwargs.get('report_id')
        record_ids = request.data.get('record_ids', [])
        
        # If no report_id in URL, check if it's a bulk export from body
        if not report_id:
            report_ids = request.data.get('report_ids', [])
            if not report_ids:
                return Response({"error": "No report_id or report_ids provided."}, status=400)
            report_id = report_ids[0] # Just take first for current version

        report = generics.get_object_or_404(Report, id=report_id)
        
        # Permission check
        if report.user and report.user != request.user:
            return Response({"error": "Forbidden"}, status=403)

        if record_ids:
            records = Record.objects.filter(report=report, id__in=record_ids)
        else:
            # Export all records for this report (limit to 500 for safety)
            records = Record.objects.filter(report=report)[:500]

        generator = PDFGenerator()
        try:
            pdf_content = generator.generate_report_pdf(report, records)
        except Exception as e:
            return Response({"error": f"PDF Generation failed: {str(e)}"}, status=500)

        response = HttpResponse(pdf_content, content_type='application/pdf')
        filename = f"report_{str(report.id)[:8]}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response


class ReportPDFExportView(views.APIView):
    """
    Analytical PDF Report generation using xhtml2pdf.
    GET /api/reports/{report_id}/export/
    """
    permission_classes = (IsAuthenticated,)

    def get(self, request, report_id, *args, **kwargs):
        # 1. Fetch data
        report = get_object_or_404(Report, id=report_id)
        
        # Permission check
        if report.user and report.user != request.user:
            return Response({"error": "Forbidden: You do not own this report."}, status=403)

        records = report.records.all()
        total_records = records.count()
        total_with_problems = records.exclude(problems=[]).count()

        # 2. Statistics (Aggregation)
        problem_counts = {}
        for record in records:
            for p in record.problems:
                problem_counts[p] = problem_counts.get(p, 0) + 1
        
        # Sort problem_counts by frequency descending
        sorted_problems = sorted(problem_counts.items(), key=lambda x: x[1], reverse=True)

        # 3. Top 10 Critical
        # Identify top 10 most critical records (by number of problems)
        top_10 = sorted(records, key=lambda r: len(r.problems), reverse=True)[:10]

        # Ensure font is available for Cyrillic
        try:
            register_fonts()
        except:
            pass

        # 4. Render Context
        context = {
            'report': report,
            'total_records': total_records,
            'total_with_problems': total_with_problems,
            'problem_counts': sorted_problems,
            'top_10': top_10,
            'date': timezone.now(),
            'font_path': FONT_PATH, # Passed to @font-face in CSS
        }

        # 5. Generate PDF
        template_path = 'report_template.html'
        template = get_template(template_path)
        html = template.render(context)
        
        result = io.BytesIO()

        def link_callback(uri, rel):
            """
            Convert HTML URIs to absolute system paths so xhtml2pdf can access those
            resources on disk.
            """
            import os
            from django.conf import settings
            
            # If it's the font path we passed in context
            if uri == FONT_PATH:
                return FONT_PATH
                
            # Fallback for static/media if needed
            return uri

        pdf = pisa.pisaDocument(
            io.BytesIO(html.encode("UTF-8")), 
            result, 
            encoding='UTF-8',
            link_callback=link_callback
        )
        
        if not pdf.err:
            response = HttpResponse(result.getvalue(), content_type='application/pdf')
            filename = f"analytical_report_{str(report.id)[:8]}.pdf"
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
        
        return Response({"error": "Failed to generate PDF report."}, status=500)


# ────────────────────────── AI Analysis ───────────────────────────

class AIAnalysisView(views.APIView):
    """
    POST /api/reports/ai-analysis

    Accepts a report_id, a list of record_ids, and a natural-language question.
    Fetches the requested records, sends them as context to GPT-4.1 Mini,
    and returns the AI-generated answer.
    """
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        report_id = request.data.get('report_id')
        record_ids = request.data.get('record_ids', [])
        question = request.data.get('question', '')

        # ── Validation ──
        if not report_id:
            return Response(
                {"error": "report_id is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not question:
            return Response(
                {"error": "question is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ── Fetch records ──
        report = _check_report_ownership(report_id, request.user)
        if record_ids:
            records = Record.objects.filter(report=report, id__in=record_ids)
        else:
            # If no specific record_ids given, use all records from the report
            records = Record.objects.filter(report=report)

        if not records.exists():
            return Response(
                {"error": "No records found for the given report and record IDs."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # ── Build context for the AI ──
        records_context = []
        for rec in records:
            records_context.append({
                "record_id": str(rec.id),
                "problems": rec.problems,
                "land_data": rec.land_data,
                "property_data": rec.property_data,
            })

        import json as _json
        context_str = _json.dumps(records_context, ensure_ascii=False, default=str)

        user_message = (
            f"Here are the records from the report:\n\n"
            f"{context_str}\n\n"
            f"Question: {question}"
        )

        # ── Call OpenAI ──
        from django.conf import settings as django_settings
        api_key = django_settings.OPENAI_API_KEY
        model = django_settings.OPENAI_MODEL

        if not api_key:
            return Response(
                {"error": "OpenAI API key is not configured. Set the OPENAI_API_KEY environment variable."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            response = client.responses.create(
                model=model,
                input=user_message,
            )
            answer = response.output_text
        except Exception as e:
            return Response(
                {"error": f"AI analysis failed: {str(e)}"},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        return Response({"answer": answer}, status=status.HTTP_200_OK)

