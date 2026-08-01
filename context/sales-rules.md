# Sales & Reporting Rules

This document outlines the business logic, categorization rules, and exceptions used in the Individual Sales Automation project. It is intended for salon managers, admin staff, and developers.

---

## 1. Departmental Groupings
Stylists are dynamically categorized into three main departments based on their canonical name:

*   **HS (Hair Stylists)**: `Nick`, `Sven`, `Yin Voon Hao`, `Steve`, `Phillip`, `Hellen`, `Tyra`, `Nicholas`, `Mayble`, `Kenny`, `Jade`, `Wei Xin`, `Kelvin`, `Gino`, `Moon`, `Daniel`, `Ella`, `Sedra`, `Rain`, `Carmen`.
*   **Nails**: `JEE`, `JESSY`, `ROI ROI`, `GRACE`, `JAY`, `JINGWEN`, `AGNES`, `Sharon`.
*   **L&A (Lash & Aesthetic)**: `DAISY`, `ALICE`, `YY`, `MOEMOE`, `WINNIE`, `NINI`, `ANGELA`, `JESSIE`, `NAOMI`.

> [!NOTE]
> All stylists in these groups are prepopulated in the final report. If a stylist has no sales or transactions for the month, they will still appear in their department section with `0.00` values.

---

## 2. Name Lookup & Mapping Rules
To handle name variations and spelling discrepancies in Wessconnect exports:
1.  **Normalization**: The system normalizes all names by converting them to lowercase and removing spaces (e.g., `"Yin Voon Hao"` becomes `"yinvoonhao"`).
2.  **Lookup Precedence**: The system matches names against the canonical list using a longest-matching-substring strategy first to prevent shorter names from causing incorrect matches on longer names.
3.  **Specific Aliases**:
    *   Any name containing `"nicky"` (case-insensitive, e.g., `"Nicky"`, `"nicky"`, `"Nicky Chen"`) is mapped to **Yin Voon Hao** (`HS`).
4.  **Fallback**: Any employee name that cannot be mapped to the predefined groups falls into the **Other** department, preserving their raw name.

---

## 3. CSV File Layout Detection
The parser dynamically identifies and handles four different Wessconnect CSV layouts based on row structure and starting fields:
*   **Employee Received Detail (15 Columns)**: Split Columns layout.
*   **Employee Received Detail (14 Columns)**: Combined Column layout (Item Code/Name merged).
*   **Employee Service Detail (14 Columns)**: Split Columns layout (starts with a date/time stamp).
*   **Employee Service Detail (13 Columns)**: Combined Column layout (starts with a date/time stamp).

---

## 4. Sales Categorization

### A. Received Detail Reports (Normal Transactions)
Sales category is determined by the `sale_type_code` and the item name:
*   **Product Sales**: Items with type code `'P'`.
*   **A la carte Sales**:
    *   Items with type code `'S'`.
    *   Items with type code `'G'` or `'C'` (usually package/gift cards) that are:
        *   Promotions: Item name contains `"makeover"`, `"nail promo"`, or `"promo"` (case-insensitive), **except** when it is `"cny promo"`.
        *   Negative net value transactions (`nett < 0`).
*   **Package Sales**:
    *   Items with type code `'G'` or `'C'` that do not meet the A la carte promotion/negative criteria.

### B. Service Detail Reports (Actual Deductions)
*   **A la carte Sales**: All transactions parsed from Service Detail reports default to A la carte sales.

---

## 5. Deductions & Special Exceptions

### A. Makeover Exception Rule (e.g., Makeover 176)
Any item containing `"makeover"` (case-insensitive) in the item name has its deduction values routed differently:

| Report Type | Standard Item Logic | Makeover Item Logic |
| :--- | :--- | :--- |
| **Received Detail** | Adds `nett` to its Category (e.g. Package). Adds `deduction` to **Deductions**. | Adds `nett + deduction` to **A la carte sales**. Adds `0.00` (nothing) to **Deductions**. |
| **Service Detail** | Adds `deduction` to **Deductions**. | Adds `deduction` to **A la carte sales** instead of Deductions. |

### B. Quantity 0.5 Adjustment (Service Detail)
If a service detail row contains a quantity (`qty`) of exactly `0.5`, the deduction value is doubled (`deduction * 2`) prior to aggregation.

---

## 6. Output Formatting & Mathematical Rules
*   **Dynamic Month Header**: The report month is extracted from the date of the first valid record and capitalized (e.g. `"JULY"`).
*   **Negative Value Clipping**: If a stylist's aggregated value for any category on a given day is negative (e.g. due to refunds or voided items), it is clipped to **`0.00`** in the final output CSV.

---

## 7. Package Consolidated Report Rules (`package_consolidated.py`)
For the isolated package totals report:
*   **Department Filtering**: Only processes and displays stylists in the **HS** (Hair Stylists) department.
*   **Monthly & Package Breakdown**: Groups transactions per month for each HS stylist, separating **Credit Package** (`'C'`) and **Treatment Package** (`'G'`).
*   **Excluded Voids/Reversals**: Excludes any records where the quantity (`qty`) is less than or equal to `0`.
*   **Quantity-Excluded Vouchers**: Certain item codes are excluded from the aggregated quantity count (though their sales values are still summed):
    *   `RBD`
    *   `RM10`
    *   `RM50`
    *   `C01044`
    *   `CP07`
*   **Ranking**: Ranks HS stylists by total sales descending for each month, displaying the **Top 7 stylists**, Credit Package Qty & Sales (RM), Treatment Package Qty & Sales (RM), and Combined Total Qty & Sales (RM).

