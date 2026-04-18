from django.contrib.auth.models import User
from rest_framework import serializers
from .models import Report, Record

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    name = serializers.CharField(source='first_name', required=False)

    class Meta:
        model = User
        fields = ('id', 'email', 'name', 'password')
        extra_kwargs = {'email': {'required': True}}

    def create(self, validated_data):
        email = validated_data.get('email', '')
        user = User.objects.create_user(
            username=email, # Django requires username, use email
            email=email,
            first_name=validated_data.get('first_name', ''),
            password=validated_data['password']
        )
        return user



class RecordSerializer(serializers.ModelSerializer):
    record_id = serializers.UUIDField(source='id', read_only=True)
    report_id = serializers.UUIDField(source='report.id', read_only=True)

    class Meta:
        model = Record
        fields = ['report_id', 'record_id', 'problems', 'land_data', 'property_data']


class ReportSerializer(serializers.ModelSerializer):
    # Includes nested representation of records within the report payload if needed
    records = RecordSerializer(many=True, read_only=True)

    class Meta:
        model = Report
        fields = ['id', 'records']
