import os
import logging
from dotenv import load_dotenv, find_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sklearn.feature_extraction.text import CountVectorizer
from skbio.diversity.alpha import shannon, simpson, simpson_e
import pandas as pd
import ci_mapping
from ci_mapping.utils.utils import identity_tokenizer
import numpy as np
from ci_mapping.data.mag_orm import (
    Paper,
    AuthorAffiliation,
    AffiliationLocation,
    PaperFieldsOfStudy,
    CoreControlGroup,
    ResearchDiversityCountry,
)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    load_dotenv(find_dotenv())

    citation_threshold = ci_mapping.config["citation_threshold"]

    db_config = os.getenv("postgresdb")
    engine = create_engine(db_config)
    Session = sessionmaker(engine)
    s = Session()

    # Delete rows in ResearchDiversityCountry
    s.query(ResearchDiversityCountry).delete()
    s.commit()

    # Read MAG data
    mag = pd.read_sql(s.query(Paper).statement, s.bind)

    #  Read AI, AICI, CI group assignment
    groups = pd.read_sql(s.query(CoreControlGroup).statement, s.bind)

    # Merge group assignment with papers
    mag = mag.merge(groups, left_on="id", right_on="id")
    # Remove papers with low citations for robustness
    mag = mag[mag.citations > citation_threshold]
    logging.info(f"MAG data shape: {mag.shape}")

    # Merge tables
    df = (
        aff_location[aff_location.country != ""][["affiliation_id", "country"]]
        .merge(author_aff, left_on="affiliation_id", right_on="affiliation_id")
        .merge(
            mag[["id", "year", "citations", "type", "avg_citations"]],
            left_on="paper_id",
            right_on="id",
        )
        .merge(paper_fos, left_on="paper_id", right_on="paper_id",)[
            [
                "affiliation_id",
                "field_of_study_id",
                "country",
                "paper_id",
                "citations",
                "year",
                "type",
                "avg_citations",
            ]
        ]
    )

    # Group FoS by year, type and country
    country_level = (
        df.drop_duplicates(
            subset=["field_of_study_id", "country", "paper_id", "year", "type"]
        )
        .groupby(["type", "year", "country"])["field_of_study_id"]
        .apply(list)
    )

    # Sum paper count by year, type and country
    country_level_paper_count = (
        df.drop_duplicates(subset=["country", "paper_id", "year", "type"])
        .groupby(["type", "year", "country"])["paper_id"]
        .count()
    )

    # Measure research diversity for each year, type and country
    frames = []
    i = pd.IndexSlice
    country_level = pd.DataFrame(country_level)
    for type in set([idx[0] for idx in country_level.index]):
        for year in sorted([idx[1] for idx in country_level.index]):
            frame = country_level.loc[i[type, year, :], :]

            if frame.shape[0] > 0:

                vectorizer = CountVectorizer(
                    tokenizer=identity_tokenizer, lowercase=False
                )
                X = vectorizer.fit_transform(list(frame.field_of_study_id))
                X = X.toarray()

                shannon_div = [shannon(arr) for arr in X]
                simpson_e_div = [simpson_e(arr) for arr in X]
                simpson_div = [simpson(arr) for arr in X]

                for j, country in enumerate([idx[2] for idx in frame.index]):
                    s.add(
                        ResearchDiversityCountry(
                            **{
                                "type": type,
                                "year": year,
                                "country": country,
                                "shannon_diversity": shannon_div[j],
                                "simpson_diversity": simpson_div[j],
                                "simpson_e_diversity": simpson_e_div[j],
                                "paper_count": int(
                                    country_level_paper_count.loc[
                                        i[type, year, country]
                                    ]
                                ),
                            }
                        )
                    )
                s.commit()
