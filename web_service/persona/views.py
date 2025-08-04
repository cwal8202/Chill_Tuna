from django.shortcuts import render

# Create your views here.
def create_persona(request) :
    if request.method == 'POST' :
        
        return None
    context = {
        "age_options": ["20대", "30대", "40대", "50대", "60대 이상"],
        "gender_options": ["남", "여"],
        "family_options": ["1인 가구", "부모동거", "부부", "자녀1명", "자녀2명 이상", "기타"],
        "taste_options": ["통조림/즉석/면류", "생수/음료/커피", "과자/떡/베이커리", "냉장/냉동/간편식", "유제품", "건강식품"],
        "rfm_options": ["VIP", "우수고객", "잠재우수고객", "신규고객", "잠재이탈고객", "이탈/휴면고객"],
        "lifestyle_options": ["트렌드추종", "가격민감", "브랜드선호", "건강중시"],
    }
    return render(request, "persona/create_persona.html", context)

def chat_persona(request) :
    return render(request, "persona/chat_persona.html")