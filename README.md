# Individual Sales Automation

This project automates the processing and aggregation of stylist sales data exported from Wessconnect. It converts raw transaction logs into an organized pivot-style summary report for easy analysis.

## Features

- **Multi-Format Parsing**: Supports both "Employee Received Detail" and "Employee Service Detail" CSV exports.
- **Departmental Grouping**: Automatically categorizes stylists into specific departments:
  - **HS** (Hair Stylists)
  - **Nails**
  - **L&A** (Lash & Aesthetic)
- **Metric Aggregation**: Summarizes sales into distinct categories:
  - Package Sales
  - Product Sales
  - A la carte Sales
  - Deductions
- **Data Integrity**: 
  - Handles negative values by clipping them to RM 0.00.
  - Correctly maps aliases (e.g., mapping "Nicky" to "Yin Voon Hao").
  - Dynamically extracts the report month from the input data.

## Setup

1. **Prerequisites**: Ensure you have Python 3.8+ installed.
2. **Virtual Environment**:
   ```powershell
   python -m venv .venv
   .venv\Scripts\activate
   ```
3. **Dependencies**:
   Currently, the project uses Python's standard libraries. If external dependencies are added later, install them via:
   ```powershell
   pip install -r requirements.txt
   ```

## Usage

1. **Prepare Inputs**: Place your raw Wessconnect CSV exports in the `input/` directory.
2. **Run the Script**:
   ```powershell
   python main.py
   ```
3. **View Results**: The processed report will be saved as `output/stylist_sales_pivot.csv`.

### One-Click Option for Non-Technical Users (Windows)

1. Put all CSV exports into the `input/` folder.
2. Double-click `Run Report.bat` in the project root.
3. Wait for the success message.
4. Open `output/stylist_sales_pivot.csv`.

If Python is not installed, the runner will show a message with the download link.

## Project Structure

- `main.py`: The entry point of the application; handles file processing and report generation.
- `sales_utils.py`: Contains logic for data parsing, stylist management, and grouping configurations.
- `input/`: Directory for raw CSV files (ignored by Git).
- `output/`: Directory for generated reports (ignored by Git).
- `.venv/`: Python virtual environment (ignored by Git).
