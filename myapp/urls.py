from django.urls import path
from .views import *
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('test/', test_view),
    path('tasks/', get_tasks),
    path('tasks/create/', create_task),
    path('tasks/update/<int:pk>/', update_task),
    path('tasks/delete/<int:pk>/', delete_task),
    path('register/', RegisterView.as_view(), name='register'),
    path('upload-picture/', upload_profile_picture, name='upload-profile-picture'),
    path('profile/', get_user_profile, name='get_user_profile'),
]