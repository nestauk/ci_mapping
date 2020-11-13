"""This pipeline is heavily based on Orion https://github.com/orion-search/orion.
For bugs/issues, contact the Nesta team or myself at k.stathou@gmail.com.
"""

from metaflow import FlowSpec, step, Parameter
import pandas as pd
from sqlalchemy.sql import exists
from sqlalchemy import create_engine, and_
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv, find_dotenv
import glob
import toolz
import pickle
import os
import ci_mapping
from ci_mapping import logger
from ci_mapping.data.create_db_and_tables import create_db_and_tables
from ci_mapping.data.query_mag import (
    query_mag_api,
    query_fields_of_study,
    build_composite_expr,
)
from ci_mapping.data.geocode import place_by_id, place_by_name, parse_response
from ci_mapping.utils.utils import unique_dicts, unique_dicts_by_value, flatten_lists
from ci_mapping.utils.utils import date_range, str2datetime, allocate_in_group
from ci_mapping.data.parse_mag_data import (
    parse_affiliations,
    parse_authors,
    parse_fos,
    parse_journal,
    parse_papers,
    parse_conference,
)
from ci_mapping.data.mag_orm import (
    Paper,
    PaperAuthor,
    Journal,
    Author,
    Affiliation,
    FieldOfStudy,
    PaperFieldsOfStudy,
    Conference,
    AuthorAffiliation,
    FosMetadata,
    CoreControlGroup,
    AffiliationLocation,
    AffiliationType,
    OpenAccess,
)

load_dotenv(find_dotenv())
config = ci_mapping.config["data"]
mag_config = ci_mapping.config["data"]["mag"]


class CollectiveIntelligenceFlow(FlowSpec):
    """
    docstring
    """

    db_name = Parameter(
        "db_name", help="DB configuration filename", default=config["db_name"]
    )
    mag_start_date = Parameter(
        "mag_start_date",
        help="Start date of the data collection",
        default=mag_config["mag_start_date"],
    )
    mag_end_date = Parameter(
        "mag_end_date",
        help="End date of the data collection",
        default=mag_config["mag_end_date"],
    )
    intervals_in_a_year = Parameter(
        "intervals_in_a_year",
        help="Collection timeframes. Used to bypass MAG's throttling.",
        default=mag_config["intervals_in_a_year"],
    )
    entity_name = Parameter(
        "entity_name", help="MAG API field to query.", default=mag_config["entity_name"]
    )
    query_values = Parameter(
        "query_values", help="Query sent to MAG", default=mag_config["query_values"]
    )
    metadata = Parameter(
        "metadata", help="Fields to fetch from MAG.", default=mag_config["metadata"]
    )
    subscription_key = Parameter(
        "subscription_key",
        help="MAG API key stored in the .env file.",
        default=os.getenv("mag_key"),
    )
    google_api_key = Parameter(
        "google_api_key", help="Google API Key", default=os.getenv("google_key")
    )
    with_doi = Parameter(
        "with_doi", help="Fetch ONLY papers with a DOI.", default=mag_config["with_doi"]
    )
    store_path = Parameter(
        "store_path",
        help="Path to store MAG response files.",
        default=mag_config["store_path"],
    )
    external_data = Parameter(
        "external_data",
        help="Path to external data.",
        default=f'{ci_mapping.project_dir}/{config["external_path"]}',
    )
    fos_subset = Parameter(
        "fos_subset",
        help="Subset of Fields of Study related to AI.",
        default=ci_mapping.config["fos_subset"],
    )
    oa_journals = Parameter(
        "open_access_journals",
        help="List of open access journals, mainly *Xivs",
        default=ci_mapping.config["open_access"],
    )
    non_industry = Parameter(
        "non_industry_affiliations",
        help="List of non-industry affiliations.",
        default=ci_mapping.config["affiliations"]["non_industry"],
    )

    def _create_session(self):
        """Creates a PostgreSQL session."""
        # Connect to postgresql
        db_config = os.getenv(self.db_name)
        engine = create_engine(db_config)
        Session = sessionmaker(bind=engine)
        return Session()

    def _is_open_access(self, name):
        if name in set(self.oa_journals):
            return 1
        else:
            return 0

    def _find_non_industry_affiliations(self, name):
        if any(val in name for val in self.non_industry):
            return 1
        else:
            return 0

    @step
    def start(self):
        """Creates the PostgreSQL database and tables if they do not exist."""
        create_db_and_tables(self.db_name)

        # Proceed to next task
        # self.next(self.geocode_affiliation)
        self.next(self.collect_mag)

    @step
    def collect_mag(self):
        """Collect papers from MAG and store the response locally as a pickle."""
        # Convert strings to datetime objects
        mag_start_date = str2datetime(self.mag_start_date)
        mag_end_date = str2datetime(self.mag_end_date)

        # Number of time intervals for the data collection
        total_intervals = (
            abs(mag_start_date.year - mag_end_date.year) + 1
        ) * self.intervals_in_a_year

        i = 0
        query_count = 1000
        for date in toolz.sliding_window(
            2, list(date_range(mag_start_date, mag_end_date, total_intervals))
        ):
            logger.info(f"Date interval: {date}")
            expression = build_composite_expr(self.query_values, self.entity_name, date)
            logger.info(f"{expression}")

            has_content = True
            # i = 1
            offset = 0
            # Request the API as long as we receive non-empty responses
            while has_content:
                logger.info(f"Query {i} - Offset {offset}...")

                data = query_mag_api(
                    expression,
                    self.metadata,
                    self.subscription_key,
                    query_count=query_count,
                    offset=offset,
                )

                if self.with_doi:
                    # Keep only papers with a DOI
                    results = [
                        ents for ents in data["entities"] if "DOI" in ents.keys()
                    ]
                else:
                    results = [ents for ents in data["entities"]]

                # Store results
                with open(
                    f"{ci_mapping.project_dir}/{self.store_path}_{i}.pickle", "wb"
                ) as h:
                    pickle.dump(results, h)
                logger.info(f"Number of stored results from query {i}: {len(results)}")

                i += 1
                offset += query_count

                if len(results) == 0:
                    has_content = False

        self.next(self.parse_mag)

    @step
    def parse_mag(self):
        """Parse MAG responses to PostgreSQL."""
        # Connect to postgresql
        s = self._create_session()

        # Read MAG responses
        data = []
        for filename in glob.iglob("".join([self.external_data, "*.pickle"])):
            with open(filename, "rb") as h:
                data.extend(pickle.load(h))

        # Collect IDs from tables to ensure we're not inserting duplicates
        paper_ids = {id_[0] for id_ in s.query(Paper.id)}
        author_ids = {id_[0] for id_ in s.query(Author.id)}
        fos_ids = {id_[0] for id_ in s.query(FieldOfStudy.id)}
        aff_ids = {id_[0] for id_ in s.query(Affiliation.id)}

        # Remove duplicates and keep only papers that are not already in the mag_papers table.
        data = [
            d for d in unique_dicts_by_value(data, "Id") if d["Id"] not in paper_ids
        ]
        logger.info(f"Number of unique  papers not existing in DB: {len(data)}")

        papers = [parse_papers(response) for response in data]
        logger.info(f"Completed parsing papers: {len(papers)}")

        journals = [
            parse_journal(response, response["Id"])
            for response in data
            if "J" in response.keys()
        ]
        logger.info(f"Completed parsing journals: {len(journals)}")

        conferences = [
            parse_conference(response, response["Id"])
            for response in data
            if "C" in response.keys()
        ]
        logger.info(f"Completed parsing conferences: {len(conferences)}")

        # Parse author information
        items = [parse_authors(response, response["Id"]) for response in data]
        authors = [
            d
            for d in unique_dicts_by_value(
                flatten_lists([item[0] for item in items]), "id"
            )
            if d["id"] not in author_ids
        ]

        paper_with_authors = unique_dicts(flatten_lists([item[1] for item in items]))
        logger.info(f"Completed parsing authors: {len(authors)}")
        logger.info(f"Completed parsing papers_with_authors: {len(paper_with_authors)}")

        # Parse Fields of Study
        items = [
            parse_fos(response, response["Id"])
            for response in data
            if "F" in response.keys()
        ]
        paper_with_fos = unique_dicts(flatten_lists([item[0] for item in items]))
        fields_of_study = [
            d
            for d in unique_dicts(flatten_lists([item[1] for item in items]))
            if d["id"] not in fos_ids
        ]
        logger.info(f"Completed parsing fields_of_study: {len(fields_of_study)}")
        logger.info(f"Completed parsing paper_with_fos: {len(paper_with_fos)}")

        # Parse affiliations
        items = [parse_affiliations(response, response["Id"]) for response in data]
        affiliations = [
            d
            for d in unique_dicts(flatten_lists([item[0] for item in items]))
            if d["id"] not in aff_ids
        ]
        paper_author_aff = unique_dicts(flatten_lists([item[1] for item in items]))
        logger.info(f"Completed parsing affiliations: {len(affiliations)}")
        logger.info(f"Completed parsing author_with_aff: {len(paper_author_aff)}")

        logger.info("Parsing completed!")

        # Insert dicts into postgresql
        s.bulk_insert_mappings(Paper, papers)
        s.bulk_insert_mappings(Journal, journals)
        s.bulk_insert_mappings(Conference, conferences)
        s.bulk_insert_mappings(Author, authors)
        s.bulk_insert_mappings(PaperAuthor, paper_with_authors)
        s.bulk_insert_mappings(FieldOfStudy, fields_of_study)
        s.bulk_insert_mappings(PaperFieldsOfStudy, paper_with_fos)
        s.bulk_insert_mappings(Affiliation, affiliations)
        s.bulk_insert_mappings(AuthorAffiliation, paper_author_aff)
        s.commit()
        logger.info("Committed to DB!")

        self.next(self.collect_fields_of_study_level)

    @step
    def collect_fields_of_study_level(self):
        """Collect Fields' of Study metadata."""
        # Connect to postgresql
        s = self._create_session()

        # Keep the FoS IDs that haven't been collected yet
        fields_of_study_ids = [
            id_[0]
            for id_ in s.query(FieldOfStudy.id).filter(
                ~exists().where(FieldOfStudy.id == FosMetadata.id)
            )
        ]
        logger.info(f"Fields of study left: {len(fields_of_study_ids)}")

        # Collect FoS metadata
        fos = query_fields_of_study(self.subscription_key, ids=fields_of_study_ids)

        # Parse api response
        for response in fos:
            s.add(FosMetadata(id=response["id"], level=response["level"]))
            s.commit()

        self.next(self.fos_groups)

    @step
    def fos_groups(self):
        """Tag Fields of Study as Core Collective Intelligence and AI+CI.
        This method could be extended to divide a dataset to core and control
        group.
        """
        # Connect to postgresql
        s = self._create_session()
        # Delete rows in CoreControlGroup
        s.query(CoreControlGroup).delete()
        s.commit()

        # Fetch postgres tables
        fos = pd.read_sql(s.query(FieldOfStudy).statement, s.bind)
        pfos = pd.read_sql(s.query(PaperFieldsOfStudy).statement, s.bind)

        # Merge and groupby so that FoS are in a list
        pfos = pfos.merge(fos, left_on="field_of_study_id", right_on="id")
        pfos = pd.DataFrame(pfos.groupby("paper_id")["norm_name"].apply(list))

        # Allocate papers in CI, AI+CI groups based on Fields of Study.
        pfos["type"] = pfos.norm_name.apply(allocate_in_group, args=([self.fos_subset]))
        logger.info(f"CI papers: {pfos[pfos['type']=='CI'].shape[0]}")
        logger.info(f"AI+CI papers: {pfos[pfos['type']=='AI_CI'].shape[0]}")

        for idx, row in pfos.iterrows():
            s.add(CoreControlGroup(id=idx, type=row["type"]))
            s.commit()

        self.next(self.open_access_journals)
        self.next(self.geocode_affiliation)

    @step
    def geocode_affiliation(self):
        """Geocode author affiliation using Google Places API."""
        # Connect to postgresql
        s = self._create_session()

        # Fetch affiliations that have not been geocoded yet.
        queries = s.query(Affiliation.id, Affiliation.affiliation).filter(
            ~exists().where(Affiliation.id == AffiliationLocation.affiliation_id)
        )
        logger.info(f"Number of places need geocoding: {queries.count()}")

        for id, name in queries:
            r = place_by_name(name, self.google_api_key)
            if r is not None:
                response = place_by_id(r, self.google_api_key)
                place_details = parse_response(response)
                place_details.update({"affiliation_id": id})
                s.add(AffiliationLocation(**place_details))
                s.commit()
            else:
                continue
        self.next(self.open_access_journals)
        # self.next(self.end)

    @step
    def open_access_journals(self):
        """Tag journals as open access based on a seed list."""
        # Connect to postgresql
        s = self._create_session()
        # Delete rows in OpenAccess
        s.query(OpenAccess).delete()
        s.commit()

        # Get journal names and IDs
        journal_access = [
            {"id": id, "open_access": self._is_open_access(journal_name)}
            for (id, journal_name) in s.query(Journal.id, Journal.journal_name)
            .distinct()
            .all()
        ]

        logger.info(f"{len(journal_access)}")

        # Store journal types
        s.bulk_insert_mappings(OpenAccess, journal_access)
        s.commit()

        self.next(self.affiliation_type)

    @step
    def affiliation_type(self):
        """Find the type (industry, non-industry) of an
        affiliation based on a seed list.
        """
        # Connect to postgresql
        s = self._create_session()
        # Delete rows in AffiliationType
        s.query(AffiliationType).delete()
        s.commit()

        # Get affiliation names and IDs
        aff_types = [
            {
                "id": aff.id,
                "non_industry": self._find_non_industry_affiliations(aff.affiliation),
            }
            for aff in s.query(Affiliation)
            .filter(and_(~exists().where(Affiliation.id == AffiliationType.id)))
            .all()
        ]
        logger.info(f"Mapped {len(aff_types)} affiliations.")

        # Store affiliation types
        s.bulk_insert_mappings(AffiliationType, aff_types)
        s.commit()

        self.next(self.end)

    @step
    def end(self):
        """Gracefully exit metaflow."""
        logger.info("Tasks completed.")


if __name__ == "__main__":
    CollectiveIntelligenceFlow()
