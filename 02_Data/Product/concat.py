# conjoint_csv 폴더에 있는 csv 파일을 합치는 코드
import os
import pandas as pd


def concat_csv(folder_path):
    all_df =[]

    if not os.path.exists(folder_path):
        print('폴더가 확인되지 않음 : ', folder_path)
        return all_df
    
    for filename in os.listdir(folder_path):
        if filename.endswith(".csv"):
            file_path = os.path.join(folder_path, filename)
            df = pd.read_csv(file_path)
            all_df.append(df)
    
    if not all_df:
        print("데이터프레임 비어있음")
        return all_df
    
    concat_df = pd.concat(all_df, ignore_index=True)
    return concat_df

if __name__=="__main__":
    folder_path='./conjoint_csv'
    filename = 'conjoint_csv_concat.csv'
    df = concat_csv(folder_path)
    print(df.head())
    df.to_csv(filename, index=False)
    print(f'df 저장완료 : {filename}')

