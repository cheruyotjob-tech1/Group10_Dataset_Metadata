# Algorithm — Dataset Metadata and Quality Assessment Tool

This mirrors the two flowcharts prepared before coding: (1) load and
validate records, (2) classify quality and build the summary.

## Part 1 — Load and validate records

START
LOAD dataset records from 10_Dataset_Metadata.csv
CREATE empty valid_list, invalid_list

WHILE more records remain
    GET next raw record
    VALIDATE record:
        - dataset_id and dataset_name are present
        - number_of_records > 0
        - number_of_variables > 0
        - missing_values >= 0
        - duplicate_records >= 0
        - missing_values <= number_of_records
        - duplicate_records <= number_of_records
        - source_type is one of {Survey, Administrative, Sensor}
        - contains_personal_data is TRUE or FALSE
    IF record fails any rule THEN
        ADD record to invalid_list WITH reason
    ELSE
        ADD record to valid_list
    END IF
END WHILE

CONTINUE to quality assessment (Part 2)
```

## Part 2 — Classify quality and build summary

```
FOR EACH record IN valid_list
    missing_percentage = missing_values / number_of_records * 100
    IF missing_percentage < 5 THEN
        quality_class = "Excellent"
    ELSE IF missing_percentage < 10 THEN
        quality_class = "Satisfactory"
    ELSE
        quality_class = "Needs improvement"
    END IF
END FOR

BUILD summary:
    - counts of records by quality_class
    - counts of records by source_type
    - dataset with most records
    - dataset with most variables
    - dataset with highest missing_percentage
    - total records represented by valid datasets
    - count and list of datasets with contains_personal_data = TRUE
    - datasets sorted from highest to lowest quality

DISPLAY results through the menu:
    1. View dataset metadata
    2. Assess data quality
    3. Search for a dataset
    4. View personal-data warnings
    5. View invalid records
    6. View portfolio summary
    7. Exit
END


Visual flowcharts for both parts were produced during design and are
referenced in the README.
