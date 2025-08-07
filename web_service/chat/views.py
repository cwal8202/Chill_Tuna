from django.shortcuts import render

# Create your views here.
def chat_persona(request) :
    return render(request, "chat/chat_persona.html")