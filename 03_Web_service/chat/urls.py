from django.urls import path
from . import views

app_name = "chat"
urlpatterns = [
    path("start/<int:persona_id>/<int:thread_id>/", views.chat_start, name="chat_start"),
    path("send_message/", views.send_message, name="send_message"),
]