import ast
import numpy as np
import pandas as pd
from ci_mapping.data.mag_orm import (
    Paper,
    CoreControlGroup,
    AffiliationType,
    AuthorAffiliation,
)


def clean_data(s):
    """Cleans the main `mag_papers` table.

    Args:
        s (`sqlalchemy.orm.session.Session`): PostgreSQL connection.

    Returns:
        mag (pd.DataFrame)

    """
    # Read tables
    mag = pd.read_sql(s.query(Paper).statement, s.bind)
    flag = pd.read_sql(s.query(CoreControlGroup).statement, s.bind)

    # Join papers with flag
    mag = mag.merge(flag, left_on="id", right_on="id")

    # Some columns have null values registered as 'NaN'
    mag["bibtex_doc_type"] = mag.bibtex_doc_type.replace("NaN", np.nan)
    mag["publisher"] = mag.publisher.replace("NaN", np.nan)
    mag["references"] = mag.references.replace("NaN", np.nan)
    mag["abstract"] = mag.abstract.replace("NaN", np.nan)
    mag["doi"] = mag.doi.replace("NaN", np.nan)

    # String to list
    mag["references"] = mag.references.apply(
        lambda x: ast.literal_eval(x) if isinstance(x, str) else np.nan
    )

    # Change the publication and the bibtex document types
    publication_type_ = {
        "0": np.nan,
        "1": "Journal article",
        "2": "Patent",
        "3": "Conference paper",
        "4": "Book chapter",
        "5": "Book",
        "6": "Book reference entry",
        "7": "Dataset",
        "8": "Repository",
    }

    bibtext_doc_type_ = {
        "a": "Journal article",
        "b": "Book",
        "c": "Book chapter",
        "p": "Conference paper",
    }

    mag["publication_type"] = mag.publication_type.apply(lambda x: publication_type_[x])
    mag["bibtex_doc_type"] = mag.bibtex_doc_type.apply(
        lambda x: bibtext_doc_type_[x] if isinstance(x, str) else np.nan
    )
    mag["month_year"] = pd.to_datetime(mag["date"]).dt.to_period("M")
    return mag


def clean_author_affiliations(s, mag_papers):
    """Cleans the main `mag_papers` table.

    Args:
        s (`sqlalchemy.orm.session.Session`): PostgreSQL connection.
        mag_paper (`pd.DataFrame`): MAG paper data.

    Returns:
        aff_papers (`pd.DataFrame`): Author-level paper affiliations
            (unique affiliation_id/paper_id pairs).
        paper_author_aff (`pd.DataFrame`): Author-level paper affiliations.

    """
    aff_type = pd.read_sql(s.query(AffiliationType).statement, s.bind)
    paper_author_aff = pd.read_sql(s.query(AuthorAffiliation).statement, s.bind)
    paper_author_aff = paper_author_aff.drop(["id"], axis=1).merge(
        aff_type, left_on="affiliation_id", right_on="id"
    )
    paper_author_aff = paper_author_aff.rename(
        index=str, columns={"type": "non_company"}
    )
    paper_author_aff = paper_author_aff.merge(
        mag_papers[["type", "year", "id"]], left_on="paper_id", right_on="id"
    )
    aff_papers = paper_author_aff.drop_duplicates(["affiliation_id", "paper_id"])

    return aff_papers, paper_author_aff
