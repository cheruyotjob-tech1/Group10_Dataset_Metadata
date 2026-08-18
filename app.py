import streamlit as st
import pandas as pd
import requests
from io import StringIO

# ------------------------------------------------------------
# Dataset Metadata and Quality Assessment Tool - Streamlit
# ------------------------------------------------------------

st.set_page_config(
    page_title="Dataset Metadata & Quality Assessment",
    page_icon="📊",
    layout="wide",
)

DATA_URL = (
    "https://raw.githubusercontent.com/"
    "cheruyotjob-tech1/Group10_Dataset_Metadata/main/"
    "data/10_Dataset_Metadata.csv"
)

RECOGNIZED_SOURCE_TYPES = {"Survey", "Administrative", "Sensor", "CSV"}
QUALITY_RANK = {"Excellent": 0, "Satisfactory": 1, "Needs improvement": 2}


@st.cache_data(ttl=3600)
def load_records(url):
    """Load the metadata CSV directly from GitHub."""
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return pd.read_csv(StringIO(response.text), dtype=str).fillna("")


def to_int(value):
    try:
        value = str(value).strip()
        return int(value) if value else None
    except (TypeError, ValueError):
        return None


def to_bool(value):
    value = str(value).strip().upper()
    if value == "TRUE":
        return True
    if value == "FALSE":
        return False
    return None


def validate_record(row):
    dataset_id = str(row.get("dataset_id", "")).strip()
    dataset_name = str(row.get("dataset_name", "")).strip()
    number_of_records = to_int(row.get("number_of_records"))
    number_of_variables = to_int(row.get("number_of_variables"))
    missing_values = to_int(row.get("missing_values"))
    duplicate_records = to_int(row.get("duplicate_records"))
    source_type = str(row.get("source_type", "")).strip()
    contains_personal_data = to_bool(row.get("contains_personal_data"))

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
        return False, f"Source type '{source_type}' is not recognised.", None

    if contains_personal_data is None:
        return False, "Contains-personal-data value must be TRUE or FALSE.", None

    clean = {
        "dataset_id": dataset_id,
        "dataset_name": dataset_name,
        "number_of_records": number_of_records,
        "number_of_variables": number_of_variables,
        "missing_values": missing_values,
        "duplicate_records": duplicate_records,
        "source_type": source_type,
        "contains_personal_data": contains_personal_data,
    }

    missing_percentage = missing_values / number_of_records * 100

    if missing_percentage < 5:
        quality = "Excellent"
    elif missing_percentage < 10:
        quality = "Satisfactory"
    else:
        quality = "Needs improvement"

    clean["missing_percentage"] = missing_percentage
    clean["quality_class"] = quality

    return True, "", clean


@st.cache_data
def process_data(df):
    valid_records = []
    invalid_records = []

    for _, row in df.iterrows():
        valid, reason, clean = validate_record(row.to_dict())

        if valid:
            valid_records.append(clean)
        else:
            invalid_records.append({
                "dataset_id": str(row.get("dataset_id", "")).strip() or "(missing)",
                "dataset_name": str(row.get("dataset_name", "")).strip() or "(missing)",
                "reason": reason,
            })

    valid_df = pd.DataFrame(valid_records)
    invalid_df = pd.DataFrame(invalid_records)

    return valid_df, invalid_df


def portfolio_summary(valid_df, invalid_df, raw_df):
    quality_counts = (
        valid_df["quality_class"].value_counts().to_dict()
        if not valid_df.empty else {}
    )

    source_counts = (
        valid_df["source_type"].value_counts().to_dict()
        if not valid_df.empty else {}
    )

    personal_count = (
        int(valid_df["contains_personal_data"].sum())
        if not valid_df.empty else 0
    )

    most_records = (
        valid_df.loc[valid_df["number_of_records"].idxmax()]
        if not valid_df.empty else None
    )

    most_variables = (
        valid_df.loc[valid_df["number_of_variables"].idxmax()]
        if not valid_df.empty else None
    )

    highest_missing = (
        valid_df.loc[valid_df["missing_percentage"].idxmax()]
        if not valid_df.empty else None
    )

    return {
        "supplied_count": len(raw_df),
        "valid_count": len(valid_df),
        "invalid_count": len(invalid_df),
        "total_valid_records": int(valid_df["number_of_records"].sum()) if not valid_df.empty else 0,
        "quality_counts": quality_counts,
        "source_counts": source_counts,
        "personal_count": personal_count,
        "most_records": most_records,
        "most_variables": most_variables,
        "highest_missing": highest_missing,
    }


# ------------------------------------------------------------
# Load data
# ------------------------------------------------------------

st.title("📊 Dataset Metadata & Quality Assessment Tool")
st.caption("MSc Fundamentals of Programming — Capstone Project (Project 10)")

try:
    raw_df = load_records(DATA_URL)
    valid_df, invalid_df = process_data(raw_df)
except Exception as e:
    st.error("Unable to load the dataset from GitHub.")
    st.exception(e)
    st.stop()

summary = portfolio_summary(valid_df, invalid_df, raw_df)

# ------------------------------------------------------------
# Sidebar navigation
# ------------------------------------------------------------

st.sidebar.title("Navigation")

page = st.sidebar.radio(
    "Select an option",
    [
        "Portfolio Summary",
        "Dataset Metadata",
        "Data Quality",
        "Search Dataset",
        "Personal Data Warnings",
        "Invalid Records",
    ],
)

st.sidebar.divider()
st.sidebar.success(f"Loaded {len(raw_df):,} metadata records")
st.sidebar.caption("Data source: GitHub repository")


# ------------------------------------------------------------
# Portfolio Summary
# ------------------------------------------------------------

if page == "Portfolio Summary":
    st.header("Portfolio Summary")

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Supplied Records", f"{summary['supplied_count']:,}")
    c2.metric("Valid Records", f"{summary['valid_count']:,}")
    c3.metric("Invalid Records", f"{summary['invalid_count']:,}")
    c4.metric("Total Records Represented", f"{summary['total_valid_records']:,}")

    st.divider()

    left, right = st.columns(2)

    with left:
        st.subheader("Quality Classification")

        quality_order = ["Excellent", "Satisfactory", "Needs improvement"]
        quality_data = pd.DataFrame({
            "Quality": quality_order,
            "Datasets": [
                summary["quality_counts"].get(q, 0)
                for q in quality_order
            ],
        })

        st.bar_chart(quality_data.set_index("Quality"))

    with right:
        st.subheader("Datasets by Source Type")

        source_data = pd.DataFrame(
            list(summary["source_counts"].items()),
            columns=["Source Type", "Datasets"],
        )

        if not source_data.empty:
            st.bar_chart(source_data.set_index("Source Type"))

    st.divider()

    c1, c2, c3 = st.columns(3)

    if summary["most_records"] is not None:
        r = summary["most_records"]
        c1.info(
            f"**Most Records**\n\n"
            f"{r['dataset_id']} — {r['dataset_name']}\n\n"
            f"{int(r['number_of_records']):,} records"
        )

    if summary["most_variables"] is not None:
        r = summary["most_variables"]
        c2.info(
            f"**Most Variables**\n\n"
            f"{r['dataset_id']} — {r['dataset_name']}\n\n"
            f"{int(r['number_of_variables']):,} variables"
        )

    if summary["highest_missing"] is not None:
        r = summary["highest_missing"]
        c3.warning(
            f"**Highest Missing Percentage**\n\n"
            f"{r['dataset_id']} — {r['dataset_name']}\n\n"
            f"{r['missing_percentage']:.2f}% missing"
        )

    st.metric("Datasets Containing Personal Data", summary["personal_count"])


# ------------------------------------------------------------
# Dataset Metadata
# ------------------------------------------------------------

elif page == "Dataset Metadata":
    st.header("Dataset Metadata")

    if valid_df.empty:
        st.warning("No valid datasets to display.")
    else:
        display_df = valid_df[
            [
                "dataset_id",
                "dataset_name",
                "number_of_records",
                "number_of_variables",
                "missing_values",
                "duplicate_records",
                "source_type",
                "contains_personal_data",
            ]
        ].copy()

        display_df.columns = [
            "ID",
            "Name",
            "Records",
            "Variables",
            "Missing",
            "Duplicates",
            "Source",
            "Personal Data",
        ]

        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
        )

        st.info(f"Total valid datasets: {len(valid_df):,}")


# ------------------------------------------------------------
# Data Quality
# ------------------------------------------------------------

elif page == "Data Quality":
    st.header("Data Quality Assessment")

    if valid_df.empty:
        st.warning("No valid datasets to assess.")
    else:
        quality_filter = st.multiselect(
            "Filter by quality classification",
            ["Excellent", "Satisfactory", "Needs improvement"],
            default=["Excellent", "Satisfactory", "Needs improvement"],
        )

        quality_df = valid_df[
            valid_df["quality_class"].isin(quality_filter)
        ].copy()

        quality_df = quality_df.sort_values(
            ["quality_class", "missing_percentage"],
            key=lambda col: (
                col.map(QUALITY_RANK)
                if col.name == "quality_class"
                else col
            ),
        )

        display_df = quality_df[
            [
                "dataset_id",
                "dataset_name",
                "missing_percentage",
                "quality_class",
            ]
        ].copy()

        display_df["missing_percentage"] = display_df["missing_percentage"].map(
            lambda x: f"{x:.2f}%"
        )

        display_df.columns = [
            "ID",
            "Name",
            "Missing %",
            "Quality",
        ]

        st.dataframe(display_df, use_container_width=True, hide_index=True)

        counts = (
            quality_df["quality_class"]
            .value_counts()
            .reindex(
                ["Excellent", "Satisfactory", "Needs improvement"],
                fill_value=0,
            )
        )

        st.subheader("Quality Classification Counts")
        st.bar_chart(counts)


# ------------------------------------------------------------
# Search Dataset
# ------------------------------------------------------------

elif page == "Search Dataset":
    st.header("Search for a Dataset")

    term = st.text_input(
        "Enter a dataset ID or part of the dataset name",
        placeholder="e.g. DS001 or customer",
    ).strip().lower()

    if term:
        matches = valid_df[
            valid_df["dataset_id"].str.lower().eq(term)
            | valid_df["dataset_name"].str.lower().str.contains(
                term, na=False, regex=False
            )
        ]

        if matches.empty:
            st.warning(f"No dataset found matching '{term}'.")
        else:
            st.success(f"{len(matches)} dataset(s) found.")

            for _, r in matches.iterrows():
                with st.expander(
                    f"{r['dataset_id']} — {r['dataset_name']}",
                    expanded=True,
                ):
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Records", f"{int(r['number_of_records']):,}")
                    c2.metric("Variables", f"{int(r['number_of_variables']):,}")
                    c3.metric("Missing %", f"{r['missing_percentage']:.2f}%")

                    st.write(f"**Missing values:** {int(r['missing_values']):,}")
                    st.write(f"**Duplicate records:** {int(r['duplicate_records']):,}")
                    st.write(f"**Source type:** {r['source_type']}")
                    st.write(
                        f"**Quality classification:** {r['quality_class']}"
                    )
                    st.write(
                        f"**Contains personal data:** "
                        f"{'Yes' if r['contains_personal_data'] else 'No'}"
                    )


# ------------------------------------------------------------
# Personal Data Warnings
# ------------------------------------------------------------

elif page == "Personal Data Warnings":
    st.header("⚠️ Personal Data Warnings")

    flagged = valid_df[valid_df["contains_personal_data"]].copy()

    if flagged.empty:
        st.success("No datasets are flagged as containing personal data.")
    else:
        st.warning(
            f"{len(flagged)} dataset(s) contain personal data. "
            "Review these datasets carefully."
        )

        display_df = flagged[
            ["dataset_id", "dataset_name", "source_type", "quality_class"]
        ].copy()

        display_df.columns = ["ID", "Name", "Source Type", "Quality"]

        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
        )


# ------------------------------------------------------------
# Invalid Records
# ------------------------------------------------------------

elif page == "Invalid Records":
    st.header("Invalid Records")

    if invalid_df.empty:
        st.success("No invalid records were found.")
    else:
        st.warning(f"{len(invalid_df)} invalid record(s) found.")

        st.dataframe(
            invalid_df,
            use_container_width=True,
            hide_index=True,
        )

        csv_data = invalid_df.to_csv(index=False).encode("utf-8")

        st.download_button(
            "Download Invalid Records CSV",
            data=csv_data,
            file_name="invalid_records.csv",
            mime="text/csv",
        )

st.divider()
st.caption(
    "Dataset Metadata and Quality Assessment Tool • "
    "Data loaded from the Group10_Dataset_Metadata GitHub repository"
)
