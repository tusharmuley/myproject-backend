# === views.py ===

from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.serializers import ModelSerializer
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.conf import settings
import os
from django.db.models import Q

from django.core.files.storage import default_storage

from rest_framework.parsers import MultiPartParser, FormParser

from .models import Task, Profile
from .serializers import TaskSerializer

# Register Serializer & View
class RegisterSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'password']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer



# for upload profile pichture 
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def upload_profile_picture(request):
    print("📦 Storage being used:", type(request.user))

    if 'profile_picture' not in request.FILES:
        return Response({'error': 'No file uploaded'}, status=400)

    profile_picture = request.FILES['profile_picture']

    if profile_picture.size > settings.MAX_FILE_SIZE_MB * 1024 * 1024:
        return Response({'error': 'File too large (max 1MB allowed)'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        profile = Profile.objects.get(user=request.user)
        if profile.profile_picture:
            # ✅ Correct way to delete on any storage backend (S3 or local)
            profile.profile_picture.delete(save=False)
    except Profile.DoesNotExist:
        profile = Profile.objects.create(user=request.user)

    profile.profile_picture = profile_picture
    profile.save()

    return Response({'message': 'Profile picture uploaded successfully'})



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_profile(request):
    user = request.user
    try:
        profile = Profile.objects.get(user=user)
        # if profile.profile_picture:
        #     profile_picture_url = profile.profile_picture.url  # ✅ REAL S3 URL
        # else:
        #     profile_picture_url = None
        if profile.profile_picture:
            filename = profile.profile_picture.name  # 'profile_pics/filename.jpg'

            # Agar production hai toh S3 url
            if settings.ENVIRONMENT == 'production':
                profile_picture_url = f'https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com/{filename}'
            else:
                # Local me absolute uri with domain
                profile_picture_url = request.build_absolute_uri(settings.MEDIA_URL + filename)
        else:
            profile_picture_url = None
            
    except Profile.DoesNotExist:
        profile_picture_url = None

    return Response({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'profile_picture': profile_picture_url
    })



# Simple test view
def test_view(request):
    return JsonResponse({"message": "Hello from Django!"})



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_tasks(request):
    tasks = Task.objects.filter(
         Q(assigned_to=request.user) | Q(created_by=request.user)
    ).order_by('-created_at')

    data = []
    for task in tasks:
        data.append({
            'id': task.id,
            'title': task.title,
            'description': task.description,
            'status': task.status,
            'priority': task.priority,
            'deadline': task.deadline,
            'created_at': task.created_at,
            'updated_at': task.updated_at,
            'assigned_to': {
                'id': task.assigned_to.id,
                'username': task.assigned_to.username,
                'email': task.assigned_to.email
            } if task.assigned_to else None,
            'created_by': {
                'id': task.created_by.id,
                'username': task.created_by.username,
                'email': task.created_by.email
            } if task.created_by else None
        })

    return Response(data)



# @api_view(['POST'])
# @permission_classes([IsAuthenticated])
# def create_task(request):
#     serializer = TaskSerializer(data=request.data)
#     if serializer.is_valid():
#         serializer.save(user=request.user)  # ← Now using logged in user
#         return Response(serializer.data, status=status.HTTP_201_CREATED)
#     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_task(request):
    # Extract fields from request
    title = request.data.get('title')
    description = request.data.get('description','')
    status_value = request.data.get('status', 'pending')  # Default fallback
    priority = request.data.get('priority', 'medium')     # Default fallback
    deadline = request.data.get('deadline')               # Format: "YYYY-MM-DD"
    assigned_to_id = request.data.get('assigned_to')               # Format: "YYYY-MM-DD"

    assigned_user = None
    if assigned_to_id:
        try:
            assigned_user = User.objects.get(id=assigned_to_id)
        except User.DoesNotExist:
            return Response({'error': 'Assigned user does not exist'}, status=status.HTTP_400_BAD_REQUEST)

    # Validate required field
    if not title:
        return Response({'error': 'Title is required'}, status=status.HTTP_400_BAD_REQUEST)

    # Create the task
    task = Task.objects.create(
        user=request.user,
        title=title,
        description=description,
        status=status_value,
        priority=priority,
        deadline=deadline,
        assigned_to=assigned_user,
        created_by=request.user
    )

    # Manual Response — matching your TaskSerializer
    return Response({
        "id": task.id,
        "user": {
            "id": request.user.id,
            "username": request.user.username,
            "email": request.user.email
        },
        "title": task.title,
        "description": task.description,
        "status": task.status,
        "priority": task.priority,
        "deadline": task.deadline,
        "created_at": task.created_at,
        "updated_at": task.updated_at
    }, status=status.HTTP_201_CREATED)



@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_task(request, pk):
    try:
        task = Task.objects.get(id=pk, user=request.user)
    except Task.DoesNotExist:
        return Response({'error': 'Task not found'}, status=404)
    
    serializer = TaskSerializer(task, data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_task(request, pk):
    try:
        task = Task.objects.get(id=pk, user=request.user)
    except Task.DoesNotExist:
        return Response({'error': 'Task not found'}, status=404)
    task.delete()
    return Response({"message": "Task deleted"})



@api_view(['get'])
@permission_classes([IsAuthenticated])
def getUsers(request):
    search = request.GET.get('search', '')
    users = User.objects.filter(username__istartswith=search)
    
    # Manually build list of user dicts
    user_list = [{
        'id': user.id,
        'username': user.username,
        'email': user.email
    } for user in users]
    
    return JsonResponse(user_list, safe=False)













