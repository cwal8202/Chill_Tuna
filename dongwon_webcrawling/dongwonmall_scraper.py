from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import pandas as pd

# 크롬 드라이버 경로 설정
chrome_path = "C:/Users/baby3/Downloads/chromedriver-win64/chromedriver-win64/chromedriver.exe"

# 크롬 옵션
options = Options()
options.add_argument("--start-maximized")

# 드라이버 실행
driver = webdriver.Chrome()
driver.get("https://www.dongwonmall.com/category/main.do?cate_id=01110065")

# "리뷰 많은순" 클릭
WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "span.sort")))
sort_buttons = driver.find_elements(By.CSS_SELECTOR, "span.sort")
for btn in sort_buttons:
    if btn.text.strip() == "리뷰 많은순":
        btn.click()
        break

time.sleep(2)

product_list = []
current_page = 1
max_pages = 2

while True:
    print(f"[페이지 {current_page}] 수집 중...")

    WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "ul#bandBestList > li.product_item"))
    )
    time.sleep(1)

    items = driver.find_elements(By.CSS_SELECTOR, "ul#bandBestList > li.product_item")
    for item in items:
        try:
            name = item.find_element(By.CSS_SELECTOR, "ul#bandBestList > li.product_item > a > p.name").text.strip()
        except:
            name = "N/A"
        try:
            price = item.find_element(By.CSS_SELECTOR, "ul#bandBestList > li.product_item > div.price_info > span.new_price > strong").text.strip()
        except:
            price = "N/A"
        try:
            grade = item.find_element(By.CSS_SELECTOR, "ul#bandBestList > li.product_item > span.star_rating > span.grade").text.strip()
        except:
            grade = "N/A"
        try:
            review = item.find_element(By.CSS_SELECTOR, "ul#bandBestList > li.product_item > span.star_rating > span.review").text.strip()
        except:
            review = "N/A"

        product_list.append({
            "페이지": current_page,
            "상품명": name,
            "가격": price,
            "평점": grade,
            "리뷰 수": review
        })

    if current_page >= max_pages:
        print("✅ 최대 페이지(10) 도달, 종료")
        break

    try:
        # 다음 페이지 번호 존재하는지 확인 (paging 내부의 ul > li > a 구조 사용)
        page_selector = f'div.paging.paging_t20r > ul > li > a'
        all_pages = driver.find_elements(By.CSS_SELECTOR, page_selector)

        next_page_number = str(current_page + 1)
        next_page_elem = None
        for p in all_pages:
            if p.text.strip() == next_page_number:
                next_page_elem = p
                break

        if next_page_elem:
            driver.execute_script("arguments[0].click();", next_page_elem)
            current_page += 1
            time.sleep(2)
        else:
            print("✅ 다음 페이지 없음, 종료")
            break
    except Exception as e:
        print("❌ 예외 발생:", e)
        break

# 저장 및 종료
driver.quit()

df = pd.DataFrame(product_list)
df.to_excel("dongwonmall_review_auto_paging.xlsx", index=False)
print("✅ 엑셀 저장 완료! 총 수집 상품 수:", len(df))
