"""
Queries Microsoft Academic Knowledge API with Fields of Study (paper keywords) and stores the responses locally.
The pickle file is a list of JSONs where every JSON object is the API response corresponding to a paper. Every 
pickle contains a maximum of 1,000 objects (that's the maximum number of papers we can retrieve from MAG with a
query).

Example API response:
{'logprob': -24.006,
 'prob': 3.75255e-11,
 'Id': 2904236373,
 'Ti': 'conspiracy ideation and fake science news',
 'Pt': '0',
 'Y': 2018,
 'D': '2018-01-18',
 'CC': 0,
 'RId': [2067319876, 2130121899],
 'PB': 'OSF',
 'BT': 'a',
 'AA': [{'DAuN': 'Asheley R. Landrum',
   'AuId': 2226866834,
   'AfId': None,
   'S': 1},
  {'DAuN': 'Alex Olshansky', 'AuId': 2883323127, 'AfId': None, 'S': 2}],
 'F': [{'DFN': 'Science communication',
   'FN': 'science communication',
   'FId': 472806},
  {'DFN': 'Public relations', 'FN': 'public relations', 'FId': 39549134},
  {'DFN': 'Public awareness of science',
   'FN': 'public awareness of science',
   'FId': 176049440},
  {'DFN': 'Political science', 'FN': 'political science', 'FId': 17744445},
  {'DFN': 'Misinformation', 'FN': 'misinformation', 'FId': 2776990098},
  {'DFN': 'Ideation', 'FN': 'ideation', 'FId': 170477896},
  {'DFN': 'Fake news', 'FN': 'fake news', 'FId': 2779756789}]}
"""
import os
import logging
import pickle
from dotenv import load_dotenv, find_dotenv
import ci_mapping
from ci_mapping.packages.mag.query_mag_api import (
    query_mag_api,
    query_fields_of_study,
    build_composite_expr,
)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    load_dotenv(find_dotenv())

    config = ci_mapping.config["data"]["mag"]
    # API params
    key = os.getenv("mag_key")
    start_year = ci_mapping.config["data"]["mag"]["timeframe"][0]
    end_year = ci_mapping.config["data"]["mag"]["timeframe"][1]
    metadata = config["metadata"]
    all_fos = [config["ci_fos"], config["ml_fos"]]
    entity_name = config["entity_name"]
    query_count = config["query_count"]
    # Path to external data with file prefix
    store_path = f'{ci_mapping.project_dir}/{config["store_path"]}'
    # Count
    i = 0

    # ML and CI FoS
    for fos in all_fos:
        # Collect data from end_year to start_year
        for year in range(end_year, start_year - 1, -1):
            # Collect data in 6-month intervals: ((start_month, end_month), (start_day, end_day))
            for date in [(("01", "06"), ("01", "01")), (("06", "12"), ("01", "31"))]:

                # Build composite expression
                expression = build_composite_expr_date(fos, entity_name, year, date)
                logging.info(f"{expression}")

                has_content = True
                offset = 0

                while has_content:
                    logging.info(f"Query {i} - Offset {offset}...")

                    data = query_mag_api(
                        expression,
                        metadata,
                        key,
                        query_count=query_count,
                        offset=offset,
                    )
                    results = [ents for ents in data["entities"]]

                    with open("_".join([store_path, f"{i}.pickle"]), "wb") as h:
                        pickle.dump(results, h)
                        logging.info(
                            f"Number of stored results from query {i}: {len(results)}"
                        )

                    i += 1
                    offset += query_count

                    if len(results) < query_count:
                        has_content = False
