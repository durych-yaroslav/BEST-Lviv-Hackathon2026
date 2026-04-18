import uuid
from django.db import models

class Report(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    def __str__(self):
        return str(self.id)

class Record(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name='records')
    problems = models.JSONField(default=dict)
    land_data = models.JSONField(default=dict)
    property_data = models.JSONField(default=dict)

    def __str__(self):
        return f"Record {self.id} for Report {self.report.id}"
