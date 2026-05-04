"""
Cache Analysis Tool
-------------------
Connects to a SQLite cache database and exports structured data
into categorised Excel files for analysis and review.
"""

import os
import glob
import sqlite3
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog

import pandas as pd


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def autosize_columns(writer, sheet_name, df):
    """Auto-resize every column in *sheet_name* to fit its content."""
    worksheet = writer.sheets[sheet_name]
    for idx, col in enumerate(df.columns):
        series = df[col]
        max_len = max(
            series.astype(str).map(len).max(),   # widest data value
            len(str(col))                         # column header width
        ) + 2                                     # small padding buffer
        worksheet.set_column(idx, idx, max_len)


def write_sheet(writer, sheet_name, df):
    """Write a DataFrame to a named sheet and autosize its columns."""
    df.to_excel(writer, sheet_name=sheet_name, index=False)
    autosize_columns(writer, sheet_name, df)


def safe_read_sql(query, con, label="query"):
    """Run a SQL query and return a DataFrame. Returns empty DF on failure."""
    try:
        return pd.read_sql(query, con)
    except Exception as exc:
        print(f"  [WARNING] Could not execute {label}: {exc}")
        return pd.DataFrame()


# ---------------------------------------------------------------------------
# File Selection
# ---------------------------------------------------------------------------

root = tk.Tk()
root.withdraw()

print("Please select the cache file to open...")
file_path = filedialog.askopenfilename(
    title="Select Cache File",
    filetypes=[("SQLite Database", "*.db *.sqlite *.cache"), ("All Files", "*.*")]
)

if not file_path:
    print("No file selected. Exiting.")
    raise SystemExit

file_folder = os.path.dirname(file_path)
print(f"Cache: {file_path}")

print("Please select the output folder...")
save_path = filedialog.askdirectory(title="Select Output Folder")

if not save_path:
    print("No output folder selected. Exiting.")
    raise SystemExit

print(f"Output: {save_path}\n")

# ---------------------------------------------------------------------------
# Connect to Database
# ---------------------------------------------------------------------------

try:
    con = sqlite3.connect(file_path)
    print(f"Connected to database: {file_path}\n")
except Exception as exc:
    print(f"[ERROR] Could not connect to database: {exc}")
    raise SystemExit


# ---------------------------------------------------------------------------
# 1. Agent_Info.xlsx
# ---------------------------------------------------------------------------

def export_agent_info(con, save_path):
    print("Exporting Agent_Info.xlsx...")
    output = os.path.join(save_path, "Agent_Info.xlsx")

    try:
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            sheets = {
                "AgentProps":        "SELECT * FROM agentprops",
                "PublicSystemInfoOS":"SELECT * FROM PublicSystemInfoOS",
                "ConfigProp":        "SELECT * FROM ConfigProp",
                "InternalConfigList":"SELECT * FROM InternalConfigList",
            }
            for sheet_name, query in sheets.items():
                df = safe_read_sql(query, con, sheet_name)
                write_sheet(writer, sheet_name, df)

        print(f"  Saved: {output}")
    except Exception as exc:
        print(f"  [ERROR] Agent_Info.xlsx failed: {exc}")


# ---------------------------------------------------------------------------
# 2. BlockInfo.xlsx
# ---------------------------------------------------------------------------

def export_block_info(con, save_path):
    print("Exporting BlockInfo.xlsx...")
    output = os.path.join(save_path, "BlockInfo.xlsx")

    try:
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:

            # All blocks
            df_blocks = safe_read_sql("SELECT * FROM Blocks", con, "Blocks")
            write_sheet(writer, "Blocks", df_blocks)

            if not df_blocks.empty and "Hash" in df_blocks.columns:
                hashes = df_blocks["Hash"].dropna().unique().tolist()
                placeholders = ",".join(["?" for _ in hashes])

                # InternalFiles for all block hashes
                df_files = safe_read_sql(
                    f"SELECT * FROM InternalFiles WHERE Hash IN ({placeholders})",
                    con, "InternalFiles"
                ) if hashes else pd.DataFrame()
                # pd.read_sql does not support ? params directly; use a temp approach
                hash_list = "','".join(hashes)
                df_files = safe_read_sql(
                    f"SELECT * FROM InternalFiles WHERE Hash IN ('{hash_list}')",
                    con, "InternalFiles"
                )
                write_sheet(writer, "InternalFiles", df_files)

                # InternalApprovalReasons for all block hashes
                df_approval = safe_read_sql(
                    f"SELECT * FROM InternalApprovalReasons WHERE Hash IN ('{hash_list}')",
                    con, "InternalApprovalReasons"
                )
                write_sheet(writer, "InternalApprovalReasons", df_approval)

                # InternalConfigList for all block hashes
                df_config = safe_read_sql(
                    f"SELECT * FROM InternalConfigList WHERE Hash IN ('{hash_list}')",
                    con, "InternalConfigList"
                )
                write_sheet(writer, "InternalConfigList", df_config)

                # Rules matching ruleID in blocks
                if "RuleID" in df_blocks.columns:
                    rule_ids = df_blocks["RuleID"].dropna().unique().tolist()
                    rule_id_list = "','".join(str(r) for r in rule_ids)
                    df_rules = safe_read_sql(
                        f"SELECT * FROM Rules WHERE RuleID IN ('{rule_id_list}')",
                        con, "Rules"
                    )
                    write_sheet(writer, "Rules", df_rules)
            else:
                print("  [INFO] Blocks table is empty or missing Hash column.")

        print(f"  Saved: {output}")
    except Exception as exc:
        print(f"  [ERROR] BlockInfo.xlsx failed: {exc}")


# ---------------------------------------------------------------------------
# 3. PerformanceInfo.xlsx
# ---------------------------------------------------------------------------

def export_performance_info(con, save_path):
    print("Exporting PerformanceInfo.xlsx...")
    output = os.path.join(save_path, "PerformanceInfo.xlsx")

    try:
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:

            # Top 10 counters by operation processing
            df_op = safe_read_sql(
                "SELECT * FROM PublicCountersOperationProcessing ORDER BY Count DESC LIMIT 10",
                con, "PublicCountersOperationProcessing"
            )
            write_sheet(writer, "OpProcessing_Top10", df_op)

            # Top 10 counters by file type
            df_ft = safe_read_sql(
                "SELECT * FROM PublicCountersOperationsByFileType ORDER BY Count DESC LIMIT 10",
                con, "PublicCountersOperationsByFileType"
            )
            write_sheet(writer, "ByFileType_Top10", df_ft)

            # Top 10 counters by process
            df_proc = safe_read_sql(
                "SELECT * FROM PublicCountersOperationsByProcess ORDER BY Count DESC LIMIT 10",
                con, "PublicCountersOperationsByProcess"
            )
            write_sheet(writer, "ByProcess_Top10", df_proc)

            # Count of each Process in InternalReports
            df_proc_count = safe_read_sql(
                "SELECT Process, COUNT(*) AS Count FROM InternalReports GROUP BY Process ORDER BY Count DESC",
                con, "InternalReports Process Count"
            )
            write_sheet(writer, "ProcessCount", df_proc_count)

            # Count of each FullPath (target) in InternalReports
            df_path_count = safe_read_sql(
                "SELECT FullPath, COUNT(*) AS Count FROM InternalReports GROUP BY FullPath ORDER BY Count DESC",
                con, "InternalReports FullPath Count"
            )
            write_sheet(writer, "FullPathCount", df_path_count)

        print(f"  Saved: {output}")
    except Exception as exc:
        print(f"  [ERROR] PerformanceInfo.xlsx failed: {exc}")


# ---------------------------------------------------------------------------
# 4. RuleChecks.xlsx
# ---------------------------------------------------------------------------

def export_rule_checks(con, save_path):
    print("Exporting RuleChecks.xlsx...")
    output = os.path.join(save_path, "RuleChecks.xlsx")

    try:
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:

            # Rules: Target=* and Action=Allow (excluding Tamper Protection)
            df = safe_read_sql(
                """SELECT * FROM Rules
                   WHERE Target = '*'
                     AND Action = 'Allow'
                     AND Policy != 'Tamper Protection'""",
                con, "Target_Star_Allow"
            )
            write_sheet(writer, "Target_Star_Allow", df)

            # Rules: Process=* and Action=Allow (excluding Tamper Protection)
            df = safe_read_sql(
                """SELECT * FROM Rules
                   WHERE Process = '*'
                     AND Action = 'Allow'
                     AND Policy != 'Tamper Protection'""",
                con, "Process_Star_Allow"
            )
            write_sheet(writer, "Process_Star_Allow", df)

            # Rules: Action=Ignore (excluding Tamper Protection)
            df = safe_read_sql(
                """SELECT * FROM Rules
                   WHERE Action = 'Ignore'
                     AND Policy != 'Tamper Protection'""",
                con, "Action_Ignore"
            )
            write_sheet(writer, "Action_Ignore", df)

            # Rules: Action=Silent (excluding Tamper Protection)
            df = safe_read_sql(
                """SELECT * FROM Rules
                   WHERE Action = 'Silent'
                     AND Policy != 'Tamper Protection'""",
                con, "Action_Silent"
            )
            write_sheet(writer, "Action_Silent", df)

            # Kernel exclusions from DebugInfo
            df = safe_read_sql(
                """SELECT * FROM DebugInfo
                   WHERE Key IN ('kernelFileOpExclusions', 'kernelProcessExclusions')""",
                con, "KernelExclusions"
            )
            write_sheet(writer, "KernelExclusions", df)

        print(f"  Saved: {output}")
    except Exception as exc:
        print(f"  [ERROR] RuleChecks.xlsx failed: {exc}")


# ---------------------------------------------------------------------------
# 5. SHA256Check.xlsx
# ---------------------------------------------------------------------------

def export_sha256_check(con, save_path):
    print("SHA256 Check...")
    sha256 = simpledialog.askstring(
        "SHA256 Check",
        "Enter the SHA256 hash to look up (leave blank to skip):"
    )

    if not sha256 or not sha256.strip():
        print("  Skipped SHA256 Check.")
        return

    sha256 = sha256.strip().lower()
    output = os.path.join(save_path, "SHA256Check.xlsx")

    try:
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:

            # The hash itself
            df_hash = pd.DataFrame({"SHA256": [sha256]})
            write_sheet(writer, "SHA256_Input", df_hash)

            # Block and ConfigList data for the hash
            df_blocks = safe_read_sql(
                f"SELECT * FROM Blocks WHERE Hash = '{sha256}'",
                con, "Blocks"
            )
            write_sheet(writer, "BlockData", df_blocks)

            df_config = safe_read_sql(
                f"SELECT * FROM InternalConfigList WHERE Hash = '{sha256}'",
                con, "InternalConfigList"
            )
            write_sheet(writer, "ConfigListData", df_config)

            # InternalFiles for the hash
            df_files = safe_read_sql(
                f"SELECT * FROM InternalFiles WHERE Hash = '{sha256}'",
                con, "InternalFiles"
            )
            write_sheet(writer, "InternalFiles", df_files)

            # InternalReports for the hash
            df_reports = safe_read_sql(
                f"SELECT * FROM InternalReports WHERE Hash = '{sha256}'",
                con, "InternalReports"
            )
            write_sheet(writer, "InternalReports", df_reports)

            # InternalCertificates for Cert_ID listed in file details
            if not df_files.empty and "Cert_ID" in df_files.columns:
                cert_ids = df_files["Cert_ID"].dropna().unique().tolist()
                if cert_ids:
                    cert_id_list = "','".join(str(c) for c in cert_ids)
                    df_certs = safe_read_sql(
                        f"SELECT * FROM InternalCertificates WHERE Cert_ID IN ('{cert_id_list}')",
                        con, "InternalCertificates"
                    )
                    write_sheet(writer, "InternalCertificates", df_certs)
                else:
                    write_sheet(writer, "InternalCertificates", pd.DataFrame())
            else:
                write_sheet(writer, "InternalCertificates", pd.DataFrame())

        print(f"  Saved: {output}")
    except Exception as exc:
        print(f"  [ERROR] SHA256Check.xlsx failed: {exc}")


# ---------------------------------------------------------------------------
# 6. LargeViews.xlsx
# ---------------------------------------------------------------------------

def export_large_views(con, save_path):
    print("Large Views...")
    confirm = messagebox.askyesno(
        "Large Views",
        "Do you want to export the large tables?\n\n"
        "This includes InternalReports and PublicTimeLine and may take a while."
    )

    if not confirm:
        print("  Skipped Large Views export.")
        return

    output = os.path.join(save_path, "LargeViews.xlsx")

    try:
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:

            df_reports = safe_read_sql("SELECT * FROM InternalReports", con, "InternalReports")
            write_sheet(writer, "InternalReports", df_reports)

            df_timeline = safe_read_sql("SELECT * FROM PublicTimeLine", con, "PublicTimeLine")
            write_sheet(writer, "PublicTimeLine", df_timeline)

        print(f"  Saved: {output}")
    except Exception as exc:
        print(f"  [ERROR] LargeViews.xlsx failed: {exc}")


# ---------------------------------------------------------------------------
# 7. Trace Check
# ---------------------------------------------------------------------------

def trace_check(file_folder):
    print("Running Trace Check...")
    trace_files = glob.glob(os.path.join(file_folder, "*.log")) + \
                  glob.glob(os.path.join(file_folder, "*.trace"))

    if trace_files:
        print("  Trace log(s) found:")
        for f in trace_files:
            print(f"    - {f}")
        # TODO: Add trace data parsing logic here
        print("  [PLACEHOLDER] Trace data checking not yet implemented.")
    else:
        print("  No trace log found in the cache directory.")


# ---------------------------------------------------------------------------
# Run All Exports
# ---------------------------------------------------------------------------

export_agent_info(con, save_path)
export_block_info(con, save_path)
export_performance_info(con, save_path)
export_rule_checks(con, save_path)
export_sha256_check(con, save_path)
export_large_views(con, save_path)
trace_check(file_folder)

# ---------------------------------------------------------------------------
# Close Connection
# ---------------------------------------------------------------------------

con.close()
print("\nAll exports complete. Database connection closed.")
