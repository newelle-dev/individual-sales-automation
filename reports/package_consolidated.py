import csv
import glob
import os
import sys
from collections import defaultdict

# Ensure project root is on sys.path so imports work when running this file directly
ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from sales_utils import DEPT_HS, STYLIST_GROUPS, StylistManager, iter_sales_records

QTY_EXCLUDED_CODES = {'RBD', 'RM10', 'RM50', 'C01044', 'CP07'}

INPUT_DIR = os.path.join(os.path.dirname(__file__), "input")
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "output", "package_consolidated_by_group.csv")


def process_package_totals(input_dir: str = INPUT_DIR, output_file: str = OUTPUT_FILE) -> None:
    """
    Processes CSV records and generates a monthly consolidated Package report for the HS department,
    separating Credit Packages ('C') and Treatment Packages ('G') per stylist.
    """
    csv_files = glob.glob(os.path.join(input_dir, "*.csv"))
    if not csv_files:
        print(f"[ERROR] No CSV files found in input directory '{input_dir}'")
        sys.exit(1)

    # Structure: month_key -> stylist -> metrics dict
    month_data = defaultdict(lambda: defaultdict(lambda: {
        'credit_qty': 0,
        'credit_sales': 0.0,
        'treatment_qty': 0,
        'treatment_sales': 0.0
    }))

    # Store datetime per month key for chronological sorting
    month_sort_keys = {}
    stylist_manager = StylistManager(STYLIST_GROUPS)
    record_count = 0

    for current_stylist, parsed in iter_sales_records(input_dir):
        dept, short_name = stylist_manager.get_info(current_stylist)
        if dept != DEPT_HS:
            continue

        sale_type = parsed.get('sale_type')
        if not sale_type or sale_type.strip().upper() not in {'C', 'G'}:
            continue

        qty = parsed.get('qty')
        # Exclude reversed/void entries (<= 0)
        if qty is None or qty <= 0:
            continue

        dt = parsed.get('date')
        if not dt:
            continue

        month_str = dt.strftime('%B %Y').upper()
        sort_key = (dt.year, dt.month)
        month_sort_keys[month_str] = sort_key

        sale_type_code = sale_type.strip().upper()
        sales_val = max(0.0, parsed.get('nett', 0.0))
        raw_item_name = parsed.get('item_name', '').strip()

        # Exclude specified vouchers/redemptions from Qty calculation
        item_code = raw_item_name.split(':')[0].strip().upper()
        add_qty = qty if item_code not in QTY_EXCLUDED_CODES else 0

        if sale_type_code == 'C':
            month_data[month_str][short_name]['credit_qty'] += add_qty
            month_data[month_str][short_name]['credit_sales'] += sales_val
        elif sale_type_code == 'G':
            month_data[month_str][short_name]['treatment_qty'] += add_qty
            month_data[month_str][short_name]['treatment_sales'] += sales_val

        record_count += 1

    # Ensure all HS stylists are present for each month recorded
    hs_stylists = STYLIST_GROUPS.get(DEPT_HS, [])
    for month_str in month_data:
        for s in hs_stylists:
            if s not in month_data[month_str]:
                month_data[month_str][s] = {
                    'credit_qty': 0,
                    'credit_sales': 0.0,
                    'treatment_qty': 0,
                    'treatment_sales': 0.0
                }

    # Sort months chronologically
    sorted_months = sorted(month_data.keys(), key=lambda m: month_sort_keys.get(m, (0, 0)))

    # Write CSV output
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    try:
        with open(output_file, mode='w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)

            writer.writerow(["HS DEPARTMENT MONTHLY PACKAGE REPORT - TOP 7 (CREDIT vs TREATMENT)"])

            grand_credit_qty = 0
            grand_credit_sales = 0.0
            grand_treatment_qty = 0
            grand_treatment_sales = 0.0

            for month_str in sorted_months:
                stylists_dict = month_data[month_str]

                # Sort stylists by total sales desc, then name asc, and take Top 7
                sorted_stylists = sorted(
                    stylists_dict.items(),
                    key=lambda x: (x[1]['credit_sales'] + x[1]['treatment_sales'], x[0]),
                    reverse=True
                )[:7]

                writer.writerow([])
                writer.writerow([f"Month: {month_str} (Department: HS - Top 7)"])
                writer.writerow([
                    "Rank", "Employee",
                    "Credit Pkg Qty", "Credit Pkg Sales (RM)",
                    "Treatment Pkg Qty", "Treatment Pkg Sales (RM)",
                    "Total Qty", "Total Sales (RM)"
                ])

                rank = 1
                month_credit_qty = 0
                month_credit_sales = 0.0
                month_treatment_qty = 0
                month_treatment_sales = 0.0

                for name, vals in sorted_stylists:
                    cq = vals['credit_qty']
                    cs = vals['credit_sales']
                    tq = vals['treatment_qty']
                    ts = vals['treatment_sales']
                    tot_q = cq + tq
                    tot_s = cs + ts

                    writer.writerow([
                        rank,
                        name,
                        int(cq) if isinstance(cq, float) and cq.is_integer() else cq,
                        f"RM{cs:.2f}",
                        int(tq) if isinstance(tq, float) and tq.is_integer() else tq,
                        f"RM{ts:.2f}",
                        int(tot_q) if isinstance(tot_q, float) and tot_q.is_integer() else tot_q,
                        f"RM{tot_s:.2f}"
                    ])

                    month_credit_qty += cq
                    month_credit_sales += cs
                    month_treatment_qty += tq
                    month_treatment_sales += ts
                    rank += 1

                month_tot_qty = month_credit_qty + month_treatment_qty
                month_tot_sales = month_credit_sales + month_treatment_sales

                grand_credit_qty += month_credit_qty
                grand_credit_sales += month_credit_sales
                grand_treatment_qty += month_treatment_qty
                grand_treatment_sales += month_treatment_sales

                # Month-level totals
                writer.writerow([])
                writer.writerow([f"Totals ({month_str} - Top 7)"])
                writer.writerow([
                    "Total", "Top 7 HS Stylists",
                    int(month_credit_qty) if isinstance(month_credit_qty, float) and month_credit_qty.is_integer() else month_credit_qty,
                    f"RM{month_credit_sales:.2f}",
                    int(month_treatment_qty) if isinstance(month_treatment_qty, float) and month_treatment_qty.is_integer() else month_treatment_qty,
                    f"RM{month_treatment_sales:.2f}",
                    int(month_tot_qty) if isinstance(month_tot_qty, float) and month_tot_qty.is_integer() else month_tot_qty,
                    f"RM{month_tot_sales:.2f}"
                ])

            # Grand combined totals across all months (if multiple)
            if len(sorted_months) > 1:
                grand_tot_qty = grand_credit_qty + grand_treatment_qty
                grand_tot_sales = grand_credit_sales + grand_treatment_sales
                writer.writerow([])
                writer.writerow(["Grand Totals (All Months)"])
                writer.writerow([
                    "Total", "Combined",
                    int(grand_credit_qty) if isinstance(grand_credit_qty, float) and grand_credit_qty.is_integer() else grand_credit_qty,
                    f"RM{grand_credit_sales:.2f}",
                    int(grand_treatment_qty) if isinstance(grand_treatment_qty, float) and grand_treatment_qty.is_integer() else grand_treatment_qty,
                    f"RM{grand_treatment_sales:.2f}",
                    int(grand_tot_qty) if isinstance(grand_tot_qty, float) and grand_tot_qty.is_integer() else grand_tot_qty,
                    f"RM{grand_tot_sales:.2f}"
                ])

    except PermissionError:
        print(f"\n[ERROR] Permission denied when writing to '{output_file}'.")
        print("Please close the file in Microsoft Excel or any other program and try again.\n")
        sys.exit(1)

    print(f"Package consolidated report written to {output_file} ({record_count} HS package items parsed).")


if __name__ == '__main__':
    # Usage: py reports\package_consolidated.py [input_dir] [output_file]
    in_dir = INPUT_DIR
    out_file = OUTPUT_FILE
    if len(sys.argv) >= 2:
        in_dir = sys.argv[1]
    if len(sys.argv) >= 3:
        out_file = sys.argv[2]

    process_package_totals(input_dir=in_dir, output_file=out_file)

