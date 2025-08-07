from django.urls import path
from . import views

app_name = "chat"
urlpatterns = [
    path("chat/<int:persona_id>/<int:thread_id>/", views.chat_start, name="chat_start"),
]