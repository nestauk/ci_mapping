Mapping Collective Intelligence research
==============================

This research project aims to create a large and open evidence base on Collective Intelligence (CI) research and its intersection with AI.  

The work in this repository is organised in a metaflow pipeline with the following steps:
1. Create a PostgreSQL database and the required tables as shown in the [ER diagram](/ci_db_ER_diagram.png). If they already exist, the initialisation is skipped.
2. Collect papers from MAG based on Fields of Study (FoS). The pickled responses are stored locally in `data/raw/`.
3. Parse the MAG API response in a PostgreSQL database.
4. Collect the level of a Field of Study in MAG's hierarchy.
5. Tag papers as CI and AI+CI. This method could be modified to divide a dataset to core and control groups.
6. Geocode author affiliation using Google Places API.
7. Tag journals as open access based on a seed list.
8. Find the type (industry, non-industry) of affiliations based on a seed list.
9. Process the data used in EDA. This involves changing data types, merging and grouping tables. 
10. Exploratory data analysis of the CI research landscape. Produce Altair plots and store them in `reports/figures` as HTML pages (some of them are interactive).
    - Annual publication increase (base year: 2000)
    - Annual sum of citations
    - Publications by industry and non-industry affiliations
    - International collaborations: % of cross-country teams in CI, AI+CI
    - Industry - academia collaborations: % in CI, AI+CI
    - Adoption of open access by CI, AI+CI
    - Field of study comparison for CI, AI+CI. Produce plots for levels 1, 2, 3 and 4 of the MAG hierarchy.
    - Annual publications in conferences and journals.


### Notes
- You can use the same pipeline to query MAG with a conference or journal name as described in [Orion's docs](https://docs.orion-search.org/docs/The%20model%20config%20file#querying-microsoft-academic-knowledge-api).
- All of the parameters are stored in the `model_config.yaml` file. Exception: Parameters of Altair plots, like width and height, are hardcoded.

## How to rerun the data collection and analysis
1. Clone the repository.
```
$ git clone https://github.com/nestauk/ci_mapping
```

2. Change your working directory to `ci_mapping/` and in an Anaconda environment, install the requirements.
```
$ pip install -r requirements.txt
```

3. Obtain access to [Microsoft Knowledge and Google Places APIs](/ci_mapping/README.md).
4. Create a `.env` file and add your secrets. You can use `.env.example` as an example.
5. Run the metaflow pipeline.
```
$ python ci_mapping/run_pipeline.py --no-pylint run
```

The project assumes you have a [working PostgreSQL distribution installed and running locally](/ci_mapping/README.md/#how-to-setup-and-use-a-postgresql-db).

--------

<p><small>Project based on the <a target="_blank" href="https://github.com/nestauk/cookiecutter-data-science-nesta">Nesta cookiecutter data science project template</a>.</small></p>
