"""
sales_utils.py

Core utility module for parsing Wessconnect CSV export reports, categorizing transaction
types, and managing stylist department mappings.

Complies with rules in /context/sales-rules.md and /context/code-standards.md.
"""

import csv
import glob
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any, Generator

# ==============================================================================
# Category & Department Constants
# ==============================================================================
CAT_ALACARTE = 'A la carte sales'
CAT_PRODUCT = 'Product sales'
CAT_PACKAGE = 'Package sales'

DEPT_HS = 'HS'
DEPT_NAILS = 'Nails'
DEPT_LA = 'L&A'
DEPT_OTHER = 'Other'

# Default Canonical Stylist Department Definitions
STYLIST_GROUPS: Dict[str, List[str]] = {
    DEPT_HS: [
        'Nick', 'Sven', 'Yin Voon Hao', 'Steve', 'Phillip', 'Hellen', 'Tyra', 'Nicholas', 'Mayble', 
        'Kenny', 'Jade', 'Wei Xin', 'Kelvin', 'Gino', 'Moon', 'Daniel', 'Ella', 'Sedra', 'Rain', 'Carmen',
        'Maw Maw', 'William', 'Negin', 'Yuri', 'Zom'
    ],
    DEPT_NAILS: [
        'JEE', 'JESSY', 'ROI ROI', 'GRACE', 'JAY', 'JINGWEN', 'AGNES', 'Sharon', 'Ying'
    ],
    DEPT_LA: [
        'DAISY', 'ALICE', 'YY', 'MOEMOE', 'WINNIE', 'NINI', 'ANGELA', 'JESSIE', 'NAOMI'
    ]
}

# Known name aliases mapping cleaned string -> (Department, Canonical Name)
DEFAULT_ALIASES: Dict[str, Tuple[str, str]] = {
    'nicky': (DEPT_HS, 'Yin Voon Hao'),
    'yin(seniormanicurist)': (DEPT_NAILS, 'Ying'),
}

# Supported Date Format Patterns for Wessconnect exports
DATE_FORMATS: Tuple[str, ...] = (
    "%d-%m-%Y %I:%M %p",
    "%d/%m/%Y %I:%M %p",
    "%d-%m-%Y %H:%M",
    "%d/%m/%Y %H:%M",
    "%Y-%m-%d %H:%M:%S",
)


# ==============================================================================
# Stylist Lookup & Management Class
# ==============================================================================
class StylistManager:
    """
    Manages normalization and resolution of raw employee names into canonical
    stylist names and department groupings.
    """

    def __init__(
        self,
        groups: Dict[str, List[str]] = STYLIST_GROUPS,
        aliases: Optional[Dict[str, Tuple[str, str]]] = None
    ) -> None:
        self.groups = groups
        self.aliases = aliases if aliases is not None else DEFAULT_ALIASES
        self.lookup: Dict[str, Tuple[str, str]] = self._build_lookup()
        # Pre-sort lookup items by cleaned key length descending for O(1) loop execution
        self.sorted_lookup: List[Tuple[str, Tuple[str, str]]] = sorted(
            self.lookup.items(), key=lambda x: len(x[0]), reverse=True
        )

    def _build_lookup(self) -> Dict[str, Tuple[str, str]]:
        """Builds normalized exact lookup dictionary mapping clean_name -> (dept, original_name)."""
        lookup = {}
        for dept, stylists in self.groups.items():
            for s in stylists:
                clean_name = self._clean(s)
                lookup[clean_name] = (dept, s)
        return lookup

    @staticmethod
    def _clean(name: str) -> str:
        """Strips all whitespace characters and converts string to lowercase."""
        if not name:
            return ""
        return "".join(name.split()).lower()

    def get_info(self, raw_name: Optional[str]) -> Tuple[str, str]:
        """
        Resolves raw employee name into (Department, Canonical Stylist Name).

        Returns:
            Tuple[str, str]: (Department Code, Canonical/Raw Name)
        """
        if not raw_name or not raw_name.strip():
            return DEPT_OTHER, 'Unknown'

        clean_raw = self._clean(raw_name)

        # 1. Specific Alias Check
        for alias_key, result in self.aliases.items():
            if alias_key in clean_raw:
                return result

        # 2. Fast O(1) Direct Lookup Check
        if clean_raw in self.lookup:
            return self.lookup[clean_raw]

        # 3. Substring Check (Longest matching substring first)
        for clean_target, (dept, original_name) in self.sorted_lookup:
            if clean_target in clean_raw:
                return dept, original_name

        # 4. Fallback to Other department with cleaned raw name
        return DEPT_OTHER, raw_name.strip()


# ==============================================================================
# Safe Parsing Helper Functions
# ==============================================================================
def _safe_float(val: Any, default: float = 0.0) -> float:
    """Defensively parses float values from raw CSV cell strings."""
    if val is None:
        return default
    if isinstance(val, (int, float)):
        return float(val)

    s = str(val).strip()
    if not s:
        return default

    # Remove currency prefixes (RM/rm), spaces, and commas
    cleaned = s.replace("RM", "").replace("rm", "").replace(",", "").strip()
    try:
        return float(cleaned)
    except ValueError:
        return default


def _safe_parse_date(date_str: str) -> Optional[datetime]:
    """Tries parsing a date string using supported Wessconnect export formats."""
    if not date_str or not date_str.strip():
        return None

    cleaned = date_str.strip()
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(cleaned, fmt)
        except ValueError:
            continue
    return None


def _identify_row_layout(row: List[str]) -> Optional[Tuple[str, bool]]:
    """
    Identifies the CSV row layout type based on column count and date detection.

    Returns:
        Optional[Tuple[str, bool]]: (Layout Code, is_service_detail) or None if un-routable.
    """
    length = len(row)
    if length == 15:
        # Received Detail (Split Columns)
        return ("REC_SPLIT", False)
    elif length == 14:
        # Check if first column is date string (Service Detail) or index (Received Detail)
        first_cell = row[0].strip() if row[0] else ""
        is_service = bool(first_cell and first_cell[0].isdigit() and '-' in first_cell)
        if is_service:
            # Service Detail (Split Columns)
            return ("SERV_SPLIT", True)
        else:
            # Received Detail (Combined Column)
            return ("REC_COMBINED", False)
    elif length == 13:
        # Service Detail (Combined Column)
        return ("SERV_COMBINED", True)

    return None


def _categorize_sale(
    sale_type_code: Optional[str],
    item_name: str,
    nett_val: float,
    is_service_detail: bool
) -> Optional[str]:
    """Categorizes transaction into A la carte, Product, or Package sales."""
    if is_service_detail:
        return CAT_ALACARTE

    code = (sale_type_code or "").strip().upper()
    item_lower = item_name.lower()

    if code == 'S':
        return CAT_ALACARTE
    elif code == 'P':
        return CAT_PRODUCT
    elif code in ('G', 'C'):
        # Check promo or negative net transaction exceptions
        is_promo = 'makeover' in item_lower or ('promo' in item_lower and 'cny promo' not in item_lower)
        if is_promo or nett_val < 0:
            return CAT_ALACARTE
        return CAT_PACKAGE

    return None


# ==============================================================================
# Core Parsing & Ingestion Generator
# ==============================================================================
def parse_sales_row(row: List[str]) -> Optional[Dict[str, Any]]:
    """
    Parses a single CSV row and returns a structured dictionary of extracted transaction data.

    Returns:
        Optional[Dict[str, Any]]: Dict containing date, item_name, sale_type, category,
                                  nett, deduction, qty, and is_service_detail. Returns
                                  None if row length/format is invalid or date parsing fails.
    """
    if not row or not isinstance(row, list):
        return None

    layout_info = _identify_row_layout(row)
    if not layout_info:
        return None

    layout_code, is_service_detail = layout_info

    try:
        # Extract raw cell values according to layout mapping
        if layout_code == "REC_SPLIT":
            date_str = row[1]
            item_name = row[6]
            sale_type_code = row[7]
            qty_val = _safe_float(row[8])
            nett_val = _safe_float(row[13])
            deduction_val = _safe_float(row[14])

        elif layout_code == "SERV_SPLIT":
            date_str = row[0]
            item_name = row[5]
            sale_type_code = None
            qty_val = _safe_float(row[10])
            nett_val = _safe_float(row[12])
            deduction_val = _safe_float(row[13])

        elif layout_code == "REC_COMBINED":
            date_str = row[1]
            item_name = row[5]
            sale_type_code = row[6]
            qty_val = _safe_float(row[7])
            nett_val = _safe_float(row[12])
            deduction_val = _safe_float(row[13])

        elif layout_code == "SERV_COMBINED":
            date_str = row[0]
            item_name = row[4]
            sale_type_code = None
            qty_val = _safe_float(row[9])
            nett_val = _safe_float(row[11])
            deduction_val = _safe_float(row[12])

        else:
            return None

        # Parse transaction date
        date_obj = _safe_parse_date(date_str)
        if not date_obj:
            return None

        # Determine sales category based on business logic
        category = _categorize_sale(sale_type_code, item_name, nett_val, is_service_detail)

        return {
            'date': date_obj,
            'item_name': item_name,
            'sale_type': sale_type_code,
            'category': category,
            'nett': nett_val,
            'deduction': deduction_val,
            'qty': qty_val,
            'is_service_detail': is_service_detail
        }
    except Exception:
        return None


def iter_sales_records(input_dir: str) -> Generator[Tuple[str, Dict[str, Any]], None, None]:
    """
    Iterates through all CSV files in input_dir and yields (stylist_name, parsed_record).
    Centralizes CSV reading, row filtering, header identification, and employee block tracking.
    """
    csv_files = glob.glob(os.path.join(input_dir, "*.csv"))
    if not csv_files:
        return

    for file_path in csv_files:
        with open(file_path, mode='r', encoding='utf-8-sig') as f:
            reader = csv.reader(f)
            current_stylist = None

            for row in reader:
                if not row or not any(row):
                    continue

                line_str = ",".join(row)
                if "Employee Received Detail" in line_str or "Employee Service Detail" in line_str or 'Grand Total' in line_str:
                    continue

                # Header check for employee name (single column or first cell non-empty with all remaining cells blank)
                if len(row) == 1 or (len(row) > 0 and row[0].strip() and not any(cell.strip() for cell in row[1:])):
                    potential_name = row[0].strip()
                    if potential_name and not potential_name.startswith('#'):
                        current_stylist = potential_name
                    continue

                # Skip header or total lines
                if row[0] == '#' or 'Total' in row or row[0] == 'Date':
                    continue

                parsed = parse_sales_row(row)
                if parsed and current_stylist:
                    yield current_stylist, parsed
