import csv
from datetime import datetime

# CSV Column Indices
# CSV Column Indices are no longer static constants because the layout varies between reports.
# They are determined dynamically inside parse_sales_row.

STYLIST_GROUPS = {
    'HS': [
        'Nick', 'Sven', 'Yin Voon Hao', 'Steve', 'Phillip', 'Hellen', 'Tyra', 'Nicholas', 'Mayble', 
        'Kenny', 'Jade', 'Wei Xin', 'Kelvin', 'Gino', 'Moon', 'Daniel', 'Ella', 'Sedra', 'Rain', 'Carmen'
    ],
    'Nails': [
        'JEE', 'JESSY', 'ROI ROI', 'GRACE', 'JAY', 'JINGWEN', 'AGNES', 'Sharon'
    ],
    'L&A': [
        'DAISY', 'ALICE', 'YY', 'MOEMOE', 'WINNIE', 'NINI', 'ANGELA', 'JESSIE', 'NAOMI'
    ]
}

class StylistManager:
    def __init__(self, groups):
        self.groups = groups
        self.lookup = self._build_lookup()

    def _build_lookup(self):
        lookup = {}
        for dept, stylists in self.groups.items():
            for s in stylists:
                # Store the cleaned name as the key
                clean_name = self._clean(s)
                lookup[clean_name] = (dept, s)
        return lookup

    def _clean(self, name):
        return name.lower().replace(" ", "")

    def get_info(self, raw_name):
        if not raw_name:
            return 'Other', 'Unknown'
            
        clean_raw = self._clean(raw_name)

        # Specific alias check (as seen in original code)
        if 'nicky' in clean_raw:
            return 'HS', 'Yin Voon Hao'

        # Check for direct matches in our lookup, longest names first to avoid substring conflicts
        sorted_lookup = sorted(self.lookup.items(), key=lambda x: len(x[0]), reverse=True)
        for clean_target, (dept, original_name) in sorted_lookup:
            if clean_target in clean_raw:
                return dept, original_name
        
        return 'Other', raw_name.strip()

def parse_sales_row(row):
    """Parses a single CSV row and returns a dictionary of data."""
    try:
        is_service_detail = False
        qty_val = None
        sale_type_code = None

        if len(row) == 15:
            # Format 1: Employee Received Detail (Split Columns)
            # Columns: #, Date, Reference No., Employee, Customer, Item Code, Item Name, Type, Qty, Total, Received, Tax, Charge, Nett, Deduction
            date_str = row[1]
            item_name = row[6]
            sale_type_code = row[7]
            qty_val = float(row[8])
            nett_val = float(row[13])
            deduction_val = float(row[14])

        elif len(row) == 14:
            # Check if row[0] is Date or Index.
            # Format 2 (Service Detail, Split Columns) starts with Date: e.g. "10-07-2026 10:55 AM"
            # Format 1 (Received Detail, Combined Column) starts with index: e.g. "1" or ""
            is_service = False
            if row[0] and row[0].strip() and row[0].strip()[0].isdigit() and '-' in row[0]:
                is_service = True
            
            if is_service:
                # Format 2: Employee Service Detail (Split Columns)
                # Columns: Date, Reference No., Employee, Customer, Item Code, Item Name, Section, Category, Prepaid, FOC, Qty, Duration (Mins), Value, Actual Value
                date_str = row[0]
                item_name = row[5]
                qty_val = float(row[10])
                nett_val = float(row[12])
                deduction_val = float(row[13])
                is_service_detail = True
            else:
                # Format 1: Employee Received Detail (Combined Column)
                # Columns: #, Date, Reference No., Employee, Customer, Item, Type, Qty, Total, Received, Tax, Charge, Nett, Deduction
                date_str = row[1]
                item_name = row[5]
                sale_type_code = row[6]
                qty_val = float(row[7])
                nett_val = float(row[12])
                deduction_val = float(row[13])

        elif len(row) == 13:
            # Format 2: Employee Service Detail (Combined Column)
            # Columns: Date, Reference No., Employee, Customer, Item, Section, Category, Prepaid, FOC, Qty, Duration (Mins), Value, Actual Value
            date_str = row[0]
            item_name = row[4]
            qty_val = float(row[9])
            nett_val = float(row[11])
            deduction_val = float(row[12])
            is_service_detail = True

        else:
            return None

        # Parse date
        try:
            date_obj = datetime.strptime(date_str.strip(), "%d-%m-%Y %I:%M %p")
        except ValueError:
            return None

        # Determine category
        category = None
        if not is_service_detail:
            item_lower = item_name.lower()
            if sale_type_code == 'S':
                category = 'A la carte sales'
            elif sale_type_code == 'P':
                category = 'Product sales'
            elif sale_type_code in ['G', 'C']:
                if 'promo' in item_lower:
                    category = None
                elif nett_val < 0:
                    category = 'A la carte sales'
                else:
                    category = 'Package sales'
        else:
            category = 'A la carte sales'
        
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


