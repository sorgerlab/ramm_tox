import pandas as pd
import numpy as np
from ramm_tox import util

def round_concentration(values):
    """Round concentration values to 4 decimal places in log space."""
    return 10 ** np.round(np.log10(values), 4)

util.init_paths()

viability_path = util.data_path.child('CellViability_Combined_mean&variance2.xlsx')
imaging_path = util.data_path.child('HCI_Rep1-4_zscores.csv')

viability_data = pd.read_excel(viability_path, 0)
vd_filter_no_media = ~viability_data.name.str.lower().str.startswith('medium')
viability_data = viability_data[vd_filter_no_media]
vd_filter_72h = viability_data['time [h]'] == 72
viability_data = viability_data[vd_filter_72h].drop('time [h]', axis=1)
viability_data.dose = round_concentration(viability_data.dose)

imaging_data = pd.read_csv(imaging_path, encoding='utf-8')
imaging_filter_no_media = ~imaging_data.pert_iname.str.lower().str.startswith('medium')
imaging_data = imaging_data[imaging_filter_no_media]
imaging_data.pert_dose = round_concentration(imaging_data.pert_dose)

viability_single = viability_data[viability_data.name == 'Omeprazole'] \
    [['dose', 'average']].pivot_table(rows='dose')
imaging_single = imaging_data[imaging_data.pert_iname == 'Omeprazole'] \
    .drop('pert_iname', axis=1).rename(columns=({'pert_dose': 'dose'})) \
    .pivot_table(rows='dose', cols='Timepoint [h]')
corr_single = imaging_single.corrwith(viability_single.average).order()
