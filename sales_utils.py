import csv
from datetime import datetime

# CSV Column Indices
COL_DATE = 1
COL_ITEM = 5
COL_SALE_TYPE = 6
COL_NETT = 12
COL_DEDUCTION = 13

STYLIST_GROUPS = {
    'HS': [
        'Nick', 'Sven', 'Yin Voon Hao', 'Steve', 'Phillip', 'Hellen', 'Tyra', 'Nicholas', 'Mayble', 
        'Kenny', 'Jade', 'Wei Xin', 'Kelvin', 'Gino', 'Angel', 'Moon', 'Daniel', 'Ella', 'Sedra', 'Rain', 'Carmen'
    ],
    'Nails': [
        'JEE', 'EVELYN', 'JESSY', 'ROI ROI', 'GRACE', 'JAY', 'JINGWEN', 'AGNES', 'Kalpana', 'Sharon'
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
        
        # Keep Angel Assist rows in HS instead of matching Angela by substring.
        if 'angelassist' in clean_raw:
            return 'HS', 'Angel'

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
        if len(row) >= 14:
            # Format 1: Employee Received Detail
            date_str = row[COL_DATE]
            item_name = row[COL_ITEM]
            sale_type_code = row[COL_SALE_TYPE]
            try:
                nett_val = float(row[COL_NETT])
                deduction_val = float(row[COL_DEDUCTION])
            except ValueError:
                return None
        elif len(row) == 13:
            # Format 2: Employee Service Detail
            # Date(0), Ref(1), Emp(2), Cust(3), Item(4), Section(5), Cat(6), Prepaid(7), FOC(8), Qty(9), Dur(10), Val(11), Actual(12)
            date_str = row[0]
            item_name = row[4]
            sale_type_code = None # Not present in this format
            try:
                nett_val = float(row[11])
                deduction_val = float(row[12])
                qty_val = float(row[9])
            except ValueError:
                return None
            is_service_detail = True
        else:
            return None

        # Parse date
        try:
            date_obj = datetime.strptime(date_str, "%d-%m-%Y %I:%M %p")
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
            'category': category,
            'nett': nett_val,
            'deduction': deduction_val,
            'qty': qty_val,
            'is_service_detail': is_service_detail
        }
    except Exception:
        return None

