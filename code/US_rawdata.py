import pandas as pd
import csv
from glob import glob
import datetime
from sklearn.preprocessing import StandardScaler
import os


SUB_FILES=glob("./rawdata/*sub.tsv")
NUM_FILES=glob("./rawdata/*num.tsv")

#讀取目標公司的基本資料
def read_company_name(country:str='all',archive_dir='./setup/公司基本資料.xlsx'):
    
    '''從設定檔讀取公司基本資料'''
    
    company_df=pd.read_excel(archive_dir)
    if country == 'all':
        company_name=list(company_df['company'])
    else:
        company_name=list(company_df[company_df['country']==country]['company'])

    #company_name=list(map(lambda x: x.upper(), company_name))
    return company_name

def read_account_list(company_name:str,archive_dir='./setup/會計科目表.xlsx'):
    
    '''從設定檔讀取目標公司使用的會計科目'''
    
    account_df=pd.read_excel(archive_dir)
    company_use_account=list(account_df[company_name])
    company_use_account = [x for x in company_use_account if x == x]
    return company_use_account

def readfiles(subfiles:str, numfiles:str):
    
    '''讀取t~t-5年的sub、num file'''
    print('Start Reading sub_files...')
    Company_sub=pd.concat((pd.read_csv(file,sep='\t',low_memory=False) for file in subfiles))
    print('Reading sub_files finished...')
    Company_sub.set_index("name",inplace=True)
    mask = Company_sub['fp'] == 'FY'

    print('Start Reading num_files...')
    Company_num=pd.concat((pd.read_csv(file,sep='\t',low_memory=False) for file in numfiles))
    Company_num.set_index("adsh",inplace=True)
    print('Finished Reading num_files ...\n')
    return Company_sub[mask],Company_num

def pivot_table(company_list:list):
    
    '''建立以[company,ddate]為index，並且column為各會計科目的pivot_table'''
    
    print('Start building pivot table...\n')
    Account_df = pd.DataFrame()
    for company in company_list:
        #從sub檔案裡抓取company上傳年報的adsh碼
        print(f'Extracting {company} Financial Statements...')
        #抓取出company t~t-5年的sub資料，並且num檔案裡的公司名稱皆為大寫，因此讀取num時，公司名稱時要記得轉換成大寫
        adsh_df=COMPANY_SUB.loc[company.upper(),["adsh"]]
        account_list=read_account_list(company)
        for name,adsh_row in adsh_df.iterrows():
            adsh = adsh_row["adsh"]
            
            #從num抓取出目標公司t~t-5年的財務資料
            Company_FS=COMPANY_NUM.loc[adsh]
            Company_FS_copy=Company_FS.copy()
            for account in account_list:
                filt = (Company_FS['tag'] == account) & (Company_FS['dimh'] == '0x00000000') & ((Company_FS['qtrs'] == 4)|(Company_FS['qtrs'] == 0))
        #'dimh' = '0x00000000'代表抓的是科目的總金額，而設定qtrs的目的是為了避免公司上上傳財報格式不一致，例如insight在num檔案裡包含了季報的數字，而且將季報的dimh也設定為0x00000000，因此會導致抓取到季報金額以及Q4會計入兩次全年金額
                
                Company_FS_copy.loc[filt, 'company'] = company #將抓取到的dataframe新增一欄公司名稱
                Account_df = pd.concat([Account_df, Company_FS_copy.loc[filt, ['company','tag', 'ddate', 'value']]])
        print(f'Finished Extracting {company} Account...\n')
    Account_df.reset_index(drop=True, inplace=True)
        
    #接著處理財報重編的問題，如果一間公司有重編財報，則該間公司同年份同科目的資料會有多筆，如果不進行處理，則在建立pivot table時會導致金額有誤，操作邏輯如下:重編的財報一定會是較大的Index，因此如果公司名稱、科目名稱、日期相同，留下index較大的那筆。    
    #先創建一個index column
    Account_df['original_index'] = Account_df.index
    #依據company,tag,ddate進行groupby後挑選各組裡index最大，也就是最新的資料，這樣就能解決重編以及重複的問題，並且將最大那筆的原index取出
    idx = Account_df.groupby(['company', 'tag', 'ddate'])['original_index'].idxmax()
    #根據取出的原index去取出Account dataframe的row
    filtered_df = Account_df.loc[idx].reset_index(drop=True)
    #再將original index刪掉
    filtered_df = filtered_df.drop(columns=['original_index'])
        
    Account_df_unique_copy = filtered_df.copy()
    Account_df_unique_copy['year'] = pd.to_datetime(Account_df_unique_copy['ddate'], format='%Y%m%d').dt.year 
    Account_df_unique_copy.rename(columns={'ddate': 'Enddate'}, inplace=True)   
    #建立pivot table
    pivot_df = Account_df_unique_copy.pivot_table(index=['company','year','Enddate'], columns='tag', values='value') #建立company、year為row，tag為column的pivot table
    pivot_df.reset_index(inplace=True)
    return pivot_df

def output(pivot_df:pd.DataFrame,dir='./'):
    if dir=='./':
        pivot_df.to_csv(f'{dir}/US_raw_data.csv', index=False)
        print(f'Already build US_raw_data.csv in this Folder.')
    else:
        if not os.path.isdir(dir):
            os.makedirs(dir)
            pivot_df.to_csv(f'{dir}/US_raw_data.csv', index=False)
        else:
            pivot_df.to_csv(f'{dir}/US_raw_data.csv', index=False)
        print(f'Already build US_raw_data.csv at {dir}')
    

if __name__ == '__main__':
    US_COMPANY=read_company_name('US')
    COMPANY_SUB,COMPANY_NUM=readfiles(SUB_FILES,NUM_FILES)
    PIVOT_TABLE=pivot_table(US_COMPANY)
    output(PIVOT_TABLE,'./rawdata') #可指定要存放的路徑
