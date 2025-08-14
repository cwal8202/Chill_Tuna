import pandas as pd
import re

# 엑셀 파일 불러오기
file_path = "모든 카테고리.xlsx"
df = pd.read_excel(file_path, header=None)

# 상품명은 E열 (index 4), 2번째 행부터
product_names = df.iloc[1:, 4]

# 1. 중량 수치, 단위 / 수량, 단위 추출
def parse_product_info_v3(text):
    text = str(text)

    # 예: 150g x10캔, 85g 20캔, 200ml*2병 등
    pattern = re.compile(r"(\d+)\s*(g|kg|ml|L|ℓ)\s*[x×*]?\s*(\d+)?\s*([개캔병팩봉매롤]+)?", re.IGNORECASE)

    weight_vals = []
    weight_units = []
    count_vals = []
    count_units = []

    for match in pattern.findall(text):
        weight_val, weight_unit, count, count_unit = match
        weight_vals.append(weight_val)
        weight_units.append(weight_unit)
        count_vals.append(count if count else "")
        count_units.append(count_unit if count_unit else "")

    return (
        ", ".join(weight_vals),
        ", ".join(weight_units),
        ", ".join(count_vals),
        ", ".join(count_units)
    )

# 결과 리스트
all_weight_vals, all_weight_units = [], []
all_count_vals, all_count_units = [], []

for name in product_names:
    wv, wu, cv, cu = parse_product_info_v3(name)
    all_weight_vals.append(wv)
    all_weight_units.append(wu)
    all_count_vals.append(cv)
    all_count_units.append(cu)

# F ~ I열에 삽입
df.iloc[1:, 5] = all_weight_vals     # 중량 수치
df.iloc[1:, 6] = all_weight_units    # 중량 단위
df.iloc[1:, 7] = all_count_vals      # 수량
df.iloc[1:, 8] = all_count_units     # 수량 단위

# 2. 가격 숫자화 ("49,200원" → 49200)
def clean_price(text):
    text = str(text)
    digits = re.sub(r"[^\d]", "", text)
    return int(digits) if digits else ""

df.iloc[1:, 9] = df.iloc[1:, 9].apply(clean_price)  # J열 (가격)

# 3. 리뷰 수 정제 ("(1,467건)" → 1467) → L열 (index 11)
def extract_review_count(text):
    text = str(text)
    digits = re.sub(r"[^\d]", "", text)
    return int(digits) if digits else ""

df.iloc[1:, 11] = df.iloc[1:, 11].apply(extract_review_count)  # L열 (리뷰 수)

# 평점은 K열 (index 10) → 그대로 유지 (float이므로 처리 안 함)

# 저장
output_path = "모든_카테고리_최종_열구조.xlsx"
df.to_excel(output_path, index=False, header=False)

print("✅ 엑셀 저장 완료:", output_path)
