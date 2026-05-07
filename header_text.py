def header_data(formatted_date,region_name,trend,stddev):
    """
    Takes date of last timestamp and region name: Antarctic, Greenland or Ocean 
    Generates Header for corresponding region GRACE-FO mascon output
    """
    if region_name == "antarctica":
        header_text = [
        "HDR Antarctica Mass",
        "HDR",
        "HDR Data from the GRACE and GRACE-FO JPL RL06.3Mv4 Mascon Solution",
        "HDR",
        "HDR This file contains values that are anomalies relative to April 2002 computed at the Jet Propulsion Laboratory under the",
        "HDR auspices of the NASA MEaSUREs program. The Greenland mass anomalies are generated using GRACE and GRACE-FO data from the JPL RL06.3Mv4",
        "HDR Mascon Solution (https://podaac.jpl.nasa.gov/dataset/TELLUS_GRACE_MASCON_CRI_GRID_RL06.3_V4).",
        "HDR",
        f"HDR Antarctic Mass Trend (04/2002 - {formatted_date}): {trend:.2f} +/-{stddev:.2f} Gt/yr", 
        "HDR",
        "HDR If you use these data please cite:",
        "HDR Wiese, D. N., D.-N. Yuan, C. Boening, F. W. Landerer, and M. M. Watkins (2022) JPL GRACE and GRACE-FO Mascon Ocean, Ice, and Hydrology Equivalent",
        "HDR Water Height RL06.3M CRI Filtered Version 4.0, Ver. 4.0, PO.DAAC, CA, USA. Dataset accessed [YYYY-MM-DD] at http://dx.doi.org/10.5067/TEMSC-3JC634.",
        "HDR",
        "HDR For information on how the data were generated please refer to:",
        "HDR Watkins, M. M., D. N. Wiese, D. -N. Yuan, C. Boening, and F. W. Landerer (2015), Improved methods for observing Earth's time variable",
        "HDR mass distribution with GRACE using spherical cap mascons, J. Geophys. Res. Solid Earth, 120, 2648_2671, doi: 10.1002/2014JB011547.",
        "HDR",
        "HDR column description",
        "HDR 1 TIME (year.decimal)",
        "HDR 2 Antarctic mass (Gigatonnes)",
        "HDR 3 Antarctic mass 1-sigma uncertainty (Gigatonnes)",
        "HDR",
        "HDR NOTES (1): Correction for Glacial Isostatic Adjustment (GIA) is from ICE6G-D, Peltier. et al. (2018), doi:10.1093/gji/ggs030",
        "HDR NOTES (2): Trend value is derived by performing a weighted least squares fit of an annual, semiannual, bias, and trend to the timeseries",
        "HDR NOTES (3): Monthly uncertainties are computed using measurement errors provided in the JPL RL06.3Mv4 Solution and considering",
        "HDR            leakage errors in accordance with Wiese et al. (2016), doi:10.1002/2016WR019344",
        "HDR NOTES (4): The trend uncertainty provides a 1-sigma confidence interval. The calculation considers only the propagation of the monthly uncertainties",
        "HDR            into the trend, assumes uncorrelated observations, and includes GIA uncertainty according to Velicogna et al. (2013), doi:10.1002/grl.50527",
        "HDR",
        "HDR Header_End---------------------------------------"
        ]
    elif region_name == "greenland":
        header_text = [
        "HDR Greenland Mass",
        "HDR",
        "HDR Data from the GRACE and GRACE-FO JPL RL06.3Mv4 Mascon Solution",
        "HDR",
        "HDR This file contains values that are anomalies relative to April 2002 computed at the Jet Propulsion Laboratory under the",
        "HDR auspices of the NASA MEaSUREs program. The Greenland mass anomalies are generated using GRACE and GRACE-FO data from the JPL RL06.3Mv4",
        "HDR Mascon Solution (https://podaac.jpl.nasa.gov/dataset/TELLUS_GRACE_MASCON_CRI_GRID_RL06.3_V4).",
        "HDR",
        f"HDR Greenland Mass Trend (04/2002 - {formatted_date}): {trend:.2f} +/-{stddev:.2f} Gt/yr", 
        "HDR",
        "HDR If you use these data please cite:",
        "HDR Wiese, D. N., D.-N. Yuan, C. Boening, F. W. Landerer, and M. M. Watkins (2022) JPL GRACE and GRACE-FO Mascon Ocean, Ice, and Hydrology Equivalent",
        "HDR Water Height RL06.3M CRI Filtered Version 4.0, Ver. 4.0, PO.DAAC, CA, USA. Dataset accessed [YYYY-MM-DD] at http://dx.doi.org/10.5067/TEMSC-3JC634.",
        "HDR",
        "HDR For information on how the data were generated please refer to:",
        "HDR Watkins, M. M., D. N. Wiese, D. -N. Yuan, C. Boening, and F. W. Landerer (2015), Improved methods for observing Earth's time variable",
        "HDR mass distribution with GRACE using spherical cap mascons, J. Geophys. Res. Solid Earth, 120, 2648_2671, doi: 10.1002/2014JB011547.",
        "HDR",
        "HDR column description",
        "HDR 1 TIME (year.decimal)",
        "HDR 2 Greenland mass (Gigatonnes)",
        "HDR 3 Greenland mass 1-sigma uncertainty (Gigatonnes)",
        "HDR",
        "HDR NOTES (1): Correction for Glacial Isostatic Adjustment (GIA) is from ICE6G-D, Peltier. et al. (2018), doi:10.1093/gji/ggs030",
        "HDR NOTES (2): Trend value is derived by performing a weighted least squares fit of an annual, semiannual, bias, and trend to the timeseries",
        "HDR NOTES (3): Monthly uncertainties are computed using measurement errors provided in the JPL RL06.3Mv4 Solution and considering",
        "HDR            leakage errors in accordance with Wiese et al. (2016), doi:10.1002/2016WR019344 and Schlegel et al. (2016), doi:10.5194/tc-10-1965-2016",
        "HDR NOTES (4): The trend uncertainty provides a 1-sigma confidence interval. The calculation considers only the propagation of the monthly uncertainties",
        "HDR            into the trend, assumes uncorrelated observations, and includes GIA uncertainty according to Velicogna et al. (2013), doi:10.1002/grl.50527",
        "HDR",
        "HDR Header_End---------------------------------------"
        ]
    elif region_name == "ocean":
        header_text = [
        "HDR Global Ocean Mass",
        "HDR",
        "HDR Data from the GRACE and GRACE-FO JPL RL06.3Mv4 Mascon Solution",
        "HDR",
        "HDR This file contains values that are anomalies relative to April 2002 computed at the Jet Propulsion Laboratory under the",
        "HDR auspices of the NASA MEaSUREs program. The global ocean mass anomalies are generated using GRACE and GRACE-FO data from the JPL RL06.3Mv4",
        "HDR Mascon Solution (https://podaac.jpl.nasa.gov/dataset/TELLUS_GRACE_MASCON_CRI_GRID_RL06.3_V4).",
        "HDR",
        f"HDR Ocean Mass Trend (04/2002 - {formatted_date}): {trend:.2f} +/-{stddev:.2f} mm/yr of sea level height", 
        "HDR",
        "HDR If you use these data please cite:",
        "HDR Wiese, D. N., D.-N. Yuan, C. Boening, F. W. Landerer, and M. M. Watkins (2022) JPL GRACE and GRACE-FO Mascon Ocean, Ice, and Hydrology Equivalent",
        "HDR Water Height RL06.3M CRI Filtered Version 4.0, Ver. 4.0, PO.DAAC, CA, USA. Dataset accessed [YYYY-MM-DD] at http://dx.doi.org/10.5067/TEMSC-3JC634.",
        "HDR",
        "HDR For information on how the data were generated please refer to:",
        "HDR Watkins, M. M., D. N. Wiese, D. -N. Yuan, C. Boening, and F. W. Landerer (2015), Improved methods for observing Earth's time variable",
        "HDR mass distribution with GRACE using spherical cap mascons, J. Geophys. Res. Solid Earth, 120, 2648_2671, doi: 10.1002/2014JB011547.",
        "HDR",
        "HDR column description",
        "HDR 1 TIME (year.decimal)",
        "HDR 2 Ocean mass (mm of sea level height)",
        "HDR 3 Ocean mass 1-sigma uncertainty (mm of sea level height)",
        "HDR 4 Ocean mass deseasoned (mm of sea level height)",
        "HDR",
        "HDR NOTES (1): Ocean mass is computed by summing up mass anomalies over the ocean in the JPL RL06.3Mv4 solution",
        "HDR            and removing the mass of the atmosphere.",
        "HDR NOTES (2): The deseasoned ocean mass timeseries is obtained by fitting an annual, semiannual, and bias to the full timeseries and removing it.",
        "HDR NOTES (3): Correction for Glacial Isostatic Adjustment (GIA) is from ICE6G-D, Peltier. et al. (2018), doi:10.1093/gji/ggs030",
        "HDR NOTES (4): Trend value is derived by performing a weighted least squares fit of an annual, semiannual, bias, and trend to the timeseries",
        "HDR NOTES (5): Monthly uncertainties are computed using measurement errors provided in the JPL RL06.3Mv4 Solution and considering",
        "HDR            leakage errors in accordance with Wiese et al. (2016), doi:10.1002/2016WR019344",
        "HDR NOTES (6): The trend uncertainty provides a 1-sigma confidence interval. The calculation considers only the propagation of the monthly uncertainties",
        "HDR            into the trend, assumes uncorrelated observations, and includes GIA uncertainty according to Chambers et al. (2016), doi:10.1007/s10712-016-9381-3",
        "HDR",
        "HDR Header_End---------------------------------------"
        ]
    else:
        print('Error: Invalid input')

    return header_text
    
    