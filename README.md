Mapping Collective Intelligence research
==============================

This research project aims to create a large and open evidence base on CI research activity and its intersection with AI research.

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
