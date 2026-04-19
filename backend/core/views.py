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
            report.delete()
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

        problem = self.request.query_params.get('problem')
        if problem:
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


# ────────────────────────── PDF helpers ───────────────────────────

PROBLEM_LABELS_UA = {
    'edrpou_of_land_user':                     'ЄДРПОУ землекористувача',
    'land_user':                                'Землекористувач',
    'location':                                 'Місцезнаходження',
    'area':                                     'Площа',
    'date_of_state_registration_of_ownership':  'Дата реєстрації права',
    'share_of_ownership':                       'Частка власності',
    'purpose':                                  'Цільове призначення',
}


def _build_pdf_context(report, records_qs):
    """
    Aggregate stats and build the full template context for the PDF.
    All per-record booleans are pre-computed here so the template
    needs zero custom template tags.
    """
    records = list(records_qs)
    total_records = len(records)
    total_with_problems = sum(1 for r in records if r.problems)
    total_clean = total_records - total_with_problems
    problem_rate = round(total_with_problems / total_records * 100, 1) if total_records else 0

    # ── Problem frequency table ──────────────────────────────────
    freq: dict = {}
    for rec in records:
        for p in (rec.problems or []):
            freq[p] = freq.get(p, 0) + 1

    max_count = max(freq.values(), default=1)
    problem_counts = []
    for key, count in sorted(freq.items(), key=lambda x: x[1], reverse=True):
        pct = round(count / total_records * 100, 1) if total_records else 0
        problem_counts.append({
            'key':       key,
            'label':     PROBLEM_LABELS_UA.get(key, key),
            'count':     count,
            'pct':       pct,
            'bar_width': round(count / max_count * 100),
        })

    # ── Top-10 most critical records ─────────────────────────────
    top_10_records = sorted(records, key=lambda r: len(r.problems or []), reverse=True)[:10]

    top_10 = []
    for rec in top_10_records:
        problems = rec.problems or []
        top_10.append({
            'record':            rec,
            'problem_count':     len(problems),
            # Human-readable labels for the pills row
            'problem_labels_list': [PROBLEM_LABELS_UA.get(p, p) for p in problems],
            # Pre-computed booleans — one per comparison row in the template
            'has_land_user':  'land_user' in problems,
            'has_edrpou':     'edrpou_of_land_user' in problems,
            'has_location':   'location' in problems,
            'has_area':       'area' in problems,
            'has_purpose':    'purpose' in problems,
            'has_date':       'date_of_state_registration_of_ownership' in problems,
            'has_share':      'share_of_ownership' in problems,
        })

    return {
        'report':              report,
        'total_records':       total_records,
        'total_with_problems': total_with_problems,
        'total_clean':         total_clean,
        'problem_rate':        problem_rate,
        'problem_counts':      problem_counts,
        'top_10':              top_10,
        'date':                timezone.now(),
        'font_path':           FONT_PATH,
    }


def _render_pdf(template_path: str, context: dict):
    """Render an HTML template to PDF bytes via xhtml2pdf."""
    try:
        register_fonts()
    except Exception:
        pass

    template = get_template(template_path)
    html = template.render(context)
    result = io.BytesIO()

    def link_callback(uri, _rel):
        if uri == FONT_PATH:
            return FONT_PATH
        return uri

    pdf_status = pisa.pisaDocument(
        io.BytesIO(html.encode('UTF-8')),
        result,
        encoding='UTF-8',
        link_callback=link_callback,
    )
    return result.getvalue(), pdf_status.err


# ────────────────────────── Export ────────────────────────────────

class ReportExportView(views.APIView):
    """POST /api/reports/export/  — bulk export (uses first report_id)."""
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        report_id = self.kwargs.get('report_id')
        record_ids = request.data.get('record_ids', [])

        if not report_id:
            report_ids = request.data.get('report_ids', [])
            if not report_ids:
                return Response({"error": "No report_id or report_ids provided."}, status=400)
            report_id = report_ids[0]

        report = get_object_or_404(Report, id=report_id)
        if report.user and report.user != request.user:
            return Response({"error": "Forbidden"}, status=403)

        records_qs = (
            Record.objects.filter(report=report, id__in=record_ids)
            if record_ids
            else Record.objects.filter(report=report)
        )

        context = _build_pdf_context(report, records_qs)
        pdf_bytes, err = _render_pdf('report_template.html', context)

        if err:
            return Response({"error": "PDF generation failed."}, status=500)

        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="audit_report_{str(report.id)[:8]}.pdf"'
        return response


class ReportPDFExportView(views.APIView):
    """
    GET  /api/reports/{report_id}/export/          — export all records
    POST /api/reports/{report_id}/export/          — export selected records
         body: { "record_ids": ["uuid", ...] }
    """
    permission_classes = (IsAuthenticated,)

    def get(self, request, report_id, *args, **kwargs):
        return self._export(request, report_id, record_ids=None)

    def post(self, request, report_id, *args, **kwargs):
        return self._export(request, report_id, record_ids=request.data.get('record_ids'))

    def _export(self, request, report_id, record_ids):
        report = get_object_or_404(Report, id=report_id)

        if report.user and report.user != request.user:
            return Response({"error": "Forbidden: You do not own this report."}, status=403)

        records_qs = (
            Record.objects.filter(report=report, id__in=record_ids)
            if record_ids
            else report.records.all()
        )

        context = _build_pdf_context(report, records_qs)
        pdf_bytes, err = _render_pdf('report_template.html', context)

        if err:
            return Response({"error": "PDF generation failed."}, status=500)

        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="analytical_report_{str(report.id)[:8]}.pdf"'
        return response


# ────────────────────────── AI Analysis ───────────────────────────

class AIAnalysisView(views.APIView):
    """POST /api/reports/ai-analysis"""
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        report_id = request.data.get('report_id')
        record_ids = request.data.get('record_ids', [])
        question = request.data.get('question', '')

        if not report_id:
            return Response({"error": "report_id is required."}, status=status.HTTP_400_BAD_REQUEST)
        if not question:
            return Response({"error": "question is required."}, status=status.HTTP_400_BAD_REQUEST)

        report = _check_report_ownership(report_id, request.user)
        records = Record.objects.filter(report=report)

        if not records.exists():
            return Response({"error": "No records found for the given report."}, status=status.HTTP_404_NOT_FOUND)

        requested_fields = record_ids

        records_context = []
        for rec in records:
            entry = {"record_id": str(rec.id)}
            if requested_fields:
                filtered_land = {k: v for k, v in (rec.land_data or {}).items() if k in requested_fields}
                filtered_property = {k: v for k, v in (rec.property_data or {}).items() if k in requested_fields}
                if filtered_land:
                    entry["land_data"] = filtered_land
                if filtered_property:
                    entry["property_data"] = filtered_property
                if "problems" in requested_fields:
                    entry["problems"] = rec.problems
            else:
                entry["problems"] = rec.problems
                entry["land_data"] = rec.land_data
                entry["property_data"] = rec.property_data
            records_context.append(entry)

        import json as _json
        context_str = _json.dumps(records_context, ensure_ascii=False, default=str)
        user_message = f"Here are the records from the report:\n\n{context_str}\n\nQuestion: {question}"

        from django.conf import settings as django_settings
        api_key = django_settings.OPENAI_API_KEY
        model = django_settings.OPENAI_MODEL

        if not api_key:
            return Response(
                {"error": "OpenAI API key is not configured."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            ai_response = client.responses.create(model=model, input=user_message)
            answer = ai_response.output_text
        except Exception as e:
            return Response({"error": f"AI analysis failed: {str(e)}"}, status=status.HTTP_502_BAD_GATEWAY)

        return Response({"answer": answer}, status=status.HTTP_200_OK)
