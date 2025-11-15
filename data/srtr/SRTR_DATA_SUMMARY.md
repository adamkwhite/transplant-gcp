# SRTR Transplant Outcomes Data Summary

## Data Source
- **Organization**: Scientific Registry of Transplant Recipients (SRTR)
- **Report**: 2023 Annual Data Report
- **Coverage**: US transplants 2012-2023
- **Location**: `/home/adam/Code/transplant-gcp/data/srtr/raw/`

## Available Files

1. **Kidney_Figures_Supporting_Information.xlsx** (21MB, 164 sheets)
2. **Liver_Figures_Supporting_Information.xlsx** (17MB)
3. **Heart_Figures_Supporting_Information.xlsx** (15MB)
4. **Pancreas_Figures_Supporting_Information.xlsx** (8.9MB)
5. **Lung_Figures_Supporting_Information.xlsx** (11MB)
6. **Intestine_Figures_Supporting_Information.xlsx** (6.1MB)

## Key Kidney Transplant Data Sheets

### Graft Survival (Post-Transplant)
- **KI-F61-tx-adult-GF-LD-5yr-age**: Graft failure rates by age (living donor)
- **KI-F62-tx-adult-GF-LD-5yr-race**: Graft failure rates by race
- **KI-F63-tx-adult-GF-LD-5yr-sex**: Graft failure rates by sex
- **KI-F64-tx-adult-GF-LD-5yr-diag**: Graft failure rates by diagnosis

**Data Format**:
- Columns: Years after transplant, age groups (18-34, 35-49, 50-64, 65+)
- Values: Graft survival percentage (starts at ~99%, declines over time)
- Time granularity: Sub-annual intervals over 5 years

### Acute Rejection Incidence
- **KI-F67-tx-adult-inc-AR-age**: Acute rejection rates by age (2012-2022)
- **KI-F68-tx-adult-inc-AR-ind**: Acute rejection rates by induction therapy

**Data Format**:
- Columns: Year, age groups
- Values: Rejection rate percentage
- Example 2022 rates:
  - 18-34 years: 7.99%
  - 35-49 years: 6.19%
  - 50-64 years: 5.43%
  - 65+ years: 5.11%

### Patient Survival
- **KI-F70 to KI-F78**: Patient survival rates by various demographics
  - Deceased donor (DD) and living donor (LD)
  - 5-year survival data
  - Stratified by age, race, sex, diagnosis

### Kidney Function
- **KI-F65-tx-adult-egfr-12M-dd**: eGFR at 12 months post-transplant (deceased donor)
- **KI-F66-tx-adult-egfr-12M-ld**: eGFR at 12 months post-transplant (living donor)

### Post-Transplant Complications
- **KI-F69-tx-adult-ptld**: Post-transplant lymphoproliferative disorder rates

## Relevant Data for Medication Adherence System

### High-Value Sheets for Our Use Case:

1. **Graft Survival by Time Post-Transplant** (KI-F61-64)
   - Use to estimate rejection risk at different time points
   - Factor into missed dose risk assessment

2. **Acute Rejection Rates** (KI-F67-68)
   - Baseline rejection probabilities
   - Age-stratified risks
   - Can compare patient's risk profile

3. **eGFR Data** (KI-F65-66)
   - Kidney function outcomes
   - Indicator of transplant health

## Potential Use Cases

### 1. Risk Stratification
Compare patient characteristics (age, time post-transplant) against SRTR population data to assess relative risk.

**Example**:
```python
# Patient: 45 years old, 6 months post-transplant
age_group = "35-49"
months_post = 6

# Query SRTR data
baseline_rejection_rate = get_rejection_rate(age_group=age_group)  # ~6.2%
graft_survival = get_graft_survival(months_post=months_post)  # ~99.5%

# Factor into AI recommendation
if baseline_rejection_rate > 7.0 and hours_late > 12:
    risk_level = "high"
```

### 2. Outcome Prediction
Use historical outcomes to inform missed dose recommendations.

### 3. Comparative Analysis
Show patient how their adherence compares to population norms.

### 4. Evidence-Based Recommendations
Ground AI recommendations in real clinical outcomes data.

## Next Steps

### Phase 1: Data Extraction (This Week)
1. Parse key sheets into structured JSON/CSV
2. Extract:
   - Graft survival curves (by age, time)
   - Rejection rates (by age, year)
   - Patient survival rates
3. Store in `/data/srtr/processed/`

### Phase 2: Firestore Integration (Next Week)
1. Create Firestore collection: `srtr_outcomes`
2. Structure:
   ```json
   {
     "organ": "kidney",
     "metric": "graft_survival",
     "age_group": "35-49",
     "months_post_transplant": 6,
     "survival_rate": 99.52,
     "source": "SRTR 2023",
     "year": 2023
   }
   ```
3. Query from ADK agents during analysis

### Phase 3: Agent Integration (Week After)
1. Modify `MedicationAdvisorAgent` to query SRTR data
2. Include population statistics in prompt context
3. Enable evidence-based risk assessment

## Data Licensing & Citation

**Citation**:
```
Organ Procurement and Transplantation Network (OPTN) and Scientific Registry of
Transplant Recipients (SRTR). OPTN/SRTR 2023 Annual Data Report.
U.S. Department of Health and Human Services, Health Resources and Services
Administration; 2025. https://srtr.transplant.hrsa.gov/annualdatareports
```

**Usage**: Public data, free to use for research and clinical decision support.

## Technical Notes

- Excel files contain multiple unnamed columns (formatting artifacts)
- Actual data starts at column 8-9
- Some sheets have trailing NaN rows
- Data is de-identified and aggregated (no patient-level details)
- Time granularity varies by sheet (annual, sub-annual intervals)

---

**Last Updated**: 2025-11-08
**Maintainer**: transplant-gcp project
