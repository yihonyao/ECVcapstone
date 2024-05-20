Here is the reformatted README for the GitHub repository:

# Project: Financial Data Processing for US and Indian Companies

## Folder Structure

```
├── finalized.py
├── India_rawdata.py
├── US_rawdata.py
├── download_and_extract.py
├── data_merge.py
├── raw_data
│   └── XML_data
└── setup
    ├── company_basic_info.xlsx
    ├── account_mapping.xlsx
    └── financial_metrics_formula.xlsx
```

## File Descriptions

### 1. Setup Files

These files contain essential information for adding new target companies and defining the financial framework.

#### a. Company Basic Info (company_basic_info.xlsx)

**Structure:**

| company (full name)                           | StartMonth | country | ServiceType  |
|-----------------------------------------------|------------|---------|--------------|
| COGNIZANT TECHNOLOGY SOLUTIONS CORP           | 1          | US      | IT Services  |

**Note:** The company name must match the data source.

#### b. Account Mapping (account_mapping.xlsx)

**Structure:**

| Target_Account | Company A Account Name        | Company B Account Name        |
|----------------|-------------------------------|-------------------------------|
| Revenue        | Revenue used by Company A     | Revenue used by Company B     |

**Note:** The company name must match the company basic info.

#### c. Financial Metrics Formula (financial_metrics_formula.xlsx)

**Structure:**

| Description             | Formula                                 |
|-------------------------|-----------------------------------------|
| NI_Margin_Ratio         | (NetIncomeLoss / Revenues) * 100        |

**Note:** The formula's account names must refer to the desired account names in the account mapping.

## Usage Instructions

### 1. Adding a New Target Company

#### a. US Company

1. **Find the company on EDGAR:**
   - Search for the company (e.g., Accenture) using its full name as shown in the search bar.
   - Ensure the company name is in uppercase.

   [EDGAR Search](https://www.sec.gov/edgar/search/)

2. **Determine the fiscal year start month:**
   - Browse filing types and set the format to 10-K.
   - Check the "Reporting for" field. If it ends on 8/31, the fiscal year starts in September.

#### b. Indian Company

1. **Find the company on NSE:**
   - Search for the company (e.g., Infosys Limited).
   - Choose "Annual" for Period Ended.
   - The company name in the search bar must match exactly (Infosys Limited).

   [NSE Corporate Filings](https://www.nseindia.com/companies-listing/corporate-filings-financial-results)

2. **Determine the fiscal year start month:**
   - Check the Period Ended field to determine the fiscal year start month (e.g., April for Infosys).

3. **Download the financial reports:**
   - Right-click the XBRL file link and save it as `Company Name_Year.xml` (e.g., Infosys Limited_2024.xml).

4. **Organize the XML data:**
   - Create a folder named `XML_data`.
   - Within `XML_data`, create a folder for each company using its full name.
   - Save each company's XML files in its respective folder.

### 2. Add Account Mapping

1. **Find and add the company's account names:**
   - For each new company, locate the financial report.
   - Identify the account items (e.g., Revenues) and find their tags (account names used by the company).
   - Add these account names to the account mapping file.

### 3. Generate Raw Data

#### a. US Company

1. **Run `download_and_extract.py`**:
   - This script will create a `rawdata` folder containing all the source data.

2. **Run `US_rawdata.py`**:
   - This script will generate `US_rawdata.csv`.

#### b. Indian Company

1. **Run `India_rawdata.py`**:
   - This script will generate `India_rawdata.csv`.

2. **Check exchange rates in `India_rawdata.py`**:
   - Ensure exchange rates for all fiscal years are present.
   - Add missing exchange rates as needed (e.g., `2025: exchange_rate`).

### 4. Generate Processed Data

1. **Run `data_merge.py`**:
   - This script will generate `processed_data.csv` in the `processed_data` folder, including harmonized financial metrics and adjusted fiscal years.

### 5. Generate Final Data

1. **Run `finalized.py`**:
   - This script will generate `Final_data`.
   - Load `Final_data` into PowerBI for further analysis.
