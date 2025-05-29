from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Task

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username']

class TaskSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Task
        # 👇 Add the new fields here
        fields = ['id', 'user', 'title','description', 'status', 'priority', 'deadline','created_by', 'assigned_to', 'created_at', 'updated_at']

