from django.urls import path
from . import views

app_name = 'api'

urlpatterns = [
    path('chat/send/', views.chat_message_api, name='chat_message_api'),
]