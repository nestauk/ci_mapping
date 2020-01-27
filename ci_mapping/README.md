## Microsoft Academic Knowledge API ##

### Getting an API key ###
* Sign up for an API Management account with [Microsoft Research](https://msr-apis.portal.azure-api.net/signup).
* To activate your account, log into the email you used during the registration, open the _Please confirm your new Microsoft Research APIs account_ email and click on the activation link.
* Click on the **Subscribe** button and choose **Project Academic Knowledge**.
* Click again on the **Subscribe** button and then **Confirm** your choice.
* You can now use the **Primary key** to query the API.

### Using your API key in this project ###
The  Microsoft Academic API key is stored in the `.env` file with the following format:

```
mag_key = MY_API_KEY
```

To learn how to use the API, check the [official documentation](https://docs.microsoft.com/en-us/azure/cognitive-services/academic-knowledge/home).

## How to setup and use a PostgreSQL DB ##
Install PostgreSQL:
* For macOS users, the fastest way is to download the [Postgres.app](https://postgresapp.com/) and follow the installation instructions. To connect to a database, make sure that the app is running.
* For all other users, you should be able to find a suitable distribution [here](https://www.postgresql.org/download/).

Then, run `python mag_orm.py` to create the project's database (`ai_ci`) and its tables.

Note that the `.env` file contains two connections to PostgreSQL in the following format:

``` python
postgresdb = postgres+psycopg2://postgres@localhost/ai_ci
test_postgresdb = postgres+psycopg2://postgres@localhost/postgres
```

`ai_ci`: the project's database.  
`postgres`: default database that is shipped with PostgreSQL and used here for testing the ORMs.
