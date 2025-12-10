# Supplementary Materials: EU LDN Data Analysis

This repository contains the source code and supplementary materials for the analysis presented in the article 'Analysis of Multi-Source Default Data of Land Productivity for SDG 15.3.1 assessment on EU drylands"

The analysis focuses on Land Productivity Dynamics (LPD) and SDG 15.3.1 indicator agreement statistics across the European Union.

## Repository Structure

### 1. Jupyter Notebooks (`/notebooks`)
- **`AgreementStatistics.ipynb`**: 
  - Calculates confidence class distributions (High, Moderate, Low) for LPD agreement across 27 EU countries.
  - Generates stacked bar charts visualizing the percentage distribution of confidence levels per country.
  - Processes vector (GADM) and raster data to compute pixel-level statistics.

- **`EU_LDN_DefultDataAnalysis_CorrelationMatrix.ipynb`**:
  - Performs cross-tabulation and correlation analysis between SDG and LPD datasets from different sources (FAO-WOCAT, JRC, TE).
  - Generates heatmaps showing the distribution of SDG vs. LPD classes.
  - Calculates correlation coefficients to assess dataset agreement.

### 2. Python Scripts (`/scripts`)
- **`calculate_statistics.py`**:
  - A standalone script designed to run within the **QGIS Python Console**.
  - Calculates Cohen's Kappa and Fuzzy Kappa statistics to quantify agreement between datasets (TE-JRC, TE-FAO, JRC-FAO).
  - Generates normalized confusion matrices and country-level agreement statistics.

## Dependencies & Usage

To run the Jupyter Notebooks, install the required Python packages:

```bash
pip install -r requirements.txt
