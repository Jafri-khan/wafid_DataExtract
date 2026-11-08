# Wafid Medical Data Extraction & Excel Automation System (Updated)

## Key Updates
1. **Persistent Edge Profile**: Reuses login sessions automatically from `edge_profile/` so manual login is skipped whenever active.
2. **Exact Excel Mapping**: Explicitly maps extracted values into Columns F through L without row shifting:
   - Column F: Height
   - Column G: Weight
   - Column H: Blood Group
   - Column I: BMI
   - Column J: Field J
   - Column K: Field K
   - Column L: Remarks
3. **Streamlined Unattended Workflow**: Individual record YES/NO confirmation prompts have been removed. Processing runs sequentially across C2 through Cn automatically.
4. **Input Field Clearing**: Before each search, `input#id_passport` is cleared using `CTRL + A` and `BACKSPACE`, verified empty, and checked after text entry.
5. **Search Page Reset**: Automatically returns to the base search page after each report extraction.
6. **Per-Record Excel Saving**: Saves workbook instantly after every record to prevent data loss.

## How to Run
1. Run `install.bat` to create the environment and install dependencies.
2. Ensure your workbook is placed at `F:\Datavalidation_Automation\Datatocheck.xlsx`.
3. Run `run.bat` to launch the application.
