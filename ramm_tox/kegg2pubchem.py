"""Get PubChem CID from KEGG compound/drug accession."""

import sys
import csv
import bs4
import requests
import re

reader = csv.DictReader(open(sys.argv[1]))
writer = csv.DictWriter(sys.stdout, reader.fieldnames)

re_pubchem = re.compile(r'^PubChem:')
kegg_url = 'http://www.kegg.jp/dbget-bin/www_bget?{}'
pubchem_url = 'http://pubchem.ncbi.nlm.nih.gov/rest/pug/substance/sid/{}/cids/txt'

writer.writeheader()
for r in reader:
    if not len(r['PubChem']) and len(r['KEGG']):
        kegg_req = requests.get(kegg_url.format(r['KEGG']))
        assert kegg_req.ok
        soup = bs4.BeautifulSoup(kegg_req.content)
        divs = soup.find_all('div', text=re_pubchem)
        assert len(divs) <= 1
        if len(divs) == 1:
            sid = divs[0].nextSibling.find('a').text
            pubchem_req = requests.get(pubchem_url.format(sid))
            if pubchem_req.status_code != 404:
                assert pubchem_req.ok
                cids = pubchem_req.content.rstrip().split('\n')
                assert len(cids) <= 1
                if len(cids) == 1:
                    r['PubChem'] = cids[0]
    writer.writerow(r)
    sys.stdout.flush()
