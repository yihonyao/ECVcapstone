import pandas as pd
from glob import glob
import os
import numpy as np

FINANCIAL_METRICS=['Capital','NetIncomeLoss','NI_Margin_Ratio','ROE_Ratio','EBITDA_Ratio','Current_Ratio',
                   'InterestCoverage_Ratio','OCF_Ratio','ResearchAndDevelopmentExpense','ResearchAndDevelopmentExpense_Growth_Ratio','Revenues',
                   'Revenue_Growth_Ratio','NI_Growth_Ratio','EarningsPerShareBasic','EPS_Growth_Ratio']

def read_company_info(country:str='all',archive_dir='./setup/公司基本資料.xlsx'):
    
    '''從設定檔讀取公司基本資料'''
    
    company_info_df=pd.read_excel(archive_dir)
    return company_info_df

def read_rawdata(archive_dir='./raw_data'):
    
    '''讀取所有的rawdata'''
    
    rawdata_filenames = [file for file in os.listdir(archive_dir) if file.endswith('raw_data.csv')]
    rawdata_dfs=[]
    
    for rawdata_filename in rawdata_filenames:
        file_path = os.path.join(archive_dir, rawdata_filename)
        rawdata_df = pd.read_csv(file_path)
        rawdata_dfs.append(rawdata_df)
    combined_raw_df = pd.concat(rawdata_dfs, ignore_index=True)
    combined_raw_df.set_index(['company', 'year','Enddate'], inplace=True)
    return combined_raw_df

def process_rawdata_format(combined_raw_df):
    
    '''將rawdata只留下所需的會計項目，會計項目的來源是「會計科目表」'''
    
    #所需抓取的會計項目是會計科目表的所有value
    account_df=pd.read_excel(f'./setup/會計科目表.xlsx',index_col='Target_Account')
    total_account_cleaned=set(account_df.values.flatten().tolist())
    total_account_cleaned=[x for x in total_account_cleaned if x == x]
    #rawdata欄位只保留需要的會計項目
    combined_raw_df = combined_raw_df.loc[:, total_account_cleaned]
    return combined_raw_df

def account_standarized(COMBINED_RAW_DF,setup_file_dir='./setup'):
    
    '''將COMBINDE_RAW_DF的欄位，對照會計科目表做轉換'''
    
    #讀取會計科目表，並將會計項目作為index
    account_df=pd.read_excel(f'{setup_file_dir}/會計科目表.xlsx',index_col='Target_Account')
    
    for tag in COMBINED_RAW_DF.columns:
        for account in account_df.index:
            search_value = tag
            account_row=account_df.loc[account]
            row_contains_value = (account_row == search_value).any()
            
            if row_contains_value==True:
                COMBINED_RAW_DF.rename(columns={tag:account},inplace=True)
                
    merged_df = COMBINED_RAW_DF.groupby(level=0, axis='columns').sum()
    print('Account Standarization Finished.\n')    
    return merged_df

def dealwith_specific_account(COMBINED_RAW_DF:pd.DataFrame):
    
    '''
    1.如果有CommonStockValue和AdditionalPaidInCapital，則Capital為兩者相加 
    2.如果有Depreciation和Amortization，則DepreciationAndAmortization為兩者相加；若這兩者有一個沒有，則OtherDepreciationAndAmortization為DepreciationAndAmortization
    '''
    
    #在計算比率前需要先處理部分公司會計科目缺漏的問題
    COMBINED_RAW_DF.reset_index(inplace=True)
    company_info_df=read_company_info()
    all_company_list=list(company_info_df['company'])
    df_proxy=[]
    
    for company in all_company_list:
        company_df=COMBINED_RAW_DF[COMBINED_RAW_DF['company']==company].copy()  # 使用 copy() 创建一个切片的副本
        if (company_df['Capital']==0).all():
            company_df.loc[:, 'Capital']=company_df['CommonStockValue']+company_df['AdditionalPaidInCapital']  # 使用 .loc[row_indexer,col_indexer] = value
          
        if company=='RACKSPACE TECHNOLOGY, INC.':
            company_df.loc[:, 'DepreciationAndAmortization']=company_df['OtherDepreciationAndAmortization']
          
        if (company_df['DepreciationAndAmortization']==0).all():
            company_df.loc[:, 'DepreciationAndAmortization']=company_df['Depreciation']+company_df['Amortization']

        if (company_df['InterestExpense']==0).all():
            company_df.loc[:, 'InterestExpense']=company_df['InterestPaidNet']


        company_df['LastYearRevenues'] = company_df['Revenues'].shift(1)
        company_df['LastYearNetIncomeLoss'] = company_df['NetIncomeLoss'].shift(1)
        company_df['LastYearEarningsPerShareBasic'] = company_df['EarningsPerShareBasic'].shift(1)
        company_df['LastYearResearchAndDevelopmentExpense'] = company_df['ResearchAndDevelopmentExpense'].shift(1)
        company_df['BeginningStockholdersEquity'] = company_df['StockholdersEquity'].shift(1)
        df_proxy.append(company_df)
    
    processed_combined_df=pd.concat(df_proxy, ignore_index=True)
    processed_combined_df.drop(columns=['CommonStockValue', 'AdditionalPaidInCapital', 'Depreciation','Amortization','OtherDepreciationAndAmortization'], inplace=True)
    print('Finished Transfering Specific Account\n')
    return processed_combined_df

def transform_financial_data(df):

    '''會計年度轉換'''

    transformed_dfs = []
    company_info_df=read_company_info()
    companies=list(company_info_df['company'])
 
    for company_name in companies:
        # Filter rows corresponding to the given company
        company_data = df[df['company'] == company_name]

        for year in range(2016, 2025):
            # Filter rows corresponding to the given year
            filtered_df = company_data[company_data['year'] == year]
            
            # Check if there are rows for the current year
            if not filtered_df.empty:
                # Extract the enddate for the current year
                enddate = str(filtered_df.iloc[0]['Enddate'])
                
                # Extract the month from the enddate
                end_month = int(enddate[4:6])
                
                # Check if the enddate format is "yyyyMMdd" (e.g., "20210331")
                if not enddate.endswith("1231"):
                    # Calculate the weights for the current year data based on the month
                    weight_current_year = (end_month - 1) / 12
                    weight_next_year = (12 - end_month + 1) / 12
                    
                    # Filter rows corresponding to the next year
                    next_year = year + 1
                    next_year_df = df[(df['company'] == company_name) & (df['year'] == next_year)]
                    
                    # Check if there is data available for the next year
                    if not next_year_df.empty:
                        # Separate data for the current year and the next year
                        data_current_year = filtered_df.iloc[:, 3:] * weight_current_year
                        data_next_year = next_year_df.iloc[:, 3:] * weight_next_year
                        # Combine weighted data for the current year and the next year
                        combined_data = data_current_year.sum() + data_next_year.sum()
                        # Add company and year columns to the combined data
                        combined_data['company'] = company_name
                        combined_data['year'] = year
                        
                        # Append the combined data to the list of transformed DataFrames
                        transformed_dfs.append(pd.DataFrame([combined_data]))
                    else:
                        # If there is no data available for the next year, leave the current year data unchanged
                        transformed_dfs.append(filtered_df)
                else:
                    # If the enddate is in the format "yyyy1231", no transformation is needed
                    transformed_dfs.append(filtered_df)
    
    # Concatenate all transformed DataFrames
    result_df = pd.concat(transformed_dfs, ignore_index=True)
    # Drop the 'Enddate' column from the last DataFrame
    result_df.drop(columns=['Enddate'], inplace=True)
    result_df.set_index(['company','year'],inplace=True)
    print('Finished Transforming to Fiscal Year.\n')
    return result_df

def read_financialmetrics_formula(archive_dir='./setup/財務指標公式.xlsx') -> dict:

    '''讀取財務指標公式檔案，以計算財務比率'''

    formula_df = pd.read_excel(archive_dir)
    formula_dict = formula_df.set_index('Description')['Formula'].to_dict()
    return formula_dict

def evaluate_pandas_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    for key, value in EVAL_CONFIG.items():
        df.eval(f'{key} = {value}', inplace=True)
    df.replace([np.inf, -np.inf], np.nan, inplace=True)
    print('Finished calculating the Finance Ratio\n')
    return df

def add_company_info(df:pd.DataFrame):
    df.reset_index(inplace=True)
    company_info_df=read_company_info()
    company_country_and_service_type=company_info_df[['company','country','ServiceType']]
    combined_df=pd.merge(df,company_country_and_service_type,left_on='company',right_on='company',how='left')
    combined_df.set_index(['company','year','ServiceType','country'],inplace=True)
    return combined_df

def output(pivot_df:pd.DataFrame,dir='./processed_data'):
    if dir=='./processed_data':
        if not os.path.isdir(dir):
            os.makedirs(dir)
        pivot_df.to_csv(f'{dir}/processed_data.csv', index=False)
        print(f'Already build processed_data.csv at processed_data folder.')


if __name__== '__main__':
    COMBINED_RAW_DF=process_rawdata_format(read_rawdata())
    COMBINED_RAW_DF=dealwith_specific_account(account_standarized(COMBINED_RAW_DF))
    COMBINED_RAW_DF=transform_financial_data(COMBINED_RAW_DF)
    EVAL_CONFIG=read_financialmetrics_formula()
    PROCESSED_COMBINED_DF=evaluate_pandas_dataframe(COMBINED_RAW_DF)
    PROCESSED_COMBINED_DF=add_company_info(PROCESSED_COMBINED_DF)
    PROCESSED_COMBINED_DF = PROCESSED_COMBINED_DF[FINANCIAL_METRICS]
    PROCESSED_COMBINED_DF.reset_index(inplace=True)
    output(PROCESSED_COMBINED_DF)