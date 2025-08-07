from django.urls import path
from . import views

app_name = "persona"
urlpatterns = [
    path('', views.create_persona, name='create'),  # /persona/
]