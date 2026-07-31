# Code Standards & Guidelines

To ensure the project remains simple, readable, and easy to maintain by non-technical users and future developers, all contributions must adhere to these standards.

## Python Coding Style

- **Python Version**: Python 3.8+ compatibility.
- **Style Compliance**: Follow standard Python conventions (PEP 8) for naming and styling:
  - Functions & Variables: `snake_case` (e.g., `parse_sales_row`, `nett_val`).
  - Classes: `PascalCase` (e.g., `StylistManager`).
  - Constants: `UPPER_SNAKE_CASE` (e.g., `STYLIST_GROUPS`).
- **Standard Library First**: Prioritize built-in packages (`csv`, `os`, `glob`, `datetime`, `collections`) unless a clear need arises for external libraries (like `pandas` or `openpyxl`). If external dependencies are added, they must be registered in `requirements.txt`.

## File Operations & File Formats

- **File Encoding**: Always open files using explicit `encoding='utf-8'` configuration to prevent OS-specific character encoding bugs (such as Windows' default CP1252 parsing).
- **Newline Handling**: When writing CSVs using `csv.writer`, specify `newline=''` in the `open` call to prevent empty/double-spaced rows on Windows platforms.
- **Directory Verification**: Always check and create output directories (`os.makedirs(..., exist_ok=True)`) before writing files.

## Error Handling & Robustness

- **Graceful Failures**: CSV files exported from external software are prone to format shifts, missing headers, or trailing empty lines. Implement defensive programming in parsers. Use `try-except` blocks to handle formatting anomalies without crashing the whole program.
- **Empty Rows**: Explicitly filter out blank rows or total/header-only rows before sending data downstream.
- **Validation**: Validate date parsing and type casting (e.g., converting strings to floats for currencies) before inserting into aggregation engines.
