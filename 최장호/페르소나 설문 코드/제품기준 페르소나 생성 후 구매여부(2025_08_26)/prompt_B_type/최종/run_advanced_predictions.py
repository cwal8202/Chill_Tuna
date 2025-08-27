#!/usr/bin/env python
# coding: utf-8

# # 최종 개선 프롬프트 LLM API 실행 노트북
# 
# 이 노트북은 `advanced_prompts_for_llm.jsonl` 파일을 읽어, 각 프롬프트를 LLM API(OpenAI GPT)에 전송하고, 그 예측 결과를 `advanced_llm_results.jsonl` 파일에 저장합니다.

# ## 1. 사전 준비: 라이브러리 설치 및 API 키 설정
# 
# 코드를 실행하기 전에 먼저 필요한 라이브러리를 설치하고 API 키를 설정해야 합니다.

# In[1]:


# 1. 라이브러리 설치 (최초 1회만 실행)
# %pip install openai tqdm
# %pip install ipywidgets


# **2. API 키 설정 (가장 중요)**
# 
# API 키는 코드에 직접 적는 것보다 **환경 변수**로 설정하는 것이 안전합니다. 아래 코드 셀을 실행하기 전에, 이 노트북을 실행하는 터미널이나 시스템에 환경 변수를 설정해주세요.
# 
# - **(Windows)** `set OPENAI_API_KEY="sk-..."`
# - **(Mac/Linux)** `export OPENAI_API_KEY="sk-..."`
# 
# 만약 환경 변수 설정이 어렵다면, **임시로** 아래 코드 셀의 `os.getenv("OPENAI_API_KEY")` 부분을 자신의 API 키 문자열로 대체할 수 있으나, 코드 공유 시 키가 노출될 수 있어 권장하지 않습니다.

# ## 2. 설정 및 함수 정의

# In[2]:

from dotenv import load_dotenv
load_dotenv()

import os
import json
import time
from openai import OpenAI
from tqdm import tqdm

# --- 설정 ---
INPUT_PROMPTS_FILE = 'advanced_prompts_for_llm.jsonl'
OUTPUT_RESULTS_FILE = 'advanced_llm_results.jsonl'
OPENAI_MODEL = "gpt-4o-mini"
SLEEP_TIME_BETWEEN_REQUESTS = 1
### [추가] 테스트할 프롬프트 개수를 10개로 제한합니다. ###
# LIMIT_PROMPTS = 10
#######################################################


# --- OpenAI API 클라이언트 설정 ---
def get_openai_client():
    """OpenAI 클라이언트를 초기화하고 반환합니다."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY 환경 변수가 설정되지 않았습니다. 위 설명을 참고하여 설정해주세요.")
    return OpenAI(api_key=api_key)

# --- 메인 API 호출 함수 ---
def get_llm_prediction(client, system_prompt, user_prompt):
    """System, User 역할을 분리하여 API에 프롬프트를 보내고 응답을 받습니다."""
    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.2
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"API 호출 중 오류 발생: {e}")
        return None

print("설정 및 함수 정의 완료.")


# ## 3. 프롬프트 실행 및 결과 저장
# 
# 아래 셀을 실행하면 `advanced_prompts_for_llm.jsonl` 파일에 있는 모든 프롬프트에 대해 LLM 예측을 수행하고, 결과를 `advanced_llm_results.jsonl`에 저장합니다. 중간에 멈춰도 이어서 실행할 수 있습니다.

# In[ ]:


# [수정] 이 코드 블록 전체를 복사하여 노트북의 마지막 코드 셀에 붙여넣으세요.

try:
    client = get_openai_client()

    with open(INPUT_PROMPTS_FILE, 'r', encoding='utf-8') as f:
        prompts = [json.loads(line) for line in f]
    print(f"총 {len(prompts)}개의 개선된 프롬프트를 불러왔습니다.")

    # [추가] LIMIT_PROMPTS 변수에 값이 설정된 경우, 프롬프트 리스트를 해당 개수만큼 자릅니다.
    # if 'LIMIT_PROMPTS' in locals() and LIMIT_PROMPTS is not None:
    #     prompts = prompts[:LIMIT_PROMPTS]
    #     print(f"\n[테스트 모드] 프롬프트 개수를 {len(prompts)}개로 제한합니다.\n")
        ################################################################################

    processed_keys = set()
    try:
        with open(OUTPUT_RESULTS_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                data = json.loads(line)
                processed_keys.add((data['product_name'], data['persona_key']))
        print(f"'{OUTPUT_RESULTS_FILE}'에서 이미 처리된 {len(processed_keys)}개의 결과를 발견했습니다. 이어서 실행합니다.")
    except FileNotFoundError:
        print("결과 파일을 새로 시작합니다.")

    with open(OUTPUT_RESULTS_FILE, 'a', encoding='utf-8') as f_out:
        for prompt_data in tqdm(prompts, desc="LLM 예측 실행 중"):

            product_name = prompt_data.get('product_name')
            persona_key = prompt_data.get('persona_key')

            if (product_name, persona_key) in processed_keys:
                continue

            system_prompt = prompt_data.get('system_prompt')
            user_prompt = prompt_data.get('user_prompt')

            llm_response_str = get_llm_prediction(client, system_prompt, user_prompt)

            if llm_response_str:
                # [수정] LLM 응답을 파싱하는 부분을 더 유연하게 변경하여 오류를 해결합니다.
                try:
                    # LLM의 응답에 '---' 구분선이 있는지 먼저 확인합니다.
                    if '---' in llm_response_str:
                        # 구분선이 있는 경우: '사고 과정'과 'JSON'으로 분리합니다.
                        reasoning_part, json_part = llm_response_str.split('---', 1)
                        json_match = json_part[json_part.find('{'):json_part.rfind('}')+1]
                        llm_json_result = json.loads(json_match)
                        reasoning = reasoning_part.strip()
                    else:
                        # 구분선이 없는 경우: 전체 응답을 'JSON'으로 간주하고, '사고 과정'은 비워둡니다.
                        llm_json_result = json.loads(llm_response_str)
                        reasoning = "N/A (LLM provided JSON output directly)"

                    # 최종 결과물 구성
                    final_result = {
                        "product_name": product_name,
                        "persona_key": persona_key,
                        "llm_reasoning": reasoning,
                        "prediction": llm_json_result 
                    }

                    f_out.write(json.dumps(final_result, ensure_ascii=False) + '\n')

                except (json.JSONDecodeError, ValueError) as e:
                    print(f"\n오류: LLM의 응답을 파싱하는 데 실패했습니다. 응답: {llm_response_str}\n 에러: {e}")

            time.sleep(SLEEP_TIME_BETWEEN_REQUESTS)

    print("="*40)
    print(f"🎉 모든 작업이 완료되었습니다. 결과가 '{OUTPUT_RESULTS_FILE}' 파일에 저장되었습니다.")

except Exception as e:
    print(f"실행 중 오류가 발생했습니다: {e}")


# In[ ]:





# In[ ]:




