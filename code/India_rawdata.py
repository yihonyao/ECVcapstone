import pandas as pd
import os
import xml.etree.ElementTree as ET
import re
import datetime

# Define exchange rates for each year
exchange_rates = {
    2024: 0.01203,
    2023: 0.01211,
    2022: 0.0127,
    2021: 0.0135,
    2020: 0.0135,
    2019: 0.01211
}

def read_company_info(country:str='all',archive_dir='./setup/公司基本資料.xlsx'):
    
    '''從設定檔讀取公司基本資料'''
    
    company_df=pd.read_excel(archive_dir)
    if country == 'all':
        company_name=list(company_df['company'])
    else:
        company_name=list(company_df[company_df['country']==country]['company'])
    return company_name

def parse_xml(xml_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()
    
    # Initialize a dictionary to store parsed data
    parsed_data = {}
    
    # Extract elements with contextRef="FourD" or "OneI"
    elements = root.findall('.//*')
    for element in elements:
        # Check if the element has contextRef="FourD" or "OneI"
        context_ref = element.attrib.get('contextRef', '')
        if context_ref in ["FourD", "OneI"]:
            # Extract element name
            element_name = re.sub(r'{.*}', '', element.tag)  # Remove namespace
            # Extract element value
            element_value = element.text
            try:
                # Try converting to numeric form
                element_value = float(element_value)
            except ValueError:
                # If conversion fails, keep it as a string
                pass
            # Add element details to parsed data
            parsed_data[element_name] = element_value  # Store element value as a single value

    return parsed_data

# List of companies
companies =read_company_info('India')

# Initialize an empty list to store DataFrames for each company
dfs = []

# Iterate over each company
for company in companies:
    # Initialize an empty list to store parsed data for the current company
    company_data = []
    current_year = datetime.date.today().year
    # Define the range of years for calculation
    start_year = current_year - 5

    # List of XML files for the current company
    xml_files = [f'./rawdata/XML_data/{company}/{company} {start_year}.xml',
                 f'./rawdata/XML_data/{company}/{company} {start_year + 1}.xml',
                 f'./rawdata/XML_data/{company}/{company} {start_year + 2}.xml',
                 f'./rawdata/XML_data/{company}/{company} {start_year + 3}.xml',
                 f'./rawdata/XML_data/{company}/{company} {start_year + 4}.xml',
                 f'./rawdata/XML_data/{company}/{company} {start_year + 5}.xml']
    
    # Check if the XML file for 2023 exists for LTIM company
    if company == 'LTIMindtree Limited' and not os.path.exists(xml_files[-1]):
        continue
    
    # Iterate over XML files for the current company
    for xml_file in xml_files:
        # Check if the XML file exists
        if os.path.exists(xml_file):
            # Parse XML file and append parsed data to the list
            parsed_data = parse_xml(xml_file)
            # Add company and year info to parsed data
            parsed_data['company'] = company
            parsed_data['year'] = int(xml_file.split()[-1].split('.')[0])
            company_data.append(parsed_data)
    
    # Create DataFrame from parsed data for the current company
    df = pd.DataFrame(company_data)
    
    # Append DataFrame to the list of DataFrames
    dfs.append(df)

# Concatenate the DataFrames into a single DataFrame
combined_df = pd.concat(dfs, ignore_index=True)

# Reorder columns to have "company" and "year" as the first two columns
combined_df = combined_df[['company', 'year'] + [col for col in combined_df.columns if col not in ['company', 'year']]]

# Rename the column
combined_df = combined_df.rename(columns={"DateOfEndOfReportingPeriod": "Enddate"})
combined_df = combined_df.rename(columns={"DateOfStartOfReportingPeriod": "Startdate"})

# Transform numeric data based on exchange rates for selected rows
for index, row in combined_df.iterrows():
    # Get the year from the second column of the current row
    year = int(row[1])  # Assuming the second column contains the year
    # Apply exchange rate to numeric values in the entire row
    for col in combined_df.columns:
        # Skip the first two columns (company and year)
        if col not in ['company', 'year']:
            try:
                combined_df.at[index, col] *= exchange_rates[year]
            except:
                pass

# Convert the date format in the "Enddate" column from "mm/dd/yyyy" to "yyyy/mm/dd"
for index, row in combined_df.iterrows():
    # Parse the date string in the "Enddate" column
    date_str = row["Enddate"]
    # Parse the date using the old format
    old_date = datetime.datetime.strptime(date_str, "%Y-%m-%d")
    # Convert the date to the new format
    new_date_str = old_date.strftime("%Y%m%d")
    # Set the new date string in the "Enddate" column
    combined_df.at[index, "Enddate"] = new_date_str

for index, row in combined_df.iterrows():
    # Parse the date string in the "Startdate" column
    date_str = row["Startdate"]
    # Parse the date using the old format
    old_date = datetime.datetime.strptime(date_str, "%Y-%m-%d")
    # Convert the date to the new format
    new_date_str = old_date.strftime("%Y%m%d")
    # Set the new date string in the "Startdate" column
    combined_df.at[index, "Startdate"] = new_date_str


# Save the combined DataFrame to a new CSV file
combined_csv_file = './rawdata/India_raw_data.csv'
combined_df.to_csv(combined_csv_file, index=False)
