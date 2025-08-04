import pandas as pd
import time
import traceback
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# --- 설정 ---
options = Options()
options.add_argument("--start-maximized")
driver = webdriver.Chrome(options=options)
start_url = "https://www.dongwonmall.com/category/main.do?cate_id=01110065" # 최상위 카테고리
driver.get(start_url)
time.sleep(2)

# =======================================================================================
# 1. 네비게이션 정보 전체 수집
# =======================================================================================
print("=========== 1. 전체 카테고리 네비게이션 정보 수집 시작 ===========")
all_navigation_tasks = []

# 1-1. 1차 카테고리 정보 수집
l1_elements = driver.find_elements(By.CSS_SELECTOR, "div#allCateList > div.tree-group > ul.list-depth > li.list-item > a")
l1_category_info = []
for elem in l1_elements:
    try:
        name = elem.find_element(By.CSS_SELECTOR, "span.txt").get_attribute("textContent").strip()
        link = elem.get_attribute("href")
        print(f"  └─ [1차] '{name}' '{link}' 정보 수집 완료.")
        if name and link:
            l1_category_info.append({"name": name, "link": link})
    except NoSuchElementException:
        continue

print(f"📌 총 {len(l1_category_info)}개의 1차 카테고리 발견")

# 1-2. 각 카테고리를 순회하며 최종 3차 카테고리 정보 추출
for l1_cat in l1_category_info:
    l1_name = l1_cat['name']
    l1_link = l1_cat['link']
    
    try:
        print(f"\n[1차] '{l1_name}' 탐색 중...")
        driver.get(l1_link)
        time.sleep(1)

        # 1-3. 2차 카테고리 정보 수집
        l2_elements = driver.find_elements(By.CSS_SELECTOR, "div#nowCateList > div.tree-group > ul.list-depth > li.list-item >  ul.list-depth > li.list-item > a")
        if not l2_elements:
            print(f"  └─ 2차 카테고리 없음.")
            continue
        
        l2_category_info = []
        for elem in l2_elements:
            name = elem.get_attribute("textContent").strip()
            onclick = elem.get_attribute("href")
            if name and "changeCategory" in onclick:
                l2_category_info.append({"name": name, "onclick": onclick})

        # 1-4. 3차 카테고리 정보 수집
        for l2_cat in l2_category_info:
            l2_name = l2_cat['name']
            l2_onclick = l2_cat['onclick']
            print(f"  └─ [2차] '{l2_name}' 탐색 중...")
            
            driver.execute_script(l2_onclick)
            time.sleep(1)

            l3_elements = driver.find_elements(By.CSS_SELECTOR, "div#nowCateList ul.list-depth.morethan > li > ul.list-depth.morethan > li > a")
            if not l3_elements:
                print(f"    └─ 3차 카테고리 없음.")
                continue

            for elem in l3_elements:
                l3_name = elem.get_attribute("textContent").strip()
                l3_onclick = elem.get_attribute("href")
                if l3_name and "changeCategory" in l3_onclick:
                    print(f"      └─ [3차] '{l3_name}' 정보 수집 완료.")
                    # 최종 작업 목록에 추가
                    all_navigation_tasks.append({
                        "l1_name": l1_name, "l1_link": l1_link,
                        "l2_name": l2_name, "l2_onclick": l2_onclick,
                        "l3_name": l3_name, "l3_onclick": l3_onclick
                    })
    except Exception as e:
        print(f"🚨 '{l1_name}' 카테고리 정보 수집 중 오류 발생. 다음으로 넘어갑니다.")
        traceback.print_exc()
        continue

print(f"\n=========== ✅ 총 {len(all_navigation_tasks)}개의 최종 카테고리 정보 수집 완료 ===========")


# =======================================================================================
# 2. 수집된 정보 기반으로 데이터 크롤링
# =======================================================================================
print("\n=========== 2. 실제 데이터 크롤링 시작 ===========")
all_data = []

for i, task in enumerate(all_navigation_tasks):
    print(f"\n🔎 [{i+1}/{len(all_navigation_tasks)}] 작업 시작: {task['l1_name']} > {task['l2_name']} > {task['l3_name']}")
    
    try:
        # 각 작업마다 안정성을 위해 1차 카테고리부터 다시 시작
        driver.get(task['l1_link'])
        time.sleep(1)
        driver.execute_script(task['l2_onclick'])
        time.sleep(1)
        driver.execute_script(task['l3_onclick'])
        time.sleep(2)

        # "리뷰 많은순" 클릭
        try:
            sort_buttons = WebDriverWait(driver, 5).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "span.sort")))
            review_sort_btn = next((btn for btn in sort_buttons if btn.text.strip() == "리뷰 많은순"), None)
            if review_sort_btn:
                review_sort_btn.click()
                time.sleep(2)
        except TimeoutException:
            print("  └─ ⚠️ 정렬 버튼을 찾을 수 없음. 그대로 진행합니다.")

        # 페이지 순회하며 상품 정보 수집 (최대 10페이지)
        max_pages = 10
        for page_num in range(1, max_pages + 1):
            print(f"  └─ 페이지 {page_num}/{max_pages}")
            try:
                WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "ul#bandBestList > li.product_item")))
            except TimeoutException:
                print("    └─ ⚠️ 상품 목록을 불러오지 못했습니다.")
                break

            items = driver.find_elements(By.CSS_SELECTOR, "ul#bandBestList > li.product_item")
            if not items:
                print("    └─ 상품이 없습니다.")
                break

            for item in items:
                try:
                    name = item.find_element(By.CSS_SELECTOR, "p.name").text.strip()
                    price = item.find_element(By.CSS_SELECTOR, "div.price_info span.new_price strong").text.strip()
                    grade = item.find_element(By.CSS_SELECTOR, "span.star_rating span.grade").text.strip()
                    review = item.find_element(By.CSS_SELECTOR, "span.star_rating span.review").text.strip()
                    all_data.append({
                        "1차 카테고리": task['l1_name'], "2차 카테고리": task['l2_name'], "3차 카테고리": task['l3_name'],
                        "페이지": page_num, "상품명": name, "가격": price, "평점": grade, "리뷰 수": review
                    })
                except NoSuchElementException:
                    continue # 일부 정보 없는 상품은 건너뛰기
            
            if page_num < max_pages:
                try:
                    next_page_link = driver.find_element(By.XPATH, f"//div[contains(@class, 'paging')]//a[text()='{page_num + 1}']")
                    driver.execute_script("arguments[0].click();", next_page_link)
                    time.sleep(2)
                except NoSuchElementException:
                    print("    └─ 다음 페이지 버튼이 없어 수집을 중단합니다.")
                    break
    except Exception as e:
        print(f"🚨🚨🚨 작업 [{i+1}] 처리 중 심각한 오류 발생. 이 작업을 건너뜁니다.")
        traceback.print_exc()
        continue


# --- 저장 ---
driver.quit()
if all_data:
    df = pd.DataFrame(all_data)
    file_name = f"dongwonmall_final_reviews.xlsx"
    df.to_excel(file_name, index=False)
    print(f"\n✅ 전체 크롤링 완료! 총 {len(df)}개 상품 저장됨 → {file_name}")
else:
    print("\n❌ 수집된 데이터가 없습니다.")