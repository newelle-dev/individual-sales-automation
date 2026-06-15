import csv
import os
import sys
import glob
from collections import defaultdict, OrderedDict

# Ensure project root is on sys.path so imports work when running this file directly
ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from sales_utils import STYLIST_GROUPS, StylistManager, parse_sales_row

INPUT_DIR = os.path.join(os.path.dirname(__file__), "input")
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "output", "package_consolidated_by_group.csv")


def process_package_totals(input_dir=INPUT_DIR, output_file=OUTPUT_FILE):
    totals = defaultdict(lambda: defaultdict(lambda: {'qty': 0, 'sales': 0.0}))
    stylist_manager = StylistManager(STYLIST_GROUPS)

    csv_files = glob.glob(os.path.join(input_dir, "*.csv"))
    if not csv_files:
        print(f"No CSV files found in {input_dir}")
        return

    for file_path in csv_files:
        with open(file_path, mode='r', encoding='utf-8') as f:
            reader = csv.reader(f)
            current_stylist = None

            for row in reader:
                if not row or not any(row):
                    continue

                line_str = ",".join(row)
                if "Employee Received Detail" in line_str or "Employee Service Detail" in line_str or 'Grand Total' in line_str:
                    continue

                # Detect a row containing only the stylist name
                if len(row) == 1 or (len(row) > 0 and row[0].strip() and not any(cell.strip() for cell in row[1:])):
                    potential_name = row[0].strip()
                    if potential_name and not potential_name.startswith('#'):
                        current_stylist = potential_name
                    continue

                # Skip header/total rows
                if row[0] == '#' or 'Total' in row or row[0] == 'Date':
                    continue

                if len(row) < 8:
                    continue

                sale_type = row[6].strip().upper()
                if sale_type not in {'C', 'G'}:
                    continue

                try:
                    raw_qty = float(row[7].strip())
                except ValueError:
                    continue

                # Exclude reversed/void entries marked with -1
                if raw_qty == -1:
                    continue

                # Exclude items that are promotions (case-insensitive)
                item_name = row[5].strip().lower() if len(row) > 5 else ''
                if 'promo' in item_name:
                    continue

                parsed = parse_sales_row(row)
                if not parsed or not current_stylist:
                    continue

                # Skip rows where the parsed quantity is -1 (explicit exclusion)
                parsed_qty = parsed.get('qty')
                if parsed_qty is not None and parsed_qty == -1:
                    continue

                dept, short_name = stylist_manager.get_info(current_stylist)

                # Use the actual positive quantity when available (exclude negatives)
                qty = raw_qty if raw_qty > 0 else (parsed_qty if parsed_qty and parsed_qty > 0 else 0)
                sales_val = max(0.0, parsed.get('nett', 0.0))

                totals[dept][short_name]['qty'] += qty
                totals[dept][short_name]['sales'] += sales_val

    # Ensure all stylists from groups are present so zeros show up
    for dept, stylists in STYLIST_GROUPS.items():
        for s in stylists:
            if s not in totals[dept]:
                totals[dept][s] = {'qty': 0, 'sales': 0.0}

    # Write CSV output
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
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

    print(f"Package consolidated report written to {output_file}")


if __name__ == '__main__':
    import sys

    # Allow overriding input/output paths from the command line
    # Usage: py reports\package_consolidated.py [input_dir] [output_file]
    in_dir = INPUT_DIR
    out_file = OUTPUT_FILE
    if len(sys.argv) >= 2:
        in_dir = sys.argv[1]
    if len(sys.argv) >= 3:
        out_file = sys.argv[2]

    process_package_totals(input_dir=in_dir, output_file=out_file)
