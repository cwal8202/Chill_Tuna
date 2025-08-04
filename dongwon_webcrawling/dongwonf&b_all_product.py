from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import pandas as pd

# 드라이버 설정
driver = webdriver.Chrome()
url = "https://www.dongwonfnb.com/services/Product/Product_List"
driver.get(url)

# 결과 저장 리스트
results = []

# 첫 로딩 대기
WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.CSS_SELECTOR, "dl.prodMenu"))
)

page_num = 1

while True:
    print(f"📄 현재 페이지: {page_num}")
    time.sleep(2)

    # 제품 블록들 수집
    try:
        blocks = driver.find_elements(By.CSS_SELECTOR, "dl.prodMenu")
        for block in blocks:
            try:
                product_name = block.find_element(By.TAG_NAME, "dt").get_attribute("textContent").strip()

                tag_wrap = block.find_elements(By.CSS_SELECTOR, "div.prodTag_wrap > span")
                tags = [t.get_attribute("textContent").strip() for t in tag_wrap]

                results.append({
                    "제품명": product_name,
                    "태그": ", ".join(tags) if tags else ""
                })
            except Exception as e:
                print(f"❗ 제품 정보 파싱 에러: {e}")
    except Exception as e:
        print(f"❗ 블록 수집 에러: {e}")
        break

    # 페이지 이동
    try:
        pagination = driver.find_element(By.CLASS_NAME, "boardPage")
        li_list = pagination.find_elements(By.TAG_NAME, "li")

        # 현재 페이지 인덱스 확인
        current_idx = -1
        for i, li in enumerate(li_list):
            if "on" in li.get_attribute("class"):
                current_idx = i
                break

        next_found = False

        # 다음 숫자 페이지 클릭
        if 0 <= current_idx < len(li_list) - 1:
            next_li = li_list[current_idx + 1]
            if "btn_next" not in next_li.get_attribute("class"):
                next_li.find_element(By.TAG_NAME, "a").click()
                page_num += 1
                continue

        # 다음 세트 페이지 (btn_next) 클릭
        prev_page = page_num
        next_btn = driver.find_element(By.CSS_SELECTOR, "ul.boardNav > li > a.btn_next")
        driver.execute_script("arguments[0].click();", next_btn)
        time.sleep(2)

        # 새 페이지 번호 업데이트
        pagination = driver.find_element(By.CLASS_NAME, "boardPage")
        li_list = pagination.find_elements(By.TAG_NAME, "li")
        for i, li in enumerate(li_list):
            if "on" in li.get_attribute("class"):
                page_num = int(li.text.strip())
                break

        if page_num == prev_page:
            print("✅ 마지막 페이지 도달 (btn_next 클릭해도 이동 없음)")
            break

    except Exception as e:
        print(f"❗ 페이지 이동 중 에러 발생: {e}")
        break

driver.quit()

# CSV 저장
df = pd.DataFrame(results)
df.to_csv("dongwonfnb_product_list_with_tags.csv", index=False, encoding="utf-8-sig")
print("✅ 전체 제품 정보 저장 완료. 총 수집 개수:", len(df))
