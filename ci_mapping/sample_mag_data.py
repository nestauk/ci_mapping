"""
Get a data sample from MAG to test parse_mag.py
"""
import os
import logging
import pickle
from dotenv import load_dotenv, find_dotenv
import ci_mapping
from ci_mapping.data.query_mag_composite import build_composite_expr, query_mag_api

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    load_dotenv(find_dotenv())

    config = ci_mapping.config["data"]["mag"]
    # API params
    key = os.getenv("mag_key")
    metadata = config["metadata"]
    fos = config["fos"]
    entity_name = config["entity_name"]
    year = config["year"]
    query_count = 5  # lower this from 1000 to test with smaller data size
    offset = 0
    # Path to external data with file prefix
    store_path = f'{ci_mapping.project_dir}/{config["store_path"]}'

    # Build an expandable query for MAG API
    expression = build_composite_expr(fos, entity_name, year)
    logging.info(f"{expression}")

    for i in range(2):
        data = query_mag_api(
            expression, metadata, key, query_count=query_count, offset=offset
        )

        results = [ents for ents in data["entities"]]

        with open("_".join([store_path, f"{i}.pickle"]), "wb") as h:
            pickle.dump(results, h)

        offset += query_count
