from django.contrib.auth.models import User
from rest_framework import serializers
from .models import Report, Record

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password')

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password']
        )
        return user


class RecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = Record
        fields = ['id', 'report', 'problems', 'land_data', 'property_data']


class ReportSerializer(serializers.ModelSerializer):
    # Includes nested representation of records within the report payload if needed
    records = RecordSerializer(many=True, read_only=True)

    class Meta:
        model = Report
        fields = ['id', 'records']
