from django.shortcuts import render, redirect
from .models import Persona
import json

# 함수명      : create_persona
# input      : request
# output     : HttpResponse (render 또는 redirect)
# 작성자      : 박동현
# 작성일자    : 2025-08-07
# 함수설명    : 
#               1. GET 요청 시, 페르소나 조건 선택 페이지를 렌더링
#               2. 해당 페이지의 버튼/폼에 필요한 선택 옵션 목록을 context를 통해 전달
#               3. POST 요청을 하면 새 페르소나를 생성하고 DB에 저장

def create_persona(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        segment = request.POST.get('segment')
        age_group = request.POST.get('age_group')
        family_structure = request.POST.get('family_structure')
        gender = request.POST.get('gender')
        customer_value = request.POST.get('customer_value')
        job = request.POST.get('job')
        persona_summary_tag = request.POST.get('persona_summary_tag')
        purchase_pattern_str = request.POST.get('purchase_pattern', '{}')
        lifestyle_str = request.POST.get('lifestyle', '{}')

        Persona.objects.create(
            name=name,
            segment=segment,
            age_group=age_group,
            family_structure=family_structure,
            gender=gender,
            customer_value=customer_value,
            job=job,
            persona_summary_tag=persona_summary_tag,
            purchase_pattern=json.loads(purchase_pattern_str),
            lifestyle=json.loads(lifestyle_str)
        )
        
        return redirect('persona:search_persona')
    
    else:
        context = {
            "age_options": ["20대", "30대", "40대", "50대", "60대 이상"],
            "gender_options": ["남", "여"],
            "family_options": ["1인 가구", "부모동거", "부부", "자녀1명", "자녀2명 이상", "기타"],
            "taste_options": ["통조림/즉석/면류", "생수/음료/커피", "과자/떡/베이커리", "냉장/냉동/간편식", "유제품", "건강식품"],
            "rfm_options": ["VIP", "우수고객", "잠재우수고객", "신규고객", "잠재이탈고객", "이탈/휴면고객"],
            "lifestyle_options": ["트렌드추종", "가격민감", "브랜드선호", "건강중시"],
        }
        return render(request, "persona/create_persona.html", context)

# 함수명      : chat_persona_view
# input       : request, persona_id
# output      : HttpResponse
# 작성자      : 박동현
# 작성일자    : 2025-08-07
# 함수설명    : 
#               1. URL로부터 특정 페르소나의 ID를 입력받아 해당 ID를 가진 Persona 객체를 데이터베이스에서 조회
#               2. 조회된 페르소나 정보를 받아 실제 채팅이 이루어지는 페이지(chat_persona.html)를 렌더링

def chat_persona_view(request, persona_id):
    persona = Persona.objects.get(id=persona_id)
    context = {
        'persona': persona,
    }
    return render(request, 'persona/chat_persona.html', context)

# 함수명      : find_and_chat_view
# input       : request
# output      : HttpResponse
# 작성자      : 박동현
# 작성일자    : 2025-08-07
# 함수설명    : 
#               1. 사용자가 조건 선택 페이지에서 선택한 조건들을 GET 파라미터로 입력받고 유사도 점수를 계산함
#               2. 가장 높은 점수를 획득한 페르소나를 '최적 페르소나'로 선정함
#               3. 선정된 최적 페르소나의 채팅 페이지로 이동해서 인터뷰를 시작

# 페르소나를 찾아 채팅으로 바로 연결하는 함수 (유사도 검색 로직 수정 필요)
def find_and_chat_view(request):
    selected_age = request.GET.get('age_group')
    selected_gender = request.GET.get('gender')
    selected_family = request.GET.get('family_structure')
    selected_rfm = request.GET.get('customer_value')
    
    selected_lifestyles = request.GET.getlist('lifestyle') 

    all_personas = Persona.objects.all()
    scores = {}

    for persona in all_personas:
        score = 0
        if selected_age and persona.age_group == selected_age:
            score += 5
        if selected_gender and persona.gender == selected_gender:
            score += 5
        if selected_family and persona.family_structure == selected_family:
            score += 3
        if selected_rfm and persona.customer_value == selected_rfm:
            score += 3

        if selected_lifestyles and isinstance(persona.lifestyle, list):
            common_lifestyles = set(selected_lifestyles) & set(persona.lifestyle)
            score += len(common_lifestyles) * 2

        scores[persona.id] = score

    if scores and sum(scores.values()) > 0:
        best_persona_id = max(scores, key=scores.get)
        best_persona = Persona.objects.get(id=best_persona_id)
        return redirect('persona:chat_persona', persona_id=best_persona.id)
    else:
        if all_personas.exists():
            return redirect('persona:chat_persona', persona_id=all_personas.first().id)
        else:
            return redirect('persona:create_persona')