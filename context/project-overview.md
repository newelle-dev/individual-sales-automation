# Project Overview: Individual Sales Automation

This project is a Python-based utility designed to automate the processing and aggregation of stylist sales data exported from Wessconnect. It converts raw transaction logs into an organized pivot-style summary report for easy business analysis.

## Core Purpose & Objective
- **Automate manual Excel work**: Minimize the administrative overhead of manually cleaning, formatting, and summarizing Wessconnect CSV exports every month.
- **Accurate performance tracking**: Group stylists by department and aggregate performance metrics (Package Sales, Product Sales, A la carte Sales, and Deductions) for payroll and performance evaluations.
- **Provide a zero-setup user experience**: Allow non-technical admin staff to run the reporting pipelines using simple Windows batch scripts (`Run Report.bat`).

## Target Audience
- **Salon managers / Admin staff**: Non-technical users who need a one-click solution.
- **Technical co-founder / Developers**: Users extending/modifying parsing and reporting rules.

## Core Features
1. **Multi-Format Parsing**:
   - Handles "Employee Received Detail" reports (for transaction amounts).
   - Handles "Employee Service Detail" reports (for actual deduction calculation).
2. **Departmental Grouping**:
   - Groups stylists dynamically into **HS** (Hair Stylists), **Nails**, and **L&A** (Lash & Aesthetic).
3. **Metric Aggregation**:
   - Summarizes net sales and deductions per stylist.
   - Outputs daily breakdown rows per category for each stylist.
4. **Data Integrity & Normalization**:
   - Handles name aliases (e.g., mapping "Nicky" to "Yin Voon Hao").
   - Clips negative values to RM 0.00 where appropriate.
   - Extracts report month and day columns dynamically.
