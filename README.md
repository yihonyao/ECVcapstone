# Project: Financial Data Processing for US and Indian Companies

## 壹、資料夾架構

```
├── finalized.py
├── India_rawdata.py
├── US_rawdata.py
├── download_and_extract.py
├── data_merge.py
├── raw_data
│   └── XML_data
└── setup
    ├── 公司基本資料.xlsx
    ├── 會計科目表.xlsx
    └── 財務指標公式.xlsx
```

## 貳、檔案說明

### 1. Setup Files (設定檔案)

這些檔案包含新增目標公司及定義財務框架所需的基本信息。

#### a. 公司基本資料 (company_basic_info.xlsx)

**結構:**

| company (full name)                           | StartMonth | country | ServiceType  |
|-----------------------------------------------|------------|---------|--------------|
| COGNIZANT TECHNOLOGY SOLUTIONS CORP           | 1          | US      | IT Services  |

**補充說明:** 公司名稱須和資料源相符。

#### b. 會計科目表 (account_mapping.xlsx)

**結構:**

| Target_Account | 公司A會計科目名稱             | 公司B會計科目名稱             |
|----------------|-------------------------------|-------------------------------|
| Revenue        | A公司使用的Revenue科目名稱    | B公司使用的Revenue科目名稱    |

**補充說明:** 公司名稱須和公司基本資料相符。

#### c. 財務指標公式 (financial_metrics_formula.xlsx)

**結構:**

| Description             | Formula                                 |
|-------------------------|-----------------------------------------|
| NI_Margin_Ratio         | (NetIncomeLoss / Revenues) * 100        |

**補充說明:** formula的會計項目名稱需參照會計科目表欲抓取的會計項目。

## 參、操作方式說明

### 1. 新增分析標的 (Adding a New Target Company)

#### a. US Company (美國公司)

1. **Find the company on EDGAR:**
   - 搜尋公司（例如：Accenture），使用其完整名稱。
   - 確保公司名稱全為大寫。

   [EDGAR Search](https://www.sec.gov/edgar/search/)

2. **Determine the fiscal year start month:**
   - Browse filing types並將格式設為10-K。
   - 查看"Reporting for"欄，若結束於8/31，則會計年度起始月份為9月。

#### b. Indian Company (印度公司)

1. **Find the company on NSE:**
   - 搜尋公司（例如：Infosys Limited）。
   - 選擇"Annual"（年報）作為Period Ended。
   - 搜尋欄中的公司名稱須完全一致（例如：Infosys Limited）。

   [NSE Corporate Filings](https://www.nseindia.com/companies-listing/corporate-filings-financial-results)

2. **Determine the fiscal year start month:**
   - 從Period Ended欄可得知會計年度起始月份（例如：Infosys的起始月份為4月）。

3. **Download the financial reports:**
   - 右鍵點選XBRL檔案連結，將其保存為`Company Name_Year.xml`（例如：Infosys Limited_2024.xml）。

4. **Organize the XML data:**
   - 創建資料夾`XML_data`。
   - 在`XML_data`內為每家公司創建一個資料夾，使用公司全名。
   - 將各公司的XML檔案保存到各自的資料夾內。

### 2. 新增會計科目表 (Add Account Mapping)

1. **Find and add the company's account names:**
   - 尋找公司的財務報表。
   - 確認會計項目名稱並新增到會計科目表中。

### 3. 產出 rawdata (Generate Raw Data)

#### a. US Company (美國公司)

1. **Run `download_and_extract.py`**:
   - 產生`rawdata`資料夾，包含所有資料源。

2. **Run `US_rawdata.py`**:
   - 產生`US_rawdata.csv`。

#### b. Indian Company (印度公司)

1. **Run `India_rawdata.py`**:
   - 產生`India_rawdata.csv`。

2. **Check exchange rates in `India_rawdata.py`**:
   - 確認所有會計年度的匯率資料是否存在。
   - 新增缺少的匯率資料（例如：`2025: 匯率數字`）。

### 4. 產出 Processed_data (Generate Processed Data)

1. **Run `資料串接.py`**:
   - 產生`processed_data.csv`，包含一致化的財務指標及調整後的會計年度。

### 5. 產出 Final_data (Generate Final Data)

1. **Run `finalized.py`**:
   - 產生`Final_data`。
   - 將`Final_data`匯入PowerBI進行進一步分析。
