Mapping Collective Intelligence research
==============================

This research project aims to provide a large and open evidence base on CI research activity and its intersection with AI research.

## How to use the repo ##
To rerun the data collection and analysis, create a separate Anaconda environment, run `$ pip install -r requirements.txt` to install the Python packages needed for the project, get the required API keys and setup PostgreSQL as described [here](/ci_mapping/README.md). Then, run the following scripts contained in the `ci_mapping` directory:

1. `$ python data/mag_orm.py`: Creates a PostgreSQL DB named `ai_ci` and the tables needed for this project.
2. `$ python query_fos_mag.py`: Collects data from MAG for sets of Fields of Study.
3. `$ python parse_mag.py`: Parses the MAG responses and stores them in PostgreSQL DB.
4. `$ python geocode_affiliations.py`: Geocodes author affiliations.
5. `$ python split_core_control.py`: Splits the data in three groups: AI, AI+CI, CI
6. `$ python collect_fos_level.py`: Collects the level in the MAG hierarchy of the Fields of Study in the DB.
7. `$ python vizualization/draw_cooccurrence_graph.py` (optional): Filter Fields of Study by level and frequency and draw a cooccurrence network.

Project Organization
------------

    ├── LICENSE
    ├── Makefile           <- Makefile with commands like `make data` or `make dvc`
    ├── README.md          <- The top-level README for developers using this project.
    ├── data
    │   ├── README.md
    │   ├── external       <- Data from third party sources.
    │   ├── interim        <- Intermediate data that has been transformed.
    │   ├── processed      <- The final, canonical data sets for modeling.
    │   ├── aux            <- Non-automatable human interventions, e.g. hand selected record ID's to ignore
    │   └── raw            <- The original, immutable data dump.
    │
    ├── docs               <- A default Sphinx project; see sphinx-doc.org for details
    │
    ├── logging.yaml       <- Logging config
    │
    ├── models             <- Trained and serialized models, model predictions, or model summaries
    │
    ├── model_config.yaml  <- Model configuration parameters
    │
    ├── notebooks          <- Jupyter notebooks. Notebooks at the top level should have a markdown header
    │   │                     outlining the notebook and should avoid function calls in favour of factored out code.
    │   ├── notebook_preamble.ipy
    │   │                     
    │   └── dev            <- Development notebooks. Naming convention is a number (for ordering),
    │                         the creator's initials, and a short `_` delimited description, e.g.
    │                         `01_jmg_eda.ipynb`.
    │
    ├── pipe               <- Contains DVC pipeline files
    │
    ├── references         <- Data dictionaries, manuals, and all other explanatory materials.
    │
    ├── reports            <- Generated analysis as HTML, PDF, LaTeX, etc.
    │   └── figures        <- Generated graphics and figures to be used in reporting
    │
    ├── requirements.txt   <- The requirements file for reproducing the analysis environment, e.g.
    │                         generated with `pip freeze > requirements.txt`
    │
    ├── setup.py           <- makes project pip installable (pip install -e .) so ci_mapping can be imported
    │
    ├── ci_mapping                <- Source code for use in this project.
    │   ├── __init__.py    <- Makes ci_mapping a Python module
    │   │
    │   ├── data           <- Scripts to download or generate data
    │   │   └── make_dataset.py
    │   │
    │   ├── features       <- Scripts to turn raw data into features for modeling
    │   │   └── build_features.py
    │   │
    │   ├── models         <- Scripts to train models and then use trained models to make
    │   │   │                 predictions
    │   │   ├── predict_model.py
    │   │   └── train_model.py
    │   │
    │   └── visualization  <- Scripts to create exploratory and results oriented visualizations
    │       └── visualize.py
    │
    └── tox.ini            <- tox file with settings for running tox; see tox.readthedocs.io


--------

<p><small>Project based on the <a target="_blank" href="https://github.com/nestauk/cookiecutter-data-science-nesta">Nesta cookiecutter data science project template</a>.</small></p>
