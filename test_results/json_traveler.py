import json
import pandas as pd

JSON_FILE = "calculation_db.coverage_db.json"
EXCEL_FILE = "scp_analysis_results.xlsx"


def get_scenario_id_from_test_case(test_case):
    return test_case.get("ScenarioID")


def collect_scenario_ids_from_unique_test_cases(unique_test_cases):
    scenarios = set()

    for test_case in unique_test_cases:
        scenario_id = get_scenario_id_from_test_case(test_case)
        if scenario_id:
            scenarios.add(scenario_id)

    return scenarios


def collect_scenario_ids_from_similar_test_cases(similar_test_cases):
    scenarios = set()

    for item in similar_test_cases:
        duplicate_case = item.get("DuplicateCase", {})
        matched_with = item.get("MatchedWith", {})

        duplicate_scenario = duplicate_case.get("ScenarioID")
        matched_scenario = matched_with.get("ScenarioID")

        if duplicate_scenario:
            scenarios.add(duplicate_scenario)

        if matched_scenario:
            scenarios.add(matched_scenario)

    return scenarios


def collect_scenario_ids_from_comparison_logs(comparison_logs):
    scenarios = set()

    for log in comparison_logs:
        optimization_type = log.get("optimization_type")

        if optimization_type in ["parallel", "bulk"]:
            continue

        case1 = log.get("Case1", {})
        case2 = log.get("Case2", {})

        scenario_1 = case1.get("ScenarioID")
        scenario_2 = case2.get("ScenarioID")

        if scenario_1:
            scenarios.add(scenario_1)

        if scenario_2:
            scenarios.add(scenario_2)

    return scenarios


def get_process_name(test_case_optimization, optimization_output):
    return (
        optimization_output.get("process_name")
        or optimization_output.get("process_title")
        or test_case_optimization.get("process_name")
        or test_case_optimization.get("process_title")
        or ""
    )


def get_optimization_type(optimization_output, comparison_logs):
    optimization_type = optimization_output.get("optimization_type")

    if optimization_type:
        return optimization_type

    if comparison_logs:
        return comparison_logs[0].get("optimization_type", "")

    return ""


with open(JSON_FILE, "r", encoding="utf-8-sig") as f:
    content = f.read().strip()

if content.startswith("["):
    data = json.loads(content)
else:
    data = [json.loads(line) for line in content.splitlines() if line.strip()]

rows = []

for doc_index, document in enumerate(data):
    processes = document.get("processes", {})

    if "test_case_optimization" not in processes:
        continue

    test_case_optimization = processes.get("test_case_optimization", {})
    optimization_output = test_case_optimization.get("output", {})

    unique_test_cases = optimization_output.get("unique_test_cases", [])
    similar_test_cases = optimization_output.get("similar_test_cases", [])
    comparison_logs = optimization_output.get("comparison_logs", [])

    unique_count = len(unique_test_cases)
    similar_count = len(similar_test_cases)
    comparison_log_count = len(comparison_logs)
    total_test_case_count = unique_count + similar_count

    process_name_or_title = get_process_name(
        test_case_optimization,
        optimization_output
    )

    optimization_type = get_optimization_type(
        optimization_output,
        comparison_logs
    )

    scenarios_after = collect_scenario_ids_from_unique_test_cases(unique_test_cases)

    if optimization_type in ["bulk", "parallel"] or comparison_log_count == 1:
        scenarios_before = (
            collect_scenario_ids_from_unique_test_cases(unique_test_cases)
            | collect_scenario_ids_from_similar_test_cases(similar_test_cases)
        )

        calculation_method = "Unique + Similar-Based"

    else:
        scenarios_before = collect_scenario_ids_from_comparison_logs(comparison_logs)
        calculation_method = "Comparison-Log-Based"

    removed_scenarios = scenarios_before - scenarios_after

    s_before = len(scenarios_before)
    s_after = len(scenarios_after)
    scp = (s_after / s_before) * 100 if s_before > 0 else 0

    rows.append({
        "Document Index": doc_index,
        "Session ID": document.get("session_id", ""),
        "Created At": document.get("created_at", ""),
        "Process Name / Title": process_name_or_title,
        "Optimization Type": optimization_type,
        "Used Model": optimization_output.get("used_model", ""),
        "Timestamp": optimization_output.get("timestamp", ""),
        "Calculation Method": calculation_method,

        "Unique Test Cases": unique_count,
        "Similar Test Cases": similar_count,
        "Total Test Cases": total_test_case_count,
        "Comparison Logs": comparison_log_count,

        "Scenarios Before": s_before,
        "Scenarios After": s_after,
        "SCP (%)": round(scp, 2),

        "Scenario List Before": ", ".join(sorted(scenarios_before)),
        "Scenario List After": ", ".join(sorted(scenarios_after)),
        "Removed Scenarios": ", ".join(sorted(removed_scenarios)) if removed_scenarios else "None"
    })

df = pd.DataFrame(rows)

with pd.ExcelWriter(EXCEL_FILE, engine="openpyxl") as writer:
    df.to_excel(writer, index=False, sheet_name="SCP Analysis")

    worksheet = writer.sheets["SCP Analysis"]

    for column_cells in worksheet.columns:
        max_length = 0
        column_letter = column_cells[0].column_letter

        for cell in column_cells:
            cell_value = str(cell.value) if cell.value is not None else ""
            max_length = max(max_length, len(cell_value))

        worksheet.column_dimensions[column_letter].width = min(max_length + 2, 60)

print(f"Excel raporu oluşturuldu: {EXCEL_FILE}")