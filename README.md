# GRACE and GRACE-FO Open Science Tutorials

This repository contains applied science tutorials as notebooks using GRACE and GRACE-FO satellite data.
GRACE Mascons have been used for the terrestrial water storage variable along with its uncertainty. The most updated dataset can be downloaded from PO.DAAC: https://podaac.jpl.nasa.gov/dataset/TELLUS_GRAC-GRFO_MASCON_CRI_GRID_RL06.3_V4

## Environment Setup

The notebooks can be run using a Miniforge / conda-forge environment to ensure a fully reproducible, cross-platform setup (Windows, macOS, Linux) without any Anaconda licensing dependencies.

### Steps to create the conda environment after installing Miniforge:
1. Create the environment

From the project root directory, run:

conda env create -f environment.yml -n grace_notebooks

2. Activate the environment:
   
conda activate grace_notebooks

3. Launch Jupyter:

jupyter notebook

This will open Jupyter in your default web browser.

## Tutorials

### GRACE Level 3 User handbook case studies:
1. Colorado River Basin: https://github.com/NASA-GRACE/GRACE-Analysis-Tutorials/blob/main/Tellus_GRACE_TWS_basin_mean.ipynb
2. Ocean Mass Budget: https://github.com/NASA-GRACE/GRACE-Analysis-Tutorials/blob/main/GRACE_handbook_gmsl_budget.ipynb

### GRACE Level 4 climate indicators 
1. Ice Sheets (Greenland and Antarctica): https://github.com/NASA-GRACE/GRACE-Analysis-Tutorials/blob/main/GRACE_Ice_Sheets_tutorial.ipynb
2. Ocean Mass: https://github.com/NASA-GRACE/GRACE-Analysis-Tutorials/blob/main/Ocean_Mass_tutorial.ipynb

Header info stored in the output text files is compatible with L4 datasets produced under RL0603 v04. This header info is read from header_text.py and can be modified to match future release metadata.


#### Backend functions are provided in:
grace_user_functions.py
trend_fit.py

