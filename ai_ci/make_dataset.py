# -*- coding: utf-8 -*-
import logging
from dotenv import find_dotenv, load_dotenv
import psycopg2
from sqlalchemy import create_engine, exc
from sqlalchemy.ext.declarative import declarative_base
from subprocess import call
# Important to import the module
# This configures logging, file-paths, model config variables
import ai_ci
from ai_ci.fetch_data import get_database


logger = logging.getLogger(__name__)

Base = declarative_base()

def main():
    """ Runs data processing scripts to turn raw data from (../raw) into
        cleaned data ready to be analyzed (saved in ../processed).
    """

    config = ai_ci.config
    project_dir = ai_ci.project_dir

    load_dotenv(find_dotenv())

    # Try to create the database if it doesn't already exist.
    try:
        get_database(project_dir)
        engine = create_engine(os.getenv("test_postgresdb"))
        conn = engine.connect()
        conn.execute("commit")
        conn.execute("create database ai_ci")
        conn.close()
        call(f"{project_dir}/data/raw/ai_ci_make_database.sh")
    except exc.DBAPIError as e:
        if isinstance(e.orig, psycopg2.errors.DuplicateDatabase):
            logging.info(e)
        else:
            logging.error(e)
            raise

    db_config = os.getenv('postgresdb')
    engine = create_engine(db_config)
    Base.metadata.create_all(engine)
    
    
    

    return



if __name__ == "__main__":
    
    project_dir = ai_ci.project_dir
    
    load_dotenv(find_dotenv())
    
    try:
        msg = f"Creating database..."
        logger.info(msg)
        main()
    except (Exception, KeyboardInterrupt) as e:
        logger.exception("Creating database failed...", stack_info=True)
        raise e
