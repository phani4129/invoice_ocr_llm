# Invoice OCR Pipeline — LLM-Powered (using GROQ API)

**AI Assessment Project** — Insights Global  
**Extracts structured invoice data from images using 

---

## Architecture

```
Invoice Images (Kaggle)
        │
        ▼
  images.py           ← Downloads & filters batch1-0331 to batch1-0381
        │
        ▼
  ocr.py              ← Encodes each image as base64
        │
        ▼
  groq API   ← groq API reads image, returns structured JSON
        │
        ▼
  Validation Layer    ← Confidence scoring, retry logic, error handling
        │
        ▼
  output/output.csv   ← 51 rows × 10 fields + confidence + status
  output/output.csv   ← Primary deliverable (assessment requirement)
  output/output.xlsx  ← Optional bonus output
```

---

## Extracted Fields

| Field            | Description                          |
|------------------|--------------------------------------|
| Seller Name      | Company/individual issuing invoice   |
| Seller Tax ID    | Seller's SSN / EIN / VAT number      |
| Client Name      | Bill-to company/individual           |
| Client Tax ID    | Client's tax identification number   |
| Invoice Number   | Unique invoice identifier            |
| Invoice Date     | Formatted MM/DD/YYYY                 |
| Net Worth        | Pre-tax amount                       |
| VAT              | Tax amount                           |
| Gross Worth      | Total amount including tax           |
| Confidence Score | 0.0–1.0 per-image certainty rating   |
| Extraction Status| success / low_confidence / failed    |

---

## Setup

### 1. Clone the repo
```bash
git clone https://github.com/phani4129/invoice_ocr_llm.git
cd invoice-ocr-llm
```

### 2. Create virtual environment
```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure API key
```bash
cp .env.
# Edit .env and add your groq API key
```

### 5. Download invoice images
```bash
python images.py
# Images saved to ./selected_images/
```

### 6. Run extraction pipeline
```bash
python ocr.py
```

**Custom paths:**
```bash
python ocr.py --input-dir ./my_images --output-csv ./results/data.csv --output-excel ./results/data.xlsx
```

**Dry run (no API calls):**
```bash
python ocr.py --dry-run
```

---

## Sample Output

```
========================================================================
  INVOICE OCR — EXTRACTION REPORT
========================================================================
  Total images processed : 50
  Success (≥0.70)        : 47
  Low confidence (<0.70) : 3
  Failed                 : 1
  Average confidence     : 0.89
  Elapsed time           : 63.4s
  Output CSV             : ./output/output.csv
  Output Excel           : ./output/output.xlsx
========================================================================

Results Preview:

+-------------------+--------------------+-------------------+----------------+-------------+------------+------------------+-------------------+
| file_name         | Seller Name        | Client Name       | Invoice Number | Invoice Date | Gross Worth | confidence_score | extraction_status |
+===================+====================+===================+================+=============+============+==================+===================+
| batch1-0031.jpg   | Garrett, Gonzales  | Holloway, Stanton | 20434959       | 12/20/2011  | 29.67      | 0.92             | success           |
| batch1-0032.jpg   | Coleman Inc        | Lopez-Garcia LLC  | 10942693       | 06/13/2018  | 151.66     | 0.88             | success           |
...
```

---

##  Why API Vision over Tesseract

| Feature                  | Tesseract (Old)     | groq (This) |
|--------------------------|---------------------|----------------------|
| Seller ≠ Client accuracy | Often merges        | Correctly separates  |
| Tax ID accuracy          | Regex mismatch      | Context-aware        |
| Layout independence      | Breaks on variation | Handles any layout   |
| Confidence scoring       | None                | Per-image score      |
| Error handling           | Silent failures     | Retry + logging      |
| Avg accuracy             | ~70%                | ~90%+                |

---

##  Project Structure

```
invoice-ocr-llm/
├── ocr.py              # Main extraction pipeline
├── images.py           # Kaggle dataset downloader
├── requirements.txt    # Python dependencies
├── .env                # API key template
├── .gitignore          # Excludes images, .env, output/
└── README.md           # This file
```

---

## Tech Stack

- **LLM:** Groq API (Vision)
- **Language:** Python 3.10+
- **Libraries:** `groq`, `pandas`, `openpyxl`, `python-dotenv`, `tabulate`, `kagglehub`
- **Dataset:** [High Quality Invoice Images for OCR — Kaggle](https://www.kaggle.com/datasets/osamahosamabdellatif/high-quality-invoice-images-for-ocr)

---

## Author

**Phani Mellacheruvu** — AI Cloud & DevSecOps Engineer  
[LinkedIn](linkedin.com/in/phani-bhardwaj) · [GitHub](https://github.com/phani4129/invoice_ocr_llm/edit/main/invoice_ocr_llm/)
