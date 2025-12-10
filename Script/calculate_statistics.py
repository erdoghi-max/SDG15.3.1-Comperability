"""
STEP 2: Calculate Agreement Statistics
Run in QGIS Python Console with:
exec(Path('/home/erdoghi/LDN/Codes/calculate_statistics.py').read_text())
"""

import os
import numpy as np
import pandas as pd
from osgeo import gdal
from qgis.core import (
    QgsProject,
    QgsVectorLayer,
    QgsMessageLog,
    Qgis
)
from qgis.analysis import QgsNativeAlgorithms
from processing.core.Processing import Processing

def log_message(message, level=Qgis.Info):
    QgsMessageLog.logMessage(message, 'SDG Step 2', level=level)

def load_data():
    """Load required datasets"""
    input_dir = '/home/erdoghi/LDN/GlobalData/EU'
    
    # Load original datasets
    datasets = {}
    for name in ['FAO', 'JRC', 'TE']:
        path = os.path.join(input_dir, f'clipped_SDG_2015_2019_{name}_EU.tif')
        ds = gdal.Open(path)
        datasets[name] = ds.GetRasterBand(1).ReadAsArray()
        ds = None
    
    # Load agreement map
    agreement_path = os.path.join(input_dir, 'SDG_Agreement_Map.tif')
    agreement = gdal.Open(agreement_path).GetRasterBand(1).ReadAsArray()
    
    # Load country boundaries
    countries = QgsVectorLayer('/home/erdoghi/LDN/GlobalData/gadm_EU.shp', 'countries')
    if not countries.isValid():
        raise Exception("Failed to load country boundaries")
    
    return datasets, agreement, countries

def calculate_kappa(arr1, arr2, valid_mask):
    """Calculate Cohen's Kappa for two arrays"""
    from sklearn.metrics import cohen_kappa_score
    return cohen_kappa_score(
        arr1[valid_mask].flatten(),
        arr2[valid_mask].flatten()
    )

def calculate_fuzzy_kappa(arr1, arr2, valid_mask):
    """Calculate Fuzzy Kappa for ordinal data"""
    # Implement your fuzzy kappa logic here
    # This is a placeholder implementation
    diff = np.abs(arr1[valid_mask] - arr2[valid_mask])
    weights = 1 - (diff / 3)  # Linear weights for ordinal data
    return np.mean(weights)

def create_confusion_matrix(arr1, arr2, valid_mask):
    """Create normalized confusion matrix"""
    from sklearn.metrics import confusion_matrix
    cm = confusion_matrix(
        arr1[valid_mask].flatten(),
        arr2[valid_mask].flatten(),
        labels=[1, 2, 3]  # Degrading, Stable, Improving
    )
    return cm / cm.sum(axis=1, keepdims=True)  # Normalize

def calculate_country_stats(datasets, agreement, countries):
    """Calculate statistics per country"""
    # Rasterize country boundaries
    Processing.initialize()
    QgsApplication.processingRegistry().addProvider(QgsNativeAlgorithms())
    
    temp_raster = '/home/erdoghi/LDN/GlobalData/EU/countries_raster.tif'
    params = {
        'INPUT': countries,
        'FIELD': 'GID_0',  # Country code field
        'OUTPUT': temp_raster
    }
    processing.run("gdal:rasterize", params)
    
    # Load country raster
    country_raster = gdal.Open(temp_raster).GetRasterBand(1).ReadAsArray()
    country_codes = np.unique(country_raster[country_raster != 0])
    
    # Calculate stats per country
    results = []
    for code in country_codes:
        mask = (country_raster == code)
        valid_mask = mask & (agreement > 0)
        
        if np.sum(valid_mask) == 0:
            continue
            
        # Agreement statistics
        high = np.sum(agreement[valid_mask] == 3) / np.sum(valid_mask) * 100
        moderate = np.sum(agreement[valid_mask] == 2) / np.sum(valid_mask) * 100
        low = np.sum(agreement[valid_mask] == 1) / np.sum(valid_mask) * 100
        
        # Dataset comparisons
        kappa_te_jrc = calculate_kappa(datasets['TE'], datasets['JRC'], valid_mask)
        kappa_te_fao = calculate_kappa(datasets['TE'], datasets['FAO'], valid_mask)
        kappa_jrc_fao = calculate_kappa(datasets['JRC'], datasets['FAO'], valid_mask)
        
        results.append({
            'Country': code,
            'High_Agreement (%)': high,
            'Moderate_Agreement (%)': moderate,
            'Low_Agreement (%)': low,
            'Kappa_TE-JRC': kappa_te_jrc,
            'Kappa_TE-FAO': kappa_te_fao,
            'Kappa_JRC-FAO': kappa_jrc_fao
        })
    
    return pd.DataFrame(results)

def main():
    try:
        log_message("Starting statistical analysis...")
        
        # Load data
        datasets, agreement, countries = load_data()
        log_message("Data loaded successfully")
        
        # Create valid mask
        valid_mask = (agreement > 0)
        
        # Calculate global statistics
        log_message("Calculating global statistics...")
        global_stats = {
            'TE-JRC Kappa': calculate_kappa(datasets['TE'], datasets['JRC'], valid_mask),
            'TE-FAO Kappa': calculate_kappa(datasets['TE'], datasets['FAO'], valid_mask),
            'JRC-FAO Kappa': calculate_kappa(datasets['JRC'], datasets['FAO'], valid_mask),
            'TE-JRC Fuzzy Kappa': calculate_fuzzy_kappa(datasets['TE'], datasets['JRC'], valid_mask),
            'TE-FAO Fuzzy Kappa': calculate_fuzzy_kappa(datasets['TE'], datasets['FAO'], valid_mask),
            'JRC-FAO Fuzzy Kappa': calculate_fuzzy_kappa(datasets['JRC'], datasets['FAO'], valid_mask)
        }
        
        # Create confusion matrices
        cm_te_jrc = create_confusion_matrix(datasets['TE'], datasets['JRC'], valid_mask)
        cm_te_fao = create_confusion_matrix(datasets['TE'], datasets['FAO'], valid_mask)
        cm_jrc_fao = create_confusion_matrix(datasets['JRC'], datasets['FAO'], valid_mask)
        
        # Calculate country-level statistics
        log_message("Calculating country-level statistics...")
        country_stats = calculate_country_stats(datasets, agreement, countries)
        
        # Save results
        output_dir = '/home/erdoghi/LDN/Results'
        os.makedirs(output_dir, exist_ok=True)
        
        # Save global stats
        with open(os.path.join(output_dir, 'global_stats.txt'), 'w') as f:
            for k, v in global_stats.items():
                f.write(f"{k}: {v:.3f}\n")
            
            f.write("\nConfusion Matrices:\n")
            f.write("TE-JRC:\n" + str(cm_te_jrc) + "\n\n")
            f.write("TE-FAO:\n" + str(cm_te_fao) + "\n\n")
            f.write("JRC-FAO:\n" + str(cm_jrc_fao) + "\n")
        
        # Save country stats
        country_stats.to_csv(os.path.join(output_dir, 'country_stats.csv'), index=False)
        
        log_message("STEP 2 COMPLETE: Results saved to /home/erdoghi/LDN/Results", Qgis.Success)
        
    except Exception as e:
        log_message(f"ERROR: {str(e)}", Qgis.Critical)
        raise

if __name__ == "__main__":
    main()