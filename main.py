"""
Dataset Metadata and Quality Assessment Tool
MSc Fundamentals of Programming - Capstone Project (Project 10)

Reads dataset metadata records from a CSV file, validates them, calculates
missing-data quality classifications and presents a menu-driven analysis
tool. Core Python only - no external libraries.
"""

import csv
import os

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "10_Dataset_Metadata.csv")

RECOGNIZED_SOURCE_TYPES = {"Survey", "Administrative", "Sensor", "CSV"}


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------

def load_records(filepath):
    """Read the raw metadata rows from the CSV file into a list of dicts."""
    records = []
    with open(filepath, newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            records.append(row)
    return records


# ---------------------------------------------------------------------------
# Conversion helpers
# ---------------------------------------------------------------------------

def _to_int(value):
    """Convert a CSV string to int; return None if it cannot be converted."""
    if value is None:
        return None
    value = value.strip()
    if value == "":
        return None
    try:
        return int(value)
    except ValueError:
        return None


def _to_bool(value):
    """Convert a CSV TRUE/FALSE string to a Python bool; return None if unclear."""
    if value is None:
        return None
    value = value.strip().upper()
    if value == "TRUE":
        return True
    if value == "FALSE":
        return False
    return None


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_record(raw_record):
    """
    Validate a single raw dataset-metadata record.

    Returns a tuple (is_valid, reason, clean_record). clean_record holds
    converted numeric/boolean values ready for analysis; it is only
    meaningful when is_valid is True.
    """
    dataset_id = raw_record.get("dataset_id", "").strip()
    dataset_name = raw_record.get("dataset_name", "").strip()
    number_of_records = _to_int(raw_record.get("number_of_records"))
    number_of_variables = _to_int(raw_record.get("number_of_variables"))
    missing_values = _to_int(raw_record.get("missing_values"))
    duplicate_records = _to_int(raw_record.get("duplicate_records"))
    source_type = raw_record.get("source_type", "").strip()
    contains_personal_data = _to_bool(raw_record.get("contains_personal_data"))

    if not dataset_id or not dataset_name:
        return False, "Dataset ID and/or name is missing.", None

    if number_of_records is None or number_of_records <= 0:
        return False, "Number of records must be a whole number greater than zero.", None

    if number_of_variables is None or number_of_variables <= 0:
        return False, "Number of variables must be a whole number greater than zero.", None

    if missing_values is None or missing_values < 0:
        return False, "Missing-values count must be a whole number and cannot be negative.", None

    if duplicate_records is None or duplicate_records < 0:
        return False, "Duplicate-records count must be a whole number and cannot be negative.", None

    if missing_values > number_of_records:
        return False, "Missing-values count cannot exceed the number of records.", None

    if duplicate_records > number_of_records:
        return False, "Duplicate-records count cannot exceed the number of records.", None

    if source_type not in RECOGNIZED_SOURCE_TYPES:
        return False, "Source type '{}' is not recognised.".format(source_type), None

    if contains_personal_data is None:
        return False, "Contains-personal-data value must be TRUE or FALSE.", None

    clean_record = {
        "dataset_id": dataset_id,
        "dataset_name": dataset_name,
        "number_of_records": number_of_records,
        "number_of_variables": number_of_variables,
        "missing_values": missing_values,
        "duplicate_records": duplicate_records,
        "source_type": source_type,
        "contains_personal_data": contains_personal_data,
    }
    return True, "", clean_record


def validate_all(raw_records):
    """Split raw records into valid (enriched) and invalid (with reasons) lists."""
    valid_records = []
    invalid_records = []
    for raw_record in raw_records:
        is_valid, reason, clean_record = validate_record(raw_record)
        if is_valid:
            clean_record["missing_percentage"] = calculate_missing_percentage(clean_record)
            clean_record["quality_class"] = classify_quality(clean_record["missing_percentage"])
            valid_records.append(clean_record)
        else:
            invalid_records.append({
                "dataset_id": raw_record.get("dataset_id", "").strip() or "(missing)",
                "dataset_name": raw_record.get("dataset_name", "").strip() or "(missing)",
                "reason": reason,
            })
    return valid_records, invalid_records


# ---------------------------------------------------------------------------
# Calculations
# ---------------------------------------------------------------------------

def calculate_missing_percentage(record):
    """missing-data percentage = missing values / number of records * 100"""
    return record["missing_values"] / record["number_of_records"] * 100


def classify_quality(missing_percentage):
    """Excellent < 5%, Satisfactory 5%-<10%, Needs improvement >= 10%."""
    if missing_percentage < 5:
        return "Excellent"
    if missing_percentage < 10:
        return "Satisfactory"
    return "Needs improvement"


QUALITY_RANK = {"Excellent": 0, "Satisfactory": 1, "Needs improvement": 2}


def sort_by_quality(valid_records):
    """Return datasets ordered from highest to lowest quality."""
    return sorted(
        valid_records,
        key=lambda r: (QUALITY_RANK[r["quality_class"]], r["missing_percentage"]),
    )


def build_summary(valid_records, invalid_records, raw_records):
    """Aggregate portfolio-level statistics used by the summary and quality menus."""
    summary = {
        "supplied_count": len(raw_records),
        "valid_count": len(valid_records),
        "invalid_count": len(invalid_records),
        "total_valid_records": sum(r["number_of_records"] for r in valid_records),
        "quality_counts": {"Excellent": 0, "Satisfactory": 0, "Needs improvement": 0},
        "source_type_counts": {},
        "personal_data_count": 0,
        "most_records": None,
        "most_variables": None,
        "highest_missing_percentage": None,
    }

    for record in valid_records:
        summary["quality_counts"][record["quality_class"]] += 1
        summary["source_type_counts"][record["source_type"]] = (
            summary["source_type_counts"].get(record["source_type"], 0) + 1
        )
        if record["contains_personal_data"]:
            summary["personal_data_count"] += 1

        if (summary["most_records"] is None
                or record["number_of_records"] > summary["most_records"]["number_of_records"]):
            summary["most_records"] = record

        if (summary["most_variables"] is None
                or record["number_of_variables"] > summary["most_variables"]["number_of_variables"]):
            summary["most_variables"] = record

        if (summary["highest_missing_percentage"] is None
                or record["missing_percentage"] > summary["highest_missing_percentage"]["missing_percentage"]):
            summary["highest_missing_percentage"] = record

    return summary


# ---------------------------------------------------------------------------
# Menu functions
# ---------------------------------------------------------------------------

def display_menu():
    print()
    print("DATASET METADATA AND QUALITY ASSESSMENT TOOL")
    print("1. View dataset metadata")
    print("2. Assess data quality")
    print("3. Search for a dataset")
    print("4. View personal-data warnings")
    print("5. View invalid records")
    print("6. View portfolio summary")
    print("7. Exit")


def view_dataset_metadata(valid_records):
    if not valid_records:
        print("\nNo valid datasets to display.")
        return
    print("\n{:<6}{:<26}{:>9}{:>7}{:>9}{:>7}  Source".format(
        "ID", "Name", "Records", "Vars", "Missing", "Dupes"))
    print("-" * 80)
    for r in valid_records:
        print("{:<6}{:<26}{:>9}{:>7}{:>9}{:>7}  {}".format(
            r["dataset_id"], r["dataset_name"], r["number_of_records"],
            r["number_of_variables"], r["missing_values"], r["duplicate_records"],
            r["source_type"]))
    print("\nTotal valid datasets: {}".format(len(valid_records)))


def assess_data_quality(valid_records):
    if not valid_records:
        print("\nNo valid datasets to assess.")
        return
    ordered = sort_by_quality(valid_records)
    print("\n{:<6}{:<26}{:>10}  Quality".format("ID", "Name", "Missing %"))
    print("-" * 65)
    for r in ordered:
        print("{:<6}{:<26}{:>9.2f}%  {}".format(
            r["dataset_id"], r["dataset_name"], r["missing_percentage"], r["quality_class"]))

    counts = {"Excellent": 0, "Satisfactory": 0, "Needs improvement": 0}
    for r in valid_records:
        counts[r["quality_class"]] += 1
    print("\nQuality classification counts:")
    for label in ("Excellent", "Satisfactory", "Needs improvement"):
        print("  {}: {}".format(label, counts[label]))


def search_dataset(valid_records):
    term = input("\nEnter a dataset ID or part of the dataset name: ").strip().lower()
    if not term:
        print("Search term cannot be empty.")
        return
    matches = [
        r for r in valid_records
        if term == r["dataset_id"].lower() or term in r["dataset_name"].lower()
    ]
    if not matches:
        print("No dataset found matching '{}'.".format(term))
        return
    for r in matches:
        print("\n{} - {}".format(r["dataset_id"], r["dataset_name"]))
        print("  Records: {}, Variables: {}".format(r["number_of_records"], r["number_of_variables"]))
        print("  Missing values: {} ({:.2f}%)".format(r["missing_values"], r["missing_percentage"]))
        print("  Duplicate records: {}".format(r["duplicate_records"]))
        print("  Source type: {}".format(r["source_type"]))
        print("  Quality classification: {}".format(r["quality_class"]))
        print("  Contains personal data: {}".format(r["contains_personal_data"]))


def view_personal_data_warnings(valid_records):
    flagged = [r for r in valid_records if r["contains_personal_data"]]
    if not flagged:
        print("\nNo datasets are flagged as containing personal data.")
        return
    print("\n{} dataset(s) contain personal data:".format(len(flagged)))
    for r in flagged:
        print("  WARNING: {} - {} ({})".format(r["dataset_id"], r["dataset_name"], r["source_type"]))


def view_invalid_records(invalid_records):
    if not invalid_records:
        print("\nNo invalid records were found.")
        return
    print("\n{} invalid record(s):".format(len(invalid_records)))
    for r in invalid_records:
        print("  {} - {}: {}".format(r["dataset_id"], r["dataset_name"], r["reason"]))


def view_portfolio_summary(valid_records, invalid_records, raw_records):
    summary = build_summary(valid_records, invalid_records, raw_records)
    print("\nPORTFOLIO SUMMARY")
    print("  Supplied records:            {}".format(summary["supplied_count"]))
    print("  Valid records:               {}".format(summary["valid_count"]))
    print("  Invalid records:             {}".format(summary["invalid_count"]))
    print("  Total records (valid sets):  {}".format(summary["total_valid_records"]))
    print("  Datasets with personal data: {}".format(summary["personal_data_count"]))

    print("\n  Quality classification counts:")
    for label in ("Excellent", "Satisfactory", "Needs improvement"):
        print("    {}: {}".format(label, summary["quality_counts"][label]))

    print("\n  Datasets by source type:")
    for source, count in summary["source_type_counts"].items():
        print("    {}: {}".format(source, count))

    if summary["most_records"]:
        r = summary["most_records"]
        print("\n  Most records:      {} - {} ({} records)".format(
            r["dataset_id"], r["dataset_name"], r["number_of_records"]))
    if summary["most_variables"]:
        r = summary["most_variables"]
        print("  Most variables:    {} - {} ({} variables)".format(
            r["dataset_id"], r["dataset_name"], r["number_of_variables"]))
    if summary["highest_missing_percentage"]:
        r = summary["highest_missing_percentage"]
        print("  Highest missing %: {} - {} ({:.2f}%)".format(
            r["dataset_id"], r["dataset_name"], r["missing_percentage"]))


# ---------------------------------------------------------------------------
# Program entry point
# ---------------------------------------------------------------------------

def main():
    raw_records = load_records(DATA_FILE)
    valid_records, invalid_records = validate_all(raw_records)

    while True:
        display_menu()
        choice = input("Enter selection: ").strip()
        if choice == "1":
            view_dataset_metadata(valid_records)
        elif choice == "2":
            assess_data_quality(valid_records)
        elif choice == "3":
            search_dataset(valid_records)
        elif choice == "4":
            view_personal_data_warnings(valid_records)
        elif choice == "5":
            view_invalid_records(invalid_records)
        elif choice == "6":
            view_portfolio_summary(valid_records, invalid_records, raw_records)
        elif choice == "7":
            print("Program closed.")
            break
        else:
            print("Invalid selection. Please choose an option from 1 to 7.")


if __name__ == "__main__":
    main()
