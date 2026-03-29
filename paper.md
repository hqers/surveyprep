---
title: "SurveyPrep: A Configurable Framework for Harmonizing Multi-Schema Household Survey Data"
tags:
  - Python
  - data preprocessing
  - data harmonization
  - household surveys
  - reproducibility
  - data engineering
authors:
  - name: Hasta Pratama
    affiliation: 1
  - name: Fetty Fitriyanti Lubis
    affiliation: 1
  - name: Jaka Sembiring
    affiliation: 1
affiliations:
  - name: School of Electrical Engineering and Informatics, Institut Teknologi Bandung, Indonesia
    index: 1
date: 2026
bibliography: paper.bib
---

# Summary

Household survey data are widely used in socio-economic research, but their practical use is often hindered by schema drift across survey waves and systems. Variations in variable names, coding schemes, and data structures require extensive manual preprocessing, leading to non-reproducible workflows. SurveyPrep is a Python-based software framework designed to harmonize heterogeneous survey datasets through a configurable and modular pipeline. The framework enables consistent feature construction across datasets, supporting reproducible analysis for applications such as household segmentation, poverty measurement, and socio-economic modeling.

# Statement of Need

Large-scale household surveys are conducted periodically across time and regions, but their schemas evolve continuously. Variables may change names, coding schemes may shift, and file structures may differ, making integration difficult without manual harmonization. Existing approaches typically rely on hard-coded scripts or static mappings, which are difficult to maintain and reuse.

SurveyPrep addresses this gap by providing a configurable framework that separates schema definitions from processing logic. This enables scalable and reproducible harmonization across multiple datasets and survey systems. The software is particularly useful for researchers working with multi-year or multi-country survey data who require consistent feature representations for downstream analysis.

# State of the Field

Several approaches have been developed for survey data harmonization. Manual methods such as crosswalks and recode scripts provide flexibility but are labor-intensive and difficult to reproduce. Automated approaches, including variable matching techniques and semantic schema models, attempt to reduce manual effort but often struggle with evolving schemas and require manual validation.

Existing tools for reproducible data processing (e.g., workflow-based systems and data packaging frameworks) improve transparency but do not explicitly address schema drift in survey data. SurveyPrep complements these approaches by introducing a configurable adapter-based mechanism to handle schema variability and a modular feature construction system.

# Software Design

SurveyPrep is implemented in Python and organized into a modular pipeline with four main components:

1. **Adapter Layer**  
   Encapsulates dataset-specific schema definitions, including variable mappings, value labels, and file configurations. This isolates schema variability from core processing logic.

2. **Runner System**  
   Implements declarative feature construction using configurable transformation rules. Supports direct mapping, conditional transformation, and aggregation across data modules.

3. **Integration Module**  
   Combines household, individual, and expenditure data into a unified dataset with consistent feature definitions.

4. **Dual-Output Exporter**  
   Produces two datasets: (1) a clustering-ready dataset without survey design variables, and (2) a profiling dataset including weights and design variables for statistical analysis.

The system is designed to be extensible, allowing users to add new survey adapters and feature definitions without modifying core code.

# Example Usage

SurveyPrep can be executed using a simple pipeline interface:

```python
from surveyprep.pipeline import run_susenas_pipeline

df = run_susenas_pipeline(
    data_dir="data/",
    output_dir="outputs/",
    verbose=True
)