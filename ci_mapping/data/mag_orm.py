from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import TEXT, VARCHAR, TSVECTOR
from sqlalchemy import Column, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.types import Integer, Date, Boolean, Float, BIGINT

Base = declarative_base()


class Paper(Base):
    """MAG papers."""

    __tablename__ = "mag_papers"

    id = Column(BIGINT, primary_key=True, autoincrement=False)
    prob = Column(Float)
    title = Column(TEXT)
    publication_type = Column(TEXT)
    year = Column(TEXT)
    date = Column(TEXT)
    citations = Column(Integer)
    references = Column(
        TEXT
    )  # This is transformed from list to string using json.dumps().
    doi = Column(VARCHAR(200))
    publisher = Column(TEXT)
    bibtex_doc_type = Column(TEXT)
    abstract = Column(TEXT)
    journals = relationship("Journal", back_populates="paper")
    fields_of_study = relationship("PaperFieldsOfStudy", back_populates="paper")
    authors = relationship("PaperAuthor", back_populates="paper")


class Journal(Base):
    """Journal where a paper was published."""

    __tablename__ = "mag_paper_journal"

    id = Column(BIGINT)
    journal_name = Column(TEXT)
    paper_id = Column(
        BIGINT, ForeignKey("mag_papers.id"), primary_key=True, autoincrement=False
    )
    paper = relationship("Paper")


class Conference(Base):
    """Conference where a paper was published."""

    __tablename__ = "mag_paper_conferences"

    id = Column(BIGINT)
    conference_name = Column(TEXT)
    paper_id = Column(
        BIGINT, ForeignKey("mag_papers.id"), primary_key=True, autoincrement=False
    )
    paper = relationship("Paper")


class PaperAuthor(Base):
    """Authors of a paper."""

    __tablename__ = "mag_paper_authors"

    paper_id = Column(
        BIGINT, ForeignKey("mag_papers.id"), primary_key=True, autoincrement=False
    )
    author_id = Column(
        BIGINT, ForeignKey("mag_authors.id"), primary_key=True, autoincrement=False
    )
    order = Column(Integer)
    paper = relationship("Paper", back_populates="authors")
    author = relationship("Author", back_populates="papers")


class Author(Base):
    """Details of an author."""

    __tablename__ = "mag_authors"

    id = Column(BIGINT, primary_key=True, autoincrement=False)
    name = Column(TEXT)
    papers = relationship("PaperAuthor", back_populates="author")
    affiliation = relationship("AuthorAffiliation")


class Affiliation(Base):
    """Details of an author affiliation."""

    __tablename__ = "mag_affiliation"

    id = Column(BIGINT, primary_key=True)
    affiliation = Column(TEXT)
    author_affiliation = relationship("AuthorAffiliation")
    aff_location = relationship("AffiliationLocation")


class AuthorAffiliation(Base):
    """Linking papers with authors and their affiliation."""

    __tablename__ = "mag_author_affiliation"

    id = Column(Integer, primary_key=True, autoincrement=True)
    affiliation_id = Column(BIGINT, ForeignKey("mag_affiliation.id"))
    author_id = Column(BIGINT, ForeignKey("mag_authors.id"))
    paper_id = Column(BIGINT, ForeignKey("mag_papers.id"))
    affiliations = relationship("Affiliation")
    authors = relationship("Author")


class FieldOfStudy(Base):
    """Fields of study."""

    __tablename__ = "mag_fields_of_study"

    id = Column(BIGINT, primary_key=True, autoincrement=False)
    name = Column(VARCHAR(250))
    norm_name = Column(VARCHAR(250))


class PaperFieldsOfStudy(Base):
    """Linking papers with their fields of study."""

    __tablename__ = "mag_paper_fields_of_study"

    paper_id = Column(
        BIGINT, ForeignKey("mag_papers.id"), primary_key=True, autoincrement=False
    )
    field_of_study_id = Column(
        BIGINT,
        ForeignKey("mag_fields_of_study.id"),
        primary_key=True,
        autoincrement=False,
    )
    paper = relationship("Paper", back_populates="fields_of_study")
    field_of_study = relationship("FieldOfStudy")


class AffiliationLocation(Base):
    """Geographic information of an affiliation."""

    __tablename__ = "geocoded_places"

    id = Column(TEXT, primary_key=True, autoincrement=False)
    affiliation_id = Column(
        BIGINT, ForeignKey("mag_affiliation.id"), primary_key=True, autoincrement=False
    )
    lat = Column(Float)
    lng = Column(Float)
    address = Column(TEXT)
    name = Column(TEXT)
    types = Column(TEXT)
    website = Column(TEXT)
    postal_town = Column(TEXT)
    administrative_area_level_2 = Column(TEXT)
    administrative_area_level_1 = Column(TEXT)
    country = Column(TEXT)
    geocoded_affiliation = relationship("Affiliation", back_populates="aff_location")


class FosMetadata(Base):
    """Level in the hierarchy and the frequency of a Field of Study."""

    __tablename__ = "mag_field_of_study_metadata"
    id = Column(
        BIGINT,
        ForeignKey("mag_fields_of_study.id"),
        primary_key=True,
        autoincrement=False,
    )
    level = Column(Integer)


class CoreControlGroup(Base):
    """Shows the subset (AI, AI/CI, CI) of a paper."""

    __tablename__ = "core_control_group"
    id = Column(
        BIGINT, ForeignKey("mag_papers.id"), primary_key=True, autoincrement=False
    )
    type = Column(TEXT)


class OpenAccess(Base):
    """Flags open access journals."""

    __tablename__ = "open_access_journals"

    id = Column(BIGINT, primary_key=True)
    open_access = Column(Integer)


class AffiliationType(Base):
    """Type (1: non-industry, 0: industry) of an affiliation."""

    __tablename__ = "affiliation_type"

    id = Column(
        BIGINT, ForeignKey("mag_affiliation.id"), primary_key=True, autoincrement=False
    )
    type = Column(Integer)


if __name__ == "__main__":
    import os
    import logging
    import psycopg2
    from dotenv import load_dotenv, find_dotenv
    from sqlalchemy import create_engine, exc

    load_dotenv(find_dotenv())

    # Try to create the database if it doesn't already exist.
    try:
        engine = create_engine(os.getenv("test_db"))
        conn = engine.connect()
        conn.execute("commit")
        conn.execute("create database ci_db")
        conn.close()
    except exc.DBAPIError as e:
        if isinstance(e.orig, psycopg2.errors.DuplicateDatabase):
            logging.info(e)
        else:
            logging.error(e)
            raise

    db_config = os.getenv("ci_db")
    engine = create_engine(db_config)
    Base.metadata.create_all(engine)
