from django.urls import path
from .views import *

urlpatterns = [
    path('test/', test_view),
    path('tasks/', get_tasks),
    path('tasks/create/', create_task),
    path('tasks/update/<int:pk>/', update_task),
    path('tasks/delete/<int:pk>/', delete_task),
    path('register/', RegisterView.as_view(), name='register'),
]