import operator
import collections
import pandas as pd
import numpy as np
from ramm_tox import util, stats

def round_concentration(values):
    """Round concentration values to 4 decimal places in log space."""
    return 10 ** np.round(np.log10(values), 4)

def strings_to_wordsets(strings, stop_words=None):
    """Build a dict of wordsets from a list of strings, with optional filter.

    For each distinct word found in the list of strings, the wordset dict will
    map that word to a set of the strings that contain it. A list of words to
    ignore may be passed in stop_words.

    """
    string_words = [set(w.split(' ')) for w in (s.lower() for s in strings)]
    words = reduce(operator.or_, string_words)
    if stop_words:
        words -= set(stop_words)
    wordsets = collections.OrderedDict(
        (w, set(strings[i] for i, s in enumerate(string_words) if w in s))
        for w in sorted(words))
    return wordsets

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
    [['dose', 'average']].pivot_table(index='dose').average
imaging_single = imaging_data[imaging_data.pert_iname == 'Omeprazole'] \
    .drop('pert_iname', axis=1).rename(columns=({'pert_dose': 'dose'})) \
    .pivot_table(index='dose', columns='Timepoint [h]')
corr, p = stats.pearsonr(imaging_single.values.T, viability_single.values)

fake_genes = [x[0] + ' t=' + unicode(x[1]) + 'h' for x in imaging_single.columns]
fake_genes = [s.replace('(2)-', '(2) -') for s in fake_genes]
wordsets = strings_to_wordsets(fake_genes, stop_words=['', '-'])
with open('genesets.gmt', 'w') as f:
    gmt_rows = ('\t'.join([w, ''] + list(ss)) for w, ss in wordsets.items())
    f.write('\n'.join(gmt_rows).encode('utf-8'))
rnk_data = pd.Series(corr, index=fake_genes)
rnk_data.to_csv('data.rnk', sep='\t', encoding='utf8')
