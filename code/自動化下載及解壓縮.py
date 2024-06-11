import requests
import zipfile
from datetime import date
from datetime import datetime
import os
import pandas as pd

FS_DATASET_URL: str = f'https://www.sec.gov/files/dera/data/financial-statement-and-notes-data-sets'

def download_sec_file_by_requests(filename: str, download_path: str) -> None:
    url: str = f'{FS_DATASET_URL}/{filename}'
    print(url)
    headers: dict = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0',
        'Referer': f'https://www.sec.gov/files/dera/data/financial-statement-and-notes-data-sets',
        'Host': 'www.sec.gov'
    }
    
    print('Current Time:', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    response = requests.get(url, headers=headers)
    print(response)
    
    if not os.path.isdir(download_path):
        os.makedirs(download_path)
        
    if response.status_code == 200:
        print(f'Downloading {filename}...')
        with open(f'{download_path}/{filename}', 'wb') as f:
            f.write(response.content)
            print(f'Downloaded {filename}')
            print(f'{download_path}/{filename}')
    else:
        print(f"Failed to download {filename}")
        
#將sub及num檔案解壓縮並修改檔名儲存到dataset資料夾裡，完成上述動作後將壓縮檔刪除
def extract(filename: str, file_path: str):
    with zipfile.ZipFile(f'{file_path}/{filename}', 'r') as zf:
        for name in zf.namelist():
            if name == 'num.tsv' or name == 'sub.tsv':
                print(f'extracting {name} in {filename}...')
                zf.extract(name, path=file_path)
        filename_without_extension = filename.split('.')[0]
    # Renaming should be done outside the loop, after all files are extracted
        os.rename(os.path.join(file_path, 'num.tsv'), os.path.join(file_path, f'{filename_without_extension}_num.tsv'))
        os.rename(os.path.join(file_path, 'sub.tsv'), os.path.join(file_path, f'{filename_without_extension}_sub.tsv'))
    os.remove(f'./rawdata/'+filename)
    print(f'remove {filename}\n...')        

def us_company_upload_month():
    company_info=pd.read_excel('./setup/公司基本資料.xlsx')
    us_start_months = set(company_info[company_info['country'] == 'US']['StartMonth'])
    us_company_upload_month={x + 1 for x in us_start_months}|{x + 2 for x in us_start_months}
    return us_company_upload_month

#決定要抓取的資料檔名
def get_filenames():
    
    '''由於SEC新政策會提供12個月內的月檔案，導致抓取的檔案檔名會不一致，因此需要做額外條件判斷的處理。此外，公司上傳年報的期限為會計年度結束後60-90天'''
    
    The_month_we_need=us_company_upload_month()
    
    t=date.today().year
    m=1
    t,m=date.today().year,date.today().month
    filenames=[]
    
    #以目標t~t-5年為迴圈，若為今年，則於12個月內的檔名會是以月分呈現，例如:本月為2024年5月，則2023/4-2024/4的檔名為 2023_04_notes.zip
    for year in range(t,t-5,-1):
        if year == t: 
            for month in range(1,m,1): #看目前是幾月，如果是5月，則檔案最多到今年4月
                if month in The_month_we_need:
                    formatted_month = str(month).zfill(2) #月份兩碼
                    filenames.append(f'{year}_{formatted_month}_notes.zip')
                    #上述迴圈的意思是，如果有目標公司上傳財報的月份，就列入要下載的file
        elif year==t-1:
            for month in range(12,m-2,-1):
                if month in The_month_we_need:
                    formatted_month = str(month).zfill(2)
                    filenames.append(f'{year}_{formatted_month}_notes.zip')
        else :
            if 1 in The_month_we_need or 2 in The_month_we_need or 3 in The_month_we_need:
                filenames.append(f'{year}q1_notes.zip')
            if 4 in The_month_we_need or 5 in The_month_we_need or 6 in The_month_we_need:
                filenames.append(f'{year}q2_notes.zip')
            if 7 in The_month_we_need or 8 in The_month_we_need or 9 in The_month_we_need:
                filenames.append(f'{year}q3_notes.zip')
            if 10 in The_month_we_need or 11 in The_month_we_need or 12 in The_month_we_need:
                filenames.append(f'{year}q4_notes.zip')
    
    return filenames
          
                    
if __name__ == '__main__':
    FILENAMES=get_filenames()
    for filename in FILENAMES:
        download_sec_file_by_requests(filename, './rawdata')
        extract(filename, './rawdata')
    print('Already extracted sub,num file to rawdata file_folder and remove zipfile.')
    print('-----------------------------------------------------------------')
