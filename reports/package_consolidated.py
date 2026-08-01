import csv
import glob
import os
import sys
from collections import defaultdict

# Ensure project root is on sys.path so imports work when running this file directly
ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from sales_utils import STYLIST_GROUPS, StylistManager, iter_sales_records

QTY_EXCLUDED_CODES = {'RBD', 'RM10', 'RM50', 'C01044', 'CP07'}

INPUT_DIR = os.path.join(os.path.dirname(__file__), "input")
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "output", "package_consolidated_by_group.csv")


def process_package_totals(input_dir: str = INPUT_DIR, output_file: str = OUTPUT_FILE) -> None:
    """
    Processes CSV records and generates a consolidated Package + Coupon sales report.
    """
    csv_files = glob.glob(os.path.join(input_dir, "*.csv"))
    if not csv_files:
        print(f"[ERROR] No CSV files found in input directory '{input_dir}'")
        sys.exit(1)

    totals = defaultdict(lambda: defaultdict(lambda: {'qty': 0, 'sales': 0.0}))
    stylist_manager = StylistManager(STYLIST_GROUPS)
    record_count = 0

    for current_stylist, parsed in iter_sales_records(input_dir):
        sale_type = parsed.get('sale_type')
        if not sale_type or sale_type.strip().upper() not in {'C', 'G'}:
            continue

        qty = parsed.get('qty')
        # Exclude reversed/void entries (<= 0)
        if qty is None or qty <= 0:
            continue

        raw_item_name = parsed.get('item_name', '').strip()
        dept, short_name = stylist_manager.get_info(current_stylist)
        sales_val = max(0.0, parsed.get('nett', 0.0))

        # Exclude specified vouchers/redemptions from Qty calculation
        item_code = raw_item_name.split(':')[0].strip().upper()
        if item_code not in QTY_EXCLUDED_CODES:
            totals[dept][short_name]['qty'] += qty

        totals[dept][short_name]['sales'] += sales_val
        record_count += 1

    # Ensure all stylists from groups are present so zeros show up
    for dept, stylists in STYLIST_GROUPS.items():
        for s in stylists:
            if s not in totals[dept]:
                totals[dept][s] = {'qty': 0, 'sales': 0.0}

    # Write CSV output
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    try:
        with open(output_file, mode='w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)

            writer.writerow(["FINAL CONSOLIDATED (C + G, Qty 1)"])

            grand_total_qty = 0
            grand_total_sales = 0.0

            # For each department, sort stylists by sales desc and write ranking
            for dept in ['HS', 'Nails', 'L&A']:
                dept_data = totals.get(dept, {})
                if not dept_data:
                    continue

                # Sort by sales descending
                sorted_stylists = sorted(dept_data.items(), key=lambda x: x[1]['sales'], reverse=True)

                writer.writerow([])
                writer.writerow([f"Department: {dept}"])
                writer.writerow(["Rank", "Employee", "Qty", "Sales (RM)"])

                rank = 1
                dept_qty = 0
                dept_sales = 0.0
                for name, vals in sorted_stylists:
                    writer.writerow([rank, name, vals['qty'], f"RM{vals['sales']:.2f}"])
                    dept_qty += vals['qty']
                    dept_sales += vals['sales']
                    grand_total_qty += vals['qty']
                    grand_total_sales += vals['sales']
                    rank += 1

                # Department-level totals
                writer.writerow([])
                writer.writerow([f"Totals ({dept})"])
                writer.writerow([f"Total Qty: {dept_qty}"])
                writer.writerow([f"Total Sales: RM{dept_sales:.2f}"])

            # Grand combined totals across all departments
            writer.writerow([])
            writer.writerow(["Totals (Combined)"])
            writer.writerow([f"Total Qty: {grand_total_qty}"])
            writer.writerow([f"Total Sales: RM{grand_total_sales:.2f}"])

    except PermissionError:
        print(f"\n[ERROR] Permission denied when writing to '{output_file}'.")
        print("Please close the file in Microsoft Excel or any other program and try again.\n")
        sys.exit(1)

    print(f"Package consolidated report written to {output_file} ({record_count} package items parsed).")


if __name__ == '__main__':
    # Usage: py reports\package_consolidated.py [input_dir] [output_file]
    in_dir = INPUT_DIR
    out_file = OUTPUT_FILE
    if len(sys.argv) >= 2:
        in_dir = sys.argv[1]
    if len(sys.argv) >= 3:
        out_file = sys.argv[2]

    process_package_totals(input_dir=in_dir, output_file=out_file)
