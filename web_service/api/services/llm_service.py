
# 함수명 : get_llm_response
# input : persona_id, user_input, model_name
# output : 
# 작성자 : 최장호
# 작성 날짜 : 2025-08-10
# 함수 설명 : 페르소나, 사용자 입력을 LLM API에 전달하고 응답을 반환합니다.
#               1. persona_id로 persona 정보 가져오기
#               2. 사용자 입력과 persona 정보를 입력해서 LLM API에 전달
#               3. LLM API에 전달하여 응답 받아오기
#               4. 응답 반환
def get_llm_response(persona_id, user_input, model_name):
    """
    사용자 입력과 페르소나 정보를 받아 LLM API에 전달하고 응답을 반환합니다.
    API 통신 실패 시 예외(Exception)를 발생시킬 수 있습니다.
    """
    # prompt = f"당신은 {persona_info}입니다. 다음 질문에 답하세요: {user_input}"
    # response = openai.Completion.create(...)
    # llm_output = response.choices[0].text.strip()
    
    # 임시 테스트 응답
    print(f"LLM에 '{user_input}' 전송... (가상)")
    llm_output = "이것은 llm_service에서 처리된 답변입니다."
    
    # 만약 LLM API 호출이 실패하면 여기서 에러가 발생한다고 가정
    # if error: raise Exception("LLM API 호출 실패")

    return llm_output