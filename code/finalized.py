from sklearn.preprocessing import StandardScaler
import datetime
import pandas as pd

def standarize(df:pd.DataFrame)->pd.DataFrame:
    scaler = StandardScaler()
    t = datetime.date.today().year
    ratio_columns = [col for col in df.columns if col.endswith('Ratio')]
    df.reset_index(inplace=True)
    df.set_index(['year','company'],inplace=True)

    output_dfs = []
    #把dataframe中相同年分的資料挑出來，針對Ratio的column進行standarize
    for year in range(t - 1, t - 6, -1):
        year_df = df.loc[year].copy()
        year_df['year']=year
        year_df[ratio_columns] = scaler.fit_transform(year_df[ratio_columns])
        year_df = year_df.reset_index()
        
        output_dfs.append(year_df)
    
    output_df = pd.concat(output_dfs, axis=0, ignore_index=True)
    output_df.set_index(['company','year'],inplace=True)
    output_df.drop(['index'],axis=1,inplace=True)
    output_df = output_df.sort_index(level='company')
    output_df.reset_index(level=['company','year'], inplace=True)
    return output_df


def calculate_factor_scores_and_ranks(df):
    # Get the current year
    current_year = datetime.date.today().year

    # Define the range of years for calculation
    start_year = current_year - 5
    end_year = current_year - 1

    # Define the financial metrics
    metrics = [
        'NI_Margin_Ratio', 'ROE_Ratio', 'EBITDA_Ratio', 'Current_Ratio',
        'InterestCoverage_Ratio', 'OCF_Ratio', 'ResearchAndDevelopmentExpense_Growth_Ratio',
        'Revenue_Growth_Ratio', 'NI_Growth_Ratio', 'EPS_Growth_Ratio'
    ]

    # Fill missing values with 0 in the metrics
    df[metrics] = df[metrics].fillna(0)
    
    # Standardize the metrics
    scaler = StandardScaler()
    df[metrics] = scaler.fit_transform(df[metrics])
    
    # Calculate factor scores
    df['Profitability_Score'] = (0.5 * df['NI_Margin_Ratio'] +
                                 0.5 * df['ROE_Ratio'] +
                                 df['EBITDA_Ratio'])
    
    df['Risk_Score'] = (0.5 * df['Current_Ratio'] +
                        0.5 * df['InterestCoverage_Ratio'] +
                        df['OCF_Ratio'])
    
    df['Growth_Rate_Score'] = (0.5 * df['ResearchAndDevelopmentExpense_Growth_Ratio'] +
                               0.5 * df['Revenue_Growth_Ratio'] +
                               df['NI_Growth_Ratio'] +
                               df['EPS_Growth_Ratio'])

    df['Yearly_Score'] = df['Profitability_Score'] + df['Risk_Score'] + df['Growth_Rate_Score']

    # Calculate yearly ranks for the defined range of years
    df['Yearly_Rank'] = df[df['year'].between(start_year, end_year)].groupby('year')['Yearly_Score'].rank(ascending=False)

    # Calculate the total score for each company
    total_scores = (df[df['year'].between(start_year, end_year)]
                    .groupby('company')
                    .apply(lambda x: (x.loc[x['year'] == start_year, 'Yearly_Score'].sum() * 1 +
                                      x.loc[x['year'] == (start_year + 1), 'Yearly_Score'].sum() * 2 +
                                      x.loc[x['year'] == (start_year + 2), 'Yearly_Score'].sum() * 3 +
                                      x.loc[x['year'] == (start_year + 3), 'Yearly_Score'].sum() * 4 +
                                      x.loc[x['year'] == (start_year + 4), 'Yearly_Score'].sum() * 5) / 15))
    
    total_scores = total_scores.rename('Total_Score').reset_index()

    # Merge the total scores back into the original dataframe
    df = pd.merge(df, total_scores, on='company', how='left')

    # Calculate the total ranks based on the total scores
    df['Total_Rank'] = df.groupby('year')['Total_Score'].rank(ascending=False)

    return df

combined_df = pd.read_csv('./processed_data.csv')
standarized_df = standarize(combined_df)
transformed_df = calculate_factor_scores_and_ranks(standarized_df)
transformed_df.to_csv('./final_data.csv', index=False)

