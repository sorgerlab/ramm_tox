import pandas as pd
from ramm_tox import util

util.init_paths()

viability_path = util.data_path.child('CellViability_Combined_mean&variance2.xlsx')
imaging_path = util.data_path.child('HCI_Rep1-4_zscores.csv')

viability_data = pd.read_excel(viability_path, 0)
vd_filter_no_media = ~viability_data.name.str.lower().str.startswith('medium')
viability_data = viability_data[vd_filter_no_media]
vd_filter_72h = viability_data['time [h]'] == 72
viability_data = viability_data[vd_filter_72h]

imaging_data = pd.read_csv(imaging_path)
imaging_filter_no_media = ~imaging_data.pert_iname.str.lower().str.startswith('medium')
imaging_data = imaging_data[imaging_filter_no_media]
