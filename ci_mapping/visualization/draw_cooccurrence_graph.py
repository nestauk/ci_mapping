"""
Filter FoS based on frequency and level. Then draw a cooccurrence graph. Note that this is dones only for the CI, AI+CI subset of the data.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pandas as pd
import numpy as np
from ci_mapping.data.mag_orm import (
    FieldOfStudy,
    PaperFieldsOfStudy,
    FosMetadata,
    CoreControlGroup,
)
from ci_mapping.utils.utils import cooccurrence_graph, flatten_lists
import networkx as nx
import ci_mapping
import os
import logging
from dotenv import load_dotenv, find_dotenv

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    load_dotenv(find_dotenv())

    # Path to store the graphml object
    store_path = f"{ci_mapping.project_dir}/data/interim/"
    graphml_obj = "ci_network.graphml"

    # Connect to db
    db_config = os.getenv("postgresdb")
    engine = create_engine(db_config)
    Session = sessionmaker(engine)
    s = Session()

    # Fetch tables
    group_type = pd.read_sql(s.query(CoreControlGroup).statement, s.bind)
    fos = pd.read_sql(s.query(FieldOfStudy).statement, s.bind)
    pfos = pd.read_sql(s.query(PaperFieldsOfStudy).statement, s.bind)
    metadata = pd.read_sql(s.query(FosMetadata).statement, s.bind)

    # Keep only CI, AI/CI paper IDs
    ci_paper_ids = set(
        group_type[(group_type.type == "ai_ci") | (group_type.type == "ci")]["id"]
    )

    # Merge FoS with FoS level
    fos = fos.merge(metadata, left_on="id", right_on="id")
    # Merge FoS with paper IDs
    pfos = pfos[pfos.paper_id.isin(ci_paper_ids)].merge(
        fos, left_on="field_of_study_id", right_on="id"
    )
    pfos = pfos.drop("id", axis=1)

    # FoS Frequency
    fos_frequency = pd.DataFrame(
        pfos.groupby(["field_of_study_id"])["paper_id"].count()
    ).reset_index()

    for i in sorted(pfos.level.unique()):
        logging.info(
            f"Level: {i} | FoS count: {pfos[pfos.level==i]['field_of_study_id'].unique().shape[0]}"
        )

    # From each level, keep only FoS with frequency > thresh
    d = {}
    for lvl, thresh in zip(sorted(pfos.level.unique())[1:], [100, 100, 100, 100, 100]):
        d[lvl] = set(
            [
                fos[fos.id == row["field_of_study_id"]]["name"].values[0]
                for _, row in pfos[pfos.level == lvl].iterrows()
                if fos_frequency[
                    fos_frequency.field_of_study_id == row["field_of_study_id"]
                ]["paper_id"].values
                > thresh
            ]
        )

    # Keep only FoS from level 1,2,3
    top_fos = set(flatten_lists([v for k, v in d.items() if k > 0 and k < 4]))
    logging.info(f"FoS number: {len(top_fos)}")

    # Create a cooccurrence network of fields of study
    graph = cooccurrence_graph(pfos.groupby("paper_id")["name"].apply(list))

    G = nx.Graph()
    for k, v in graph.items():
        # Keep only edges where the pair has cooccurred more than 15 times
        if k[0] in top_fos and k[1] in top_fos and v > 15:
            G.add_edge(k[0], k[1], weight=int(v))

    print(f"Nodes: {len(G)}")
    print(f"Edges: {len(G.edges)}")

    nx.write_graphml(G, path="".join([store_path, graphml_obj]))
