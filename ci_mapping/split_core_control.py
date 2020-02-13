"""
Categorises a paper to one of the three groups: AI, AI/CI, CI. It fetches paper IDs and their FoS and allocates papers into groups and stores their ID, DOI and group type in a PostgreSQL DB. 
"""
import os
import logging
import pickle
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.sql import exists
from dotenv import load_dotenv, find_dotenv
import pandas as pd
import ci_mapping
from ci_mapping.utils.utils import allocate_in_group
from ci_mapping.data.mag_orm import PaperFieldsOfStudy, FieldOfStudy, CoreControlGroup

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    load_dotenv(find_dotenv())

    # Connect to DB
    db_config = os.getenv("postgresdb")
    engine = create_engine(db_config)
    Session = sessionmaker(engine)
    s = Session()

    # Fetch queried FoS
    config = ci_mapping.config["data"]["mag"]
    ci_fos = config["ci_fos"]
    ai_fos = config["ai_fos"]

    # Fetch postgres tables
    fos = pd.read_sql(s.query(FieldOfStudy).statement, s.bind)
    pfos = pd.read_sql(s.query(PaperFieldsOfStudy).statement, s.bind)

    # Merge and groupby so that FoS are in a list
    pfos = pfos.merge(fos, left_on='field_of_study_id', right_on='id')
    pfos = pd.DataFrame(pfos.groupby('paper_id')['norm_name'].apply(list))

    # Match ci, ai, ai_ci FoS in the list
    pfos['type'] = pfos.norm_name.apply(allocate_in_group, args=(ci_fos, ai_fos))

    logging.info(f"AI papers: {pfos[pfos['type']=='ai'].shape[0]}")
    logging.info(f"CI papers: {pfos[pfos['type']=='ci'].shape[0]}")
    logging.info(f"AI/CI papers: {pfos[pfos['type']=='ai_ci'].shape[0]}")
    
    for idx, row in pfos.iterrows():
        s.add(CoreControlGroup(id=idx, type=row['type']))
        s.commit()
