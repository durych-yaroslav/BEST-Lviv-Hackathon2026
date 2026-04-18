import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")
django.setup()

from django.core.management import call_command
call_command("migrate")

from core.models import Report, Record
from core.views import JSONArrayLength

report = Report.objects.create()
Record.objects.create(report=report, problems=['area', 'location'])
Record.objects.create(report=report, problems=['area'])
Record.objects.create(report=report, problems=[])

try:
    qs = Record.objects.filter(report=report).annotate(pc=JSONArrayLength('problems')).order_by('-pc')
    print([(r.id, r.problems, getattr(r, 'pc', None)) for r in qs])
    print("SUCCESS")
except Exception as e:
    print(f"FAILED: {e}")
