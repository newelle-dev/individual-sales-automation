import csv
import glob
import os
import sys
from collections import defaultdict
from sales_utils import STYLIST_GROUPS, StylistManager, iter_sales_records

def process_files(input_dir: str, output_file: str) -> None:
    """
    Processes all Wessconnect sales CSV files in input_dir and generates
    the aggregated pivot summary report written to output_file.
    """
    csv_files = glob.glob(os.path.join(input_dir, "*.csv"))
    if not csv_files:
        print(f"[ERROR] No CSV files found in input directory '{input_dir}'.")
        sys.exit(1)

    # Data structure: data[dept][category][day][short_name] = amount
    data = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(float))))
    all_dates = set()
    dept_stylists = defaultdict(set)
    stylist_manager = StylistManager(STYLIST_GROUPS)
    
    # Prepopulate `dept_stylists` with all stylists from STYLIST_GROUPS
    # so stylists with zero transactions still appear in the output.
    for dept, stylists in STYLIST_GROUPS.items():
        for s in stylists:
            d, short_name = stylist_manager.get_info(s)
            dept_stylists[d].add(short_name)

    # Track the month name from the data
    month_name = "MONTH"
    record_count = 0

    for current_stylist, parsed in iter_sales_records(input_dir):
        record_count += 1
        date_obj = parsed['date']
        day = date_obj.day
        all_dates.add(day)
        
        # Set month name from first valid date
        if month_name == "MONTH":
            month_name = date_obj.strftime("%B").upper()
        
        dept, short_name = stylist_manager.get_info(current_stylist)
        dept_stylists[dept].add(short_name)

        item_lower = parsed.get('item_name', '').lower()
        is_makeover = 'makeover' in item_lower

        if parsed['is_service_detail']:
            # For Service Detail files, add the 'actual value' to Deductions
            # so that: service-detail actuals + received-detail deductions
            # produce the final deduction sales per stylist.
            deduction = parsed['deduction']
            if parsed.get('qty') == 0.5:
                deduction *= 2
            
            if is_makeover:
                data[dept]['A la carte sales'][day][short_name] += deduction
            else:
                data[dept]['Deductions'][day][short_name] += deduction
        else:
            # Normal processing for Received Detail files
            if parsed['category']:
                if is_makeover:
                    data[dept][parsed['category']][day][short_name] += (parsed['nett'] + parsed['deduction'])
                else:
                    data[dept][parsed['category']][day][short_name] += parsed['nett']
            
            # Aggregate Deductions
            if not is_makeover:
                data[dept]['Deductions'][day][short_name] += parsed['deduction']

    if not all_dates:
        print("[ERROR] No valid transaction data found in input CSV files.")
        sys.exit(1)

    sorted_days = sorted(list(all_dates))
    
    # Write to output CSV
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    try:
        with open(output_file, mode='w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            
            # Consistent section order
            categories = ['Package sales', 'Product sales', 'A la carte sales', 'Deductions']
            departments = ['HS', 'Nails', 'L&A']

            for dept in departments:
                if dept not in dept_stylists and dept not in data:
                    continue
                
                for sale_type in categories:
                    # Section Header
                    writer.writerow([f"INDIVIDUAL {sale_type.upper()} - {dept}"])
                    
                    # Use defined order for stylists in this dept
                    preferred_order = STYLIST_GROUPS.get(dept, [])
                    present_stylists = [s for s in preferred_order if s in dept_stylists[dept]]
                    
                    # Add any stylists found that weren't in the preferred order (fallback)
                    other_found = sorted([s for s in dept_stylists[dept] if s not in preferred_order])
                    present_stylists.extend(other_found)

                    if not present_stylists:
                        continue
                    
                    # Column Headers (Dynamic Month)
                    header = [month_name] + present_stylists
                    writer.writerow(header)
                    
                    # Data Rows
                    for day in sorted_days:
                        row = [day]
                        for s in present_stylists:
                            val = data[dept][sale_type][day][s]
                            # Handling negative values by clipping to 0
                            row.append(f"{max(0.0, val):.2f}")
                        writer.writerow(row)
                    
                    writer.writerow([]) # Blank line between sections
                    writer.writerow([]) 

    except PermissionError:
        print(f"\n[ERROR] Permission denied when writing to '{output_file}'.")
        print("Please close the file in Microsoft Excel or any other program and try again.\n")
        sys.exit(1)

    print(f"Processed {len(csv_files)} CSV file(s), parsed {record_count} transactions across {len(all_dates)} day(s).")
    print(f"Optimized pivot summary saved to {output_file}")

if __name__ == "__main__":
    process_files("input", "output/stylist_sales_pivot.csv")
