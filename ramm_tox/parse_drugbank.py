import os
import sys
import lxml.etree
import sqlalchemy as sa
import xlrd

ns = 'http://www.drugbank.ca'

def xpath(obj, path, single=True):
    result = map(unicode,
                 obj.xpath(path, namespaces={'d': ns}, smart_strings=False))
    if single:
        if len(result) == 0:
            result = None
        elif len(result) == 1:
            result = result[0]
        else:
            raise ValueError("XPath expression matches more than one value")
    return result

def qname(tag):
    return '{{{ns}}}{tag}'.format(ns=ns, tag=tag)

db_file = 'drugbank.sqlite'
#db_file = ':memory:'
engine = sa.create_engine('sqlite:///' + db_file)
conn = engine.connect()
metadata = sa.MetaData(bind=conn)
drugbank_drug = sa.Table(
    'drugbank_drug', metadata,
    sa.Column('drug_id', sa.String(), primary_key=True),
    sa.Column('name', sa.String()),
    sa.Column('synonyms', sa.PickleType()),  # list of strings
    sa.Column('chebi_id', sa.String()),
    sa.Column('kegg_id', sa.String()),
    sa.Column('pubchem_cid', sa.String()),
    sa.Column('molecular_formula', sa.String()),
    sa.Column('partners', sa.PickleType()),  # list of strings
    )
drugbank_name = sa.Table(
    'drugbank_name', metadata,
    sa.Column('drug_id', sa.String()),
    sa.Column('name', sa.String(), index=True),
    )
metadata.drop_all()
metadata.create_all()

datafile_name = 'drugbank.xml'
datafile = open(datafile_name)

# Parse drugbank xml into sqlite, only if the table is empty.
if not conn.execute(drugbank_drug.select()).first():
    with conn.begin() as trans:
        for event, element in lxml.etree.iterparse(datafile, tag=qname('drug')):
            # We need to skip 'drug' elements in various sub-elements.
            # It's unfortunate they re-used this tag name.
            if element.getparent().tag != qname('drugbank'):
                continue
            drug_id = xpath(element, 'd:drugbank-id[@primary="true"]/text()')
            name = xpath(element, 'd:name/text()')
            synonyms = xpath(
                element, 'd:synonyms/d:synonym/text()', single=False)
            synonyms += xpath(
                element, 'd:brands/d:brand/text()', single=False)
            molecular_formula = xpath(
                element, './/d:property[d:kind="Molecular Formula"]/'
                'd:value/text()')
            chebi_id = xpath(
                element, './/d:external-identifier[d:resource="ChEBI"]/'
                'd:identifier/text()')
            kegg_id = xpath(
                element, './/d:external-identifier[d:resource="KEGG Drug"]/'
                'd:identifier/text()')
            pubchem_cid = xpath(
                element, './/d:external-identifier[d:resource="PubChem Compound"]/'
                'd:identifier/text()')
            partner_ids = xpath(
                element, 'd:targets/d:target/@partner', single=False)
            conn.execute(
                drugbank_drug.insert().
                values(drug_id=drug_id, name=name, synonyms=synonyms,
                       chebi_id=chebi_id, kegg_id=kegg_id,
                       pubchem_cid=pubchem_cid,
                       molecular_formula=molecular_formula,
                       partners=partner_ids))
            conn.execute(
                drugbank_name.insert().
                values(drug_id=drug_id, name=name.lower()))
            for s in synonyms:
                conn.execute(
                    drugbank_name.insert().
                    values(drug_id=drug_id, name=s.lower()))
            element.clear()

    # Turns out it's much faster to do a second iterparse loop with a different
    # tag argument than to do just one iterparse loop with a conditional on the
    # tag name. The lxml internals are much more efficient at filtering tags
    # than we are, and the disk I/O and buffer cache impact are negligible. It
    # would be nice if the tag argument could accept a list of tag names...
    datafile.seek(0)
    partner_to_uniprot = {}
    for event, element in lxml.etree.iterparse(datafile, tag=qname('partner')):
        partner_id = element.get('id')
        uniprot_id = xpath(element, './/d:external-identifier'
                           '[d:resource="UniProtKB"]/d:identifier/text()')
        partner_to_uniprot[partner_id] = uniprot_id
        element.clear()

    with conn.begin() as trans:
        for rec in conn.execute(drugbank_drug.select()):
            new_values = dict(rec)
            new_values['partners'] = map(partner_to_uniprot.__getitem__, rec.partners)
            new_values['partners'] = filter(None, new_values['partners'])
            conn.execute(drugbank_drug.update().
                         where(drugbank_drug.c.drug_id == rec.drug_id).
                         values(**new_values))
