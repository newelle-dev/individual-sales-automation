import csv
import os
import glob
from collections import defaultdict
from sales_utils import STYLIST_GROUPS, StylistManager, parse_sales_row

def process_files(input_dir, output_file):
    # Data structure: data[dept][category][day][short_name] = amount
    data = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(float))))
    all_dates = set()
    dept_stylists = defaultdict(set)
    stylist_manager = StylistManager(STYLIST_GROUPS)
    
    # Track the month name from the data
    month_name = "MONTH"

    csv_files = glob.glob(os.path.join(input_dir, "*.csv"))
    
    for file_path in csv_files:
        with open(file_path, mode='r', encoding='utf-8') as f:
            reader = csv.reader(f)
            current_stylist = None
            
            for row in reader:
                # Basic row filtering
                if not row or not any(row):
                    continue
                
                line_str = ",".join(row) # For specific string checks
                if "Employee Received Detail" in line_str or "Employee Service Detail" in line_str or 'Grand Total' in line_str:
                    continue
                
                # Check for employee name (usually a single column row with name)
                if len(row) == 1 or (len(row) > 0 and row[0].strip() and not any(row[1:])):
                    potential_name = row[0].strip()
                    if potential_name and not potential_name.startswith('#'):
                        current_stylist = potential_name
                    continue

                # Skip header or total lines
                if row[0] == '#' or 'Total' in row or row[0] == 'Date':
                    continue
                
                parsed = parse_sales_row(row)
                if not parsed or not current_stylist:
                    continue
                
                # Extract data
                date_obj = parsed['date']
                day = date_obj.day
                all_dates.add(day)
                
                # Set month name from first valid date
                if month_name == "MONTH":
                    month_name = date_obj.strftime("%B").upper()
                
                dept, short_name = stylist_manager.get_info(current_stylist)
                dept_stylists[dept].add(short_name)

                if parsed['is_service_detail']:
                    # For Service Detail files, only add to Deductions for non-HS groups
                    # (Avoids double-counting sales and respects the HS group exclusion)
                    if dept != 'HS':
                        data[dept]['Deductions'][day][short_name] += parsed['deduction']
                else:
                    # Normal processing for Received Detail files
                    if parsed['category']:
                        data[dept][parsed['category']][day][short_name] += parsed['nett']
                    
                    # Aggregate Deductions
                    data[dept]['Deductions'][day][short_name] += parsed['deduction']



    if not all_dates:
        print("No data found to process.")
        return

    sorted_days = sorted(list(all_dates))
    
    # Write to output CSV
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
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
                        row.append(f"RM{max(0.0, val):.2f}")
                    writer.writerow(row)
                
                writer.writerow([]) # Blank line between sections
                writer.writerow([]) 

if __name__ == "__main__":
    process_files("input", "output/stylist_sales_pivot.csv")
    print("Optimized pivot summary saved to output/stylist_sales_pivot.csv")
