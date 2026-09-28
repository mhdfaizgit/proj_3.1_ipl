project_3.1


## Data Profiling

Data profiling is the process of understanding the dataset before making any changes to it.

### What was done

- Inspected the five IPL tables:
  - `matches`
  - `deliveries`
  - `players`
  - `teams`
  - `venues`
- Checked the number of rows and columns.
- Checked distinct values in important columns.
- Identified missing values and blank values.
- Checked duplicate records.
- Investigated inconsistent names and categories.
- Recorded the identified data quality issues in a Data Quality Log.

### Output

- Data Dictionary
- Data Quality Log
- List of issues that need to be fixed in the next stage

> **Important:** No data was changed during profiling. It was only inspected and documented.

---

## Data Preparation

Data preparation fixes the problems identified during data profiling and creates a clean dataset for analysis.

### What was done

- Converted blank values into proper `NULL` values.
- Standardized inconsistent categories and names.
- Cleaned venue names.
- Removed duplicate venue records.
- Filled missing city values where possible.
- Converted season information into a usable year.
- Defined which matches should be treated as wins.
- Combined the cleaning rules to create `matches_clean`.

The cleaning rules were written in separate SQL files and executed in order.

### Output

A cleaned table called:

`matches_clean`

The raw tables were not modified.

---

## Data Analysis

Data analysis uses the cleaned data to answer cricket-related business questions and find useful patterns.

### Analysis Views

Three main views were created:

- `v_ball` – one row per ball
- `v_innings` – one row per team innings
- `v_match_totals` – one row per completed match

These views make it easier to analyze different levels of IPL data.

### Areas Analyzed

- Batting
- Batting roles
- Innings phases
- Bowling
- Pace vs Spin
- Bowling specialists
- Toss
- Batting first vs Chasing
- Venues
- Teams
- Wickets and dismissals
- Seasons
- Player scouting

### Analysis Process

Each analysis follows a simple process:

**Question → SQL Query → Result → Interpretation → Finding**

Minimum sample requirements are used where necessary to avoid misleading results from very small samples.

### Output

- SQL analysis queries
- Numerical results
- Charts
- Analysis findings and conclusions

The analysis is performed using the cleaned data rather than the original raw tables.

---

## Project Workflow

```text
Raw IPL Data
     ↓
Data Profiling
     ↓
Data Quality Log
     ↓
Data Preparation
     ↓
Cleaned Data
     ↓
Data Analysis
     ↓
Findings & Insights
