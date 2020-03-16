import pandas as pd
import numpy as np
from sqlalchemy import create_engine
import sqlalchemy as db
from sqlalchemy.orm import sessionmaker
import ast
from ai_ci.mag_orm import Paper, CoreControlGroup
from progress.bar import ChargingBar

# Read the configuration file and create a session.
db_config = 'postgres+psycopg2://postgres@localhost/ai_ci'
engine = create_engine(db_config)
metadata = db.MetaData()
Session = sessionmaker(engine)
s = Session()

mag = pd.read_sql(s.query(Paper).statement, s.bind)

control_group = pd.read_sql(s.query(CoreControlGroup).statement, s.bind)

mag = mag.merge(control_group[['id', 'type']], left_on='id', right_on='id')

# Drop 2020 papers
mag = mag[mag.year!='2020']

# Some columns have null values registered as 'NaN'
mag['bibtex_doc_type'] = mag.bibtex_doc_type.replace('NaN', np.nan)
mag['publisher'] = mag.publisher.replace('NaN', np.nan)
mag['references'] = mag.references.replace('NaN', np.nan)
mag['inverted_abstract'] = mag.inverted_abstract.replace('NaN', np.nan)
mag['doi'] = mag.doi.replace('NaN', np.nan)

# String to list
mag['references'] = mag.references.apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else np.nan)

# Change the publication and the bibtex document types
publication_type_ = {'0':np.nan, 
                     '1':'Journal article', 
                     '2':'Patent', 
                     '3':'Conference paper',
                     '4':'Book chapter',
                     '5':'Book',
                     '6':'Book reference entry', 
                     '7':'Dataset', 
                     '8':'Repository'}

bibtext_doc_type_ = {'a':'Journal article', 'b':'Book', 'c':'Book chapter', 'p':'Conference paper'}

mag['publication_type'] = mag.publication_type.apply(lambda x: publication_type_[x])
mag['bibtex_doc_type'] = mag.bibtex_doc_type.apply(lambda x: bibtext_doc_type_[x] if isinstance(x, str) else np.nan)

def uninvert_abstract(inverted_abstract):
    index_length = int(inverted_abstract.split('{"IndexLength": ')[1].split(', "InvertedIndex"')[0])

    dict_temp = {}
    for i in range(1,len(inverted_abstract.split('"InvertedIndex":')[1].split('{')[1].split('}}')[0].split('": '))):
        if i == 1:
            key = inverted_abstract.split('"InvertedIndex":')[1].split('{')[1].split('}}')[0].split('": ')[i-1].split('"')[1]
        else:
            key = inverted_abstract.split('"InvertedIndex":')[1].split('{')[1].split('}}')[0].split('": ')[i-1].split(', "')[-1]
        value = inverted_abstract.split('"InvertedIndex":')[1].split('{')[1].split('}}')[0].split('": ')[i].split(', "')[0].split('[')[1].split(']')[0]
        dict_temp[key] = value

    for key, value in dict_temp.items():
        if ',' in value:
            dict_temp[key] = value.split(', ')

    abstract= []
    for i in range(index_length):
        for key, value in dict_temp.items():
            if type(value) == str:
                if i == int(value):
                    abstract.append(key)
            else:
                for v in value:
                    if i == int(v):
                        abstract.append(key)
    abstract = ' '.join(abstract)

    return abstract

mag['abstract'] = np.zeros(len(mag))

bar = ChargingBar(f'Progress for reverting abstracts', max=len(mag))
for i in range(len(mag)):
    if type(mag.inverted_abstract[i]) == str:
        abstract = uninvert_abstract(mag.inverted_abstract[i])
        mag['abstract'][i] = abstract
    bar.next()
bar.finish()

mag.to_csv('mag.csv')