from sklearn.preprocessing import StandardScaler
import datetime
import pandas as pd

def standarize(df: pd.DataFrame) -> pd.DataFrame:
    # Ensure 'year' and 'company' columns are present and correctly named
    if 'Year' in df.columns:
        df.rename(columns={'Year': 'year'}, inplace=True)
    if 'Company' in df.columns:
        df.rename(columns={'Company': 'company'}, inplace=True)
    
    print("Columns after renaming:", df.columns)
    
    if 'year' not in df.columns or 'company' not in df.columns:
        raise KeyError("The dataframe must contain 'year' and 'company' columns.")
    
    scaler = StandardScaler()
    t = datetime.date.today().year
    ratio_columns = [col for col in df.columns if col.endswith('Ratio')]
    
    df.reset_index(inplace=True)
    df.set_index(['year', 'company'], inplace=True)

    output_dfs = []
    # Extract the same year data and standardize Ratio columns
    for year in range(t - 1, t - 6, -1):
        if year in df.index.get_level_values('year'):
            year_df = df.loc[year].copy()
            year_df['year'] = year
            year_df[ratio_columns] = scaler.fit_transform(year_df[ratio_columns])
            year_df = year_df.reset_index()
            output_dfs.append(year_df)
    
    output_df = pd.concat(output_dfs, axis=0, ignore_index=True)
    output_df.set_index(['company', 'year'], inplace=True)
    output_df.drop(['index'], axis=1, inplace=True)
    output_df = output_df.sort_index(level='company')
    output_df.reset_index(level=['company', 'year'], inplace=True)
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
    standardized_df = df.copy()
    standardized_df[metrics] = scaler.fit_transform(standardized_df[metrics])

    # Calculate factor scores using the standardized values
    df['Profitability_Score'] = (0.5 * standardized_df['NI_Margin_Ratio'] +
                                 0.5 * standardized_df['ROE_Ratio'] +
                                 standardized_df['EBITDA_Ratio'])
    
    df['Risk_Score'] = (0.5 * standardized_df['Current_Ratio'] +
                        0.5 * standardized_df['InterestCoverage_Ratio'] +
                        standardized_df['OCF_Ratio'])
    
    df['Growth_Rate_Score'] = (0.5 * standardized_df['ResearchAndDevelopmentExpense_Growth_Ratio'] +
                               0.5 * standardized_df['Revenue_Growth_Ratio'] +
                               standardized_df['NI_Growth_Ratio'] +
                               standardized_df['EPS_Growth_Ratio'])

    df['Yearly_Score'] = df['Profitability_Score'] + df['Risk_Score'] + df['Growth_Rate_Score']

    # Calculate yearly ranks for the defined range of years
    df['Yearly_Rank'] = df[df['year'].between(start_year, end_year)].groupby('year')['Yearly_Score'].rank(ascending=False)

    # Calculate the total score for each company with the accurate weighted calculation
    def calculate_weighted_score(group):
        available_years = group['year'].nunique()
        weights = {start_year: 1, start_year + 1: 2, start_year + 2: 3, start_year + 3: 4, start_year + 4: 5}
        weighted_sum = sum(group.loc[group['year'] == year, 'Yearly_Score'].values[0] * weights[year] for year in range(start_year, start_year + available_years) if not group.loc[group['year'] == year, 'Yearly_Score'].empty)
        total_weight = sum(weights[year] for year in range(start_year, start_year + available_years) if year in group['year'].values)
        return weighted_sum / total_weight if total_weight > 0 else 0

    total_scores = (df[df['year'].between(start_year, end_year)]
                    .groupby('company')
                    .apply(calculate_weighted_score))
    
    total_scores = total_scores.rename('Total_Score').reset_index()

    # Merge the total scores back into the original dataframe
    df = pd.merge(df, total_scores, on='company', how='left')

    # Calculate the total ranks based on the total scores
    df['Total_Rank'] = df.groupby('year')['Total_Score'].rank(ascending=False)

    return df

# Load the data
combined_df = pd.read_csv('./processed_data/processed_data.csv')

# Check and rename columns if necessary
print("Original columns:", combined_df.columns)
if 'Year' in combined_df.columns:
    combined_df.rename(columns={'Year': 'year'}, inplace=True)
if 'Company' in combined_df.columns:
    combined_df.rename(columns={'Company': 'company'}, inplace=True)

# Keep a copy of the original data for final output
original_df = combined_df.copy()

# Standardize the data and calculate factor scores and ranks
standarized_df = standarize(combined_df)
transformed_df = calculate_factor_scores_and_ranks(standarized_df)

# Combine the original data with the calculated scores
final_df = pd.merge(original_df, transformed_df[['company', 'year', 'Profitability_Score', 'Risk_Score', 'Growth_Rate_Score', 'Yearly_Score', 'Yearly_Rank', 'Total_Score', 'Total_Rank']], on=['company', 'year'])

# Save the final data
final_df.to_csv('./final_data/final_data.csv', index=False)
