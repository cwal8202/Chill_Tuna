from django.shortcuts import render, redirect
from django.contrib import messages
from .models import ChatThread, ChatMessage, Persona
from django.http import HttpResponse

# Create your views here.

#-------- Chat 새로운 흐름 ---------#
# 1. 페르소나 ID 로 페르소나 조회
# 2. "chat-system-msg" 출력
# 3. 사용자가 채팅을 치면 값 llm에 전달.
# 4. llm에서 output으로 나오면 chatthread에 저장
# 5. 화면에 output 값 전달
# 6. 만약 화면 꺼지거나, session 종료되거나, 사용자가 끄면 chatthread에 저장

#-------- Chat 기존 전체 흐름 ---------#
# 1. 채팅 목록, 페르소나 확인 
#   1) thread_id 로 chatthread 조회. 없으면 에러
#   2) chatthread에서 persona_id 로 persona 조회 후 정보 전달
# 2. 채팅 유/무 확인
#   1). 채팅 없으면 "chat-system-msg" 보여줌
#   1-1). 채팅 있으면 채팅 불러오기
# 3. 사용자가 채팅을 치면 값 llm에 전달.
# 4. llm에서 output으로 나온 값을 화면에 전달.
# 5. 만약 화면 꺼지거나, session 종료되거나, 사용자가 끄면 chatthread에 저장

# 함수명 : chat_start
# input : request, thread_id
# output : chat_persona.html 화면 + context
# 작성자 : 최장호
# 작성 날짜 : 2025-08-07
# 함수 설명 : chat 화면 로드
#               1. thread_id로 thread확인. 채팅 내용 조회
#               2. persona 조회
#               3. 화면전달 : persona, chat_message
persona_id = 1
thread_id = 1
def chat_start(request, persona_id, thread_id):
    # 1. thread_id 유/무 확인 후 있으면 chatthread 조회, 채팅 내용 조회
    chatthread = None
    chat_messages = []

    if thread_id and thread_id > 0:
        try:
            chatthread = ChatThread.objects.get(id=thread_id)
        except ChatThread.DoesNotExist:
            messages.error(request, f"{thread_id}번 채팅 스레드를 찾을 수 없습니다.")
            return redirect("home")
        
        if chatthread.persona_id.id != persona_id:
            messages.error(request, "thread_id와 persona_id가 일치하지 않습니다.")
            return redirect("home")
        # chatmessage 모델 확인 결과 thread 객체 자체를 넣음.
        chat_messages = ChatMessage.objects.filter(thread=chatthread).order_by("timestamp")    

    # 2. persona_id 로 persona 조회
    try:
        persona = Persona.objects.get(id=persona_id)
    except Persona.DoesNotExist:
        messages.error(request, f"{persona_id}번 페르소나를 찾을 수 없습니다.")
        return redirect("home")
    
    # 3. 화면에 정보전달 : persona, chat_message
    context = {
        "persona": persona,
        "chat_messages": chat_messages,
    }
    return render(request, "chat/chat_persona.html", context)