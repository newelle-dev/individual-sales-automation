# Code Quality, Architecture & User Experience Review

**Project**: Individual Sales Automation  
**Date**: August 2, 2026  
**Audience**: Salon Managers, Admin Staff, and Technical Developers  
**Scope**: `sales_utils.py`, `main.py`, `reports/package_consolidated.py`, `Run Report.bat`, `reports/run_report.bat`, `README.md`, `/context/` standards

---

## Executive Summary

A comprehensive architectural, performance, and user-experience code review was conducted across the **Individual Sales Automation** codebase. 

While the system successfully automates monthly Wessconnect CSV aggregation into pivot summary reports, the review identified several critical performance bottlenecks, error-handling gaps, logic duplication, and user experience friction points:
1. **Performance Bottleneck**: `sorted_lookup` is re-created and sorted inside `get_info()` on every row evaluation ($O(K \log K)$ sorting computation per row).
2. **Logic & Parsing Duplication**: File reading, header skipping, and employee block detection are duplicated across `main.py` and `reports/package_consolidated.py`, leading to a subtle bug when encountering whitespace-padded CSV rows.
3. **UX & Error Handling**: Missing input CSV files lead to false `[SUCCESS]` messages in `Run Report.bat`. Unhandled file locking (`PermissionError` when Excel holds the output CSV open) displays scary raw Python stack traces to non-technical staff.
4. **Silent Failure Risk**: Parsing exceptions are suppressed silently via top-level `except Exception: return None`, risking silent row drops.

---

## 1. Itemized Code Review & Analysis

### ⚡ Performance & Optimization (Preserving Same Behavior)

#### 🔴 1.1 Critical: Repeated List Sorting in Name Matching Loop
- **Location**: [`sales_utils.py:L49-50`](file:///C:/Users/alec/OneDrive/Desktop/alec176avenue/individual-sales-automation/sales_utils.py#L49-L50)
- **Issue**: `sorted_lookup = sorted(self.lookup.items(), key=lambda x: len(x[0]), reverse=True)` is executed inside `get_info()` on **every single transaction row**. For CSV exports containing thousands of rows, this creates redundant $O(K \log K)$ sorting computations and heap memory allocations per row.
- **Suggestion**: Pre-sort `self.lookup` once during `StylistManager.__init__()` and store it as a pre-built attribute `self.sorted_lookup`.

#### 🟠 1.2 Important: Missing $O(1)$ Direct Lookup Fast-Path
- **Location**: [`sales_utils.py:L48-52`](file:///C:/Users/alec/OneDrive/Desktop/alec176avenue/individual-sales-automation/sales_utils.py#L48-L52)
- **Issue**: Exact name matches (e.g., `"Nick"` -> `"nick"`) bypass direct dictionary lookup and immediately start linear substring iteration over all stylists.
- **Suggestion**: Perform a direct $O(1)$ key check (`if clean_raw in self.lookup: return self.lookup[clean_raw]`) before longest-substring matching.

#### 🟡 1.3 Suggestion: Deeply Nested `defaultdict` Structures
- **Location**: [`main.py:L9`](file:///C:/Users/alec/OneDrive/Desktop/alec176avenue/individual-sales-automation/main.py#L9)
- **Issue**: 4-deep nested `defaultdict` (`data[dept][category][day][short_name]`) risks auto-vivifying empty dictionaries during read operations.
- **Suggestion**: Replace with a composite key dictionary (`data[(dept, category, day, short_name)] += amount`) or explicit domain data structures.

---

### 🏗️ Code & Component Modular Structure

#### 🟠 2.1 Important: Duplicated File Ingestion & Row Filtering
- **Location**: [`main.py:L25-L55`](file:///C:/Users/alec/OneDrive/Desktop/alec176avenue/individual-sales-automation/main.py#L25-L55) vs [`reports/package_consolidated.py:L29-L56`](file:///C:/Users/alec/OneDrive/Desktop/alec176avenue/individual-sales-automation/reports/package_consolidated.py#L29-L56)
- **Issue**: Both scripts duplicate CSV reading, header filtering, and employee row tracking logic.
- **Divergence Bug**: In `main.py` L40, `not any(row[1:])` fails if trailing cells contain whitespace strings (e.g. `["NAME", "  "]`), whereas `package_consolidated.py` L43 correctly uses `cell.strip()`.
- **Suggestion**: Extract a unified generator function `iter_sales_records(input_dir)` in `sales_utils.py` to centralize row parsing.

#### 🟠 2.2 Important: Lack of 3-Tier Layering (Ingestion → Domain → Presentation)
- **Location**: [`main.py:L7-L144`](file:///C:/Users/alec/OneDrive/Desktop/alec176avenue/individual-sales-automation/main.py#L7-L144)
- **Issue**: `process_files` combines CSV file I/O, domain rules (makeover exceptions, quantity adjustments), matrix calculations, and CSV writing into a single monolithic 138-line function.
- **Suggestion**: Split into:
  1. **Ingestion**: `iter_sales_records(input_dir)`
  2. **Aggregation**: `aggregate_daily_sales(records)`
  3. **Presentation**: `write_sales_pivot_csv(data, output_file)`

---

### 🎨 UI, CLI & Accessibility (Batch UX & Future Web UI Roadmap)

#### 🔴 3.1 Critical: False Success Message on Empty Input Directory
- **Location**: [`Run Report.bat:L9-L15`](file:///C:/Users/alec/OneDrive/Desktop/alec176avenue/individual-sales-automation/Run%20Report.bat#L9-L15) & [`main.py:L95-L97`](file:///C:/Users/alec/OneDrive/Desktop/alec176avenue/individual-sales-automation/main.py#L95-L97)
- **Issue**: If `input/` contains no CSV files, `main.py` prints `"No data found to process."` and exits with code `0`. `Run Report.bat` then incorrectly displays `[SUCCESS] Report generated.` to non-technical users.
- **Suggestion**:
  - Update `Run Report.bat` to check `dir /b "input\*.csv"` before running Python.
  - Return exit code `1` in Python when no CSV files or valid data rows exist.

#### 🟠 3.2 Important: Unhandled Excel File Lock (`PermissionError`)
- **Location**: [`main.py:L103`](file:///C:/Users/alec/OneDrive/Desktop/alec176avenue/individual-sales-automation/main.py#L103)
- **Issue**: If a salon manager leaves `output/stylist_sales_pivot.csv` open in Excel and re-runs the batch script, Python crashes with a raw `PermissionError` traceback.
- **Suggestion**: Catch `PermissionError` and output a friendly message: `"ERROR: 'output/stylist_sales_pivot.csv' is open in Microsoft Excel. Please close it and try again."`

#### 🌐 3.3 Web / Desktop GUI Accessibility & UI Roadmap
If transitioning to a React / Next.js / Desktop Web interface:
1. **ARIA Live Regions**: Use `aria-live="polite"` on upload/parsing status indicators and `role="alert"` for error messages.
2. **Keyboard Accessible File Upload**: Ensure dropzone input uses visible focus rings (`focus-visible:ring-2`) and associated `<label htmlFor="csv-upload">`.
3. **Semantic HTML Table Structure**: Use proper `<thead>`, `<tbody>`, `scope="col"`, and `scope="row"` for pivot output tables to ensure screen reader compatibility.
4. **Interactive Data Table Components**: Split giant pivot views into collapsible Department components (`<HairStylistSection />`, `<NailsSection />`, `<LashAestheticSection />`).

---

### ⚠️ Error Handling & User Feedback

#### 🔴 4.1 Critical: Silent Exception Suppression in Parser
- **Location**: [`sales_utils.py:L147-L148`](file:///C:/Users/alec/OneDrive/Desktop/alec176avenue/individual-sales-automation/sales_utils.py#L147-L148)
- **Issue**: `try: ... except Exception: return None` silently drops un-parseable rows without diagnostic warnings or logs.
- **Suggestion**: Handle specific conversion exceptions (`ValueError`, `TypeError`) in defensive helper functions and log unparseable row warnings.

#### 🟠 4.2 Important: Un-defensive Numeric & Date Conversions
- **Location**: [`sales_utils.py:L69, L115`](file:///C:/Users/alec/OneDrive/Desktop/alec176avenue/individual-sales-automation/sales_utils.py#L69)
- **Issue**: `float(row[8])` crashes on currency prefixes (`"RM 50.00"`), empty strings, or commas (`"1,200.00"`). `strptime` fails if date separators switch between `-` and `/`.
- **Suggestion**: Implement `_safe_float()` (stripping `RM`, commas, spaces) and a multi-format `_safe_parse_date()` helper.

---

### 🧠 Business Logic Separation

#### 🟠 5.1 Important: Intermingled CSV Layout Parsing
- **Location**: [`sales_utils.py:L63-L110`](file:///C:/Users/alec/OneDrive/Desktop/alec176avenue/individual-sales-automation/sales_utils.py#L63-L110)
- **Issue**: CSV column layout detection (15, 14, 13 column variants across Received and Service Detail reports) is directly mixed into value extraction.
- **Suggestion**: Extract layout detection into a dedicated helper `_identify_row_layout(row: List[str])`.

#### 🟡 5.2 Suggestion: Redundant Promotion Clause
- **Location**: [`sales_utils.py:L128`](file:///C:/Users/alec/OneDrive/Desktop/alec176avenue/individual-sales-automation/sales_utils.py#L128)
- **Issue**: `'nail promo' in item_lower` is redundant because `'nail promo'` is already captured by `('promo' in item_lower and 'cny promo' not in item_lower)`.
- **Suggestion**: Clean condition to `'makeover' in item_lower or ('promo' in item_lower and 'cny promo' not in item_lower)`.

---

### 📝 Comments, Documentation & Standards

#### 🟠 6.1 Important: Virtual Environment (`.venv`) Ignored by Batch Scripts
- **Location**: [`Run Report.bat:L19-L38`](file:///C:/Users/alec/OneDrive/Desktop/alec176avenue/individual-sales-automation/Run%20Report.bat#L19-L38) vs [`README.md:L25-L29`](file:///C:/Users/alec/OneDrive/Desktop/alec176avenue/individual-sales-automation/README.md#L25-L29)
- **Issue**: `README.md` documents `.venv` creation, but `Run Report.bat` skips checking for `.venv\Scripts\python.exe` and directly invokes system `py`/`python`.
- **Suggestion**: Check for `.venv\Scripts\python.exe` first in batch scripts.

#### 🟡 6.2 Suggestion: Missing Type Annotations & PEP 257 Docstrings
- **Location**: [`sales_utils.py`](file:///C:/Users/alec/OneDrive/Desktop/alec176avenue/individual-sales-automation/sales_utils.py), [`main.py`](file:///C:/Users/alec/OneDrive/Desktop/alec176avenue/individual-sales-automation/main.py)
- **Issue**: Functions lack type hints (`Optional[str]`, `Dict[str, Any]`) and detailed docstrings specifying parameters and return contracts.

---

### 🧹 Clean Code & Removal of Unused Code

#### 💡 7.1 Nitpick: Unused Imports
- **Location**: [`sales_utils.py:L1`](file:///C:/Users/alec/OneDrive/Desktop/alec176avenue/individual-sales-automation/sales_utils.py#L1) (`import csv` is unused)
- **Location**: [`reports/package_consolidated.py:L5, L133`](file:///C:/Users/alec/OneDrive/Desktop/alec176avenue/individual-sales-automation/reports/package_consolidated.py#L5) (`OrderedDict` is unused, `import sys` imported twice).

---

## 2. Actionable Improvement & Priority Matrix

| Priority | File / Component | Recommendation | Expected Impact |
| :--- | :--- | :--- | :--- |
| 🔴 **P0** | [`sales_utils.py`](file:///C:/Users/alec/OneDrive/Desktop/alec176avenue/individual-sales-automation/sales_utils.py) | Pre-sort lookup items in `StylistManager.__init__` and add $O(1)$ direct dict lookup check before substring loop. | Replaces $O(K \log K)$ sorting per row with $O(1)$ operations; boosts parsing speed. |
| 🔴 **P0** | [`sales_utils.py`](file:///C:/Users/alec/OneDrive/Desktop/alec176avenue/individual-sales-automation/sales_utils.py) | Remove bare `except Exception`, add `_safe_float()` and `_safe_parse_date()` helpers. | Prevents silent data loss and handles messy currency strings/date formats. |
| 🔴 **P0** | [`Run Report.bat`](file:///C:/Users/alec/OneDrive/Desktop/alec176avenue/individual-sales-automation/Run%20Report.bat) / `main.py` | Add `.csv` existence checks before running Python and exit with status code `1` on missing data. | Eliminates false success messages on empty input folders. |
| 🟠 **P1** | [`main.py`](file:///C:/Users/alec/OneDrive/Desktop/alec176avenue/individual-sales-automation/main.py) / `sales_utils.py` | Centralize CSV row iteration (`iter_sales_records`) in `sales_utils.py` to share across `main.py` and `package_consolidated.py`. | Fixes whitespace string parsing bug and eliminates code duplication. |
| 🟠 **P1** | [`main.py`](file:///C:/Users/alec/OneDrive/Desktop/alec176avenue/individual-sales-automation/main.py) | Wrap output writing in `try...except PermissionError` with user-friendly instructions. | Prevents ugly Python tracebacks when Excel locks the output CSV file. |
| 🟠 **P1** | [`Run Report.bat`](file:///C:/Users/alec/OneDrive/Desktop/alec176avenue/individual-sales-automation/Run%20Report.bat) | Detect and prioritize `.venv\Scripts\python.exe` execution. | Aligns batch runners with `README.md` virtual environment documentation. |
| 🟡 **P2** | Entire Codebase | Add Python type annotations, PEP 257 docstrings, and clean unused imports (`import csv`, `OrderedDict`). | Improves maintainability and developer experience. |
