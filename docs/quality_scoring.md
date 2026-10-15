# Data Quality Scoring Methodology

ExcelPilot measures data quality across four objective dimensions: Completeness, Validity, Uniqueness, and Consistency. The composite quality score is calculated as a weighted index ranging from 0.0 to 100.0.

## Dimensions

### 1. Completeness (Weight: 30%)
Completeness measures the proportion of populated, non-null values across all cells in the dataset.
- Formula: `Score = max(0.0, 100.0 - (total_null_cells / (total_rows * total_columns) * 100.0))`
- Mandatory Columns: If a column is defined as `nullable: false` or classified as an `IDENTIFIER`, any missing value generates a `HIGH` severity defect.
- General Columns: Missing values exceeding 25% of total rows generate `MEDIUM` severity defects; smaller proportions generate `LOW` severity defects.

### 2. Validity (Weight: 30%)
Validity measures conformance with business rules, allowed domain sets, and logical constraints.
- Range Constraints: Values below `minimum` or above `maximum` deduct points proportional to the affected record percentage.
- Semantic Boundaries: Monetary values (`CURRENCY`) and order quantities are checked for unexpected negative numbers.
- Domain Sets: Columns configured with `allowed_values` verify that every observed category belongs to the authorised dictionary.

### 3. Uniqueness (Weight: 20%)
Uniqueness measures the absence of duplicate rows and primary key collisions.
- Full Row Duplicates: Points are deducted directly proportional to duplicate row frequency: `Score = max(0.0, 100.0 - duplicate_rows_percentage)`.
- Key Uniqueness: Columns classified as `IDENTIFIER` are audited for uniqueness. Any non-unique keys generate a `HIGH` severity defect.

### 4. Consistency (Weight: 20%)
Consistency measures uniformity in data representation and text encoding.
- Whitespace Integrity: String columns are scanned for untrimmed leading or trailing whitespace (e.g. `" Hardware "`), which can cause unintended grouping splits.
- Type Uniformity: Inconsistencies between physical storage types and expected semantic schemas are flagged.

## Composite Quality Score

The overall score is computed as:

$$\text{Overall Score} = 0.30 \times \text{Completeness} + 0.30 \times \text{Validity} + 0.20 \times \text{Uniqueness} + 0.20 \times \text{Consistency}$$

## Defect Severity Levels

- **HIGH**: Critical data integrity issues (duplicate primary keys, negative quantities, missing mandatory fields).
- **MEDIUM**: Significant anomalies (high null percentages, values exceeding bounds).
- **LOW**: Minor formatting inconsistencies (untrimmed whitespace, low-frequency missing values in non-essential fields).
