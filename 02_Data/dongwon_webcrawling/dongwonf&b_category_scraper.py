# dongwonfnb_scraper_final.py

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import pandas as pd

# ===== 드라이버 설정 =====
driver = webdriver.Chrome()
driver.get("https://www.dongwonfnb.com/services/Product/Product_List")
wait = WebDriverWait(driver, 10)
time.sleep(3)

results = []

# ===== 1차 카테고리 수집 =====
first_select = Select(wait.until(EC.presence_of_element_located((By.ID, "selCategoryD1"))))
first_options = [opt.text for opt in first_select.options if opt.text != "1차분류"]

for first in first_options:
    # fresh select 객체로 1차 카테고리 선택
    first_select = Select(driver.find_element(By.ID, "selCategoryD1"))
    first_select.select_by_visible_text(first)
    time.sleep(2)

    # ===== 2차 카테고리 수집 =====
    second_select = Select(driver.find_element(By.ID, "selCategoryD2"))
    second_options = [opt.text for opt in second_select.options if opt.text != "2차분류"]

    for second in second_options:
        # fresh select 객체로 2차 카테고리 선택
        second_select = Select(driver.find_element(By.ID, "selCategoryD2"))
        second_select.select_by_visible_text(second)
        time.sleep(1)

        # ✅ "조회" 버튼 클릭
        search_btn = driver.find_element(By.CLASS_NAME, "ico_right")
        search_btn.click()
        time.sleep(2)

        # ===== 페이지 루프 시작 =====
        page_num = 1
        while True:
            print(f"📄 {first} > {second} > 페이지 {page_num}")
            time.sleep(1)

            items = driver.find_elements(By.CSS_SELECTOR, "dl.prodMenu > dt")
            for item in items:
                results.append({
                    "1차카테고리": first,
                    "2차카테고리": second,
                    "메뉴명": item.get_attribute("textContent").strip()
                })

            # 다음 페이지 버튼 탐색
            try:
                pagination = driver.find_element(By.CLASS_NAME, "boardPage")
                li_list = pagination.find_elements(By.TAG_NAME, "li")

                current_idx = -1
                for i, li in enumerate(li_list):
                    if "on" in li.get_attribute("class"):
                        current_idx = i
                        break

                next_found = False
                if 0 <= current_idx < len(li_list) - 1:
                    next_li = li_list[current_idx + 1]
                    if "btn_next" not in next_li.get_attribute("class"):
                        next_li.find_element(By.TAG_NAME, "a").click()
                        page_num += 1
                        next_found = True
                        continue

                # 다음 세트 버튼 처리
                if not next_found:
                    try:
                        prev_page = page_num
                        next_btn = driver.find_element(By.CSS_SELECTOR, "ul.boardNav > li > a.btn_next")
                        driver.execute_script("arguments[0].click();", next_btn)
                        time.sleep(2)

                        # 페이지 증가했는지 확인
                        pagination = driver.find_element(By.CLASS_NAME, "boardPage")
                        li_list = pagination.find_elements(By.TAG_NAME, "li")
                        for li in li_list:
                            if "on" in li.get_attribute("class"):
                                page_num = int(li.text.strip())
                                break

                        if page_num == prev_page:
                            print("✅ 마지막 페이지 도달.")
                            break

                        print("➡️ 다음 버튼 클릭 (세트 이동)")
                        continue
                    except:
                        print("✅ 다음 세트 없음 (btn_next 클릭 실패).")
                        break

            except Exception as e:
                print(f"❗ 페이지 이동 중 에러: {e}")
                break

driver.quit()

# ===== 결과 저장 =====
df = pd.DataFrame(results)
df.to_csv("dongwonfnb_all_products.csv", index=False, encoding="utf-8-sig")
print("✅ 제품 목록 저장 완료. 총 항목 수:", len(df))
