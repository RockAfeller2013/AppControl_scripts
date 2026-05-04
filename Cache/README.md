# Cache Analysis Tool — Code & Feature Reference

## Overview

This tool connects to a SQLite cache database and exports structured data into
categorized Excel files for analysis and review.

---

## Output Files

### `Agent_Info.xlsx`
- Export all of `AgentProps`
- Export all of `PublicSystemInfoOS`
- Export all of `ConfigProp`
- Export all of `InternalConfigList`

---

### `BlockInfo.xlsx`
- Creates a table of all Blocks
- Exports a list of all blocks
- Exports the `InternalFiles` for all hashes in blocks
- Exports the `InternalApprovalReasons` for all hashes listed in blocks
- Exports the `InternalConfigList` for all hashes listed in blocks
- Exports the Rule listed as the `ruleID` in the block event

---

### `PerformanceInfo.xlsx`
- Exports the top 10 `PublicCountersOperationProcessing`
- Exports the top 10 `PublicCountersOperationsByFileType`
- Exports the top 10 `PublicCountersOperationsByProcess`
- Exports the count of Processes listed in `InternalReports`
- Exports the count of the `FullPath` (target) in `InternalReports`

---

### `RuleChecks.xlsx`
- Exports all rules with Target `*` and action `Allow` *(except Tamper Protection)*
- Exports all rules with Process `*` and action `Allow` *(except Tamper Protection)*
- Exports all rules with action `Ignore` *(except Tamper Protection)*
- Exports all rules with action `Silent` *(except Tamper Protection)*
- Exports all `kernelFileOpExclusions` and `kernelProcessExclusions` from `DebugInfo`

---

### `SHA256Check.xlsx`
- Creates a temporary table with the SHA256 provided
- Exports the SHA256 provided
- Exports Block and `ConfigList` data for the hash provided
- Exports the `InternalFiles` data for the hash provided
- Exports the `InternalReports` for the hash provided
- Exports the `InternalCertificates` for the `Cert_ID` listed in the file details of the hash provided

---

### `LargeViews.xlsx`
- Prompts whether to export the large tables
- Exports all of `InternalReports`
- Exports all of `PublicTimeLine`

---

### Trace Check
- Checks if a trace log was collected in the same directory as the cache
- Currently a placeholder for trace data checking

---

## Code Reference

### Select the Cache to Open

```python
# Set Open Cache Window
root = tk.Tk()
root.withdraw()
file_path = filedialog.askopenfilename()
file_folder = "/".join(file_path.split("/")[:-1])
```

---

### Select the Output Folder

```python
save_path = filedialog.askdirectory()
```

---

### Attach SQLite3 to the Database Provided

```python
con = sqlite3.connect(file_path)
print(con)
cursorObj = con.cursor()
```

---

### Create a Code Block to Export to Excel

The pattern below is reusable — adapt the SQL query, sheet name, and file name
to create additional exports.

```python
def Agent_info(con):
    # Track sheet names written in this workbook
    Current_List = []

    # Bind writer to output Excel file
    writer = pd.ExcelWriter(
        os.path.join(save_path, 'Agent_Info.xlsx'),
        engine='xlsxwriter'
    )

    # --- AgentProps sheet ---
    sql_string = 'SELECT * FROM agentprops'
    df = pd.read_sql(sql_string, con)
    df.to_excel(writer, sheet_name='AgentProps', index=False)
    Current_List.append('AgentProps')

    # Auto-resize all columns for readability (WIP)
    for i in Current_List:
        worksheet = writer.sheets[i]
        for idx, col in enumerate(df):
            series = df[col]
            max_len = max(
                series.astype(str).map(len).max(),  # widest data value
                len(str(series.name))               # column header width
            ) + 1                                   # small padding buffer
            worksheet.set_column(idx, idx, max_len)

    # Save workbook
    writer.save()
    print("Finished Exporting Agent Info")

Agent_info(con)
```

---

### Close the SQLite Connection (Unlocks DB)

```python
con.close()
```
