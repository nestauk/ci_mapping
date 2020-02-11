import requests
from retrying import retry

ENDPOINT = "https://api.labs.cognitive.microsoft.com/academic/v1.0/evaluate"


def build_composite_expr(query_values, entity_name, year):
    """Builds a composite expression with ANDs in OR to be used as MAG query.

    Args:
        query_values (:obj:`list` of str): Phrases to query MAG with. 
        entity_name (str): MAG attribute that will be used in query.
        year (int): We collect data in the [year, now] timeframe.
    Returns:
        (str) MAG expression.
    
    """
    query_prefix_format = "expr=OR({})"
    and_queries = [
        "".join([f"And(Composite({entity_name}='{query_value}'), Y>={year})"])
        for query_value in query_values
    ]
    return query_prefix_format.format(", ".join(and_queries))


@retry(stop_max_attempt_number=5)
def query_mag_api(expr, fields, subscription_key, query_count=1000, offset=0, timeout=30):
    """Posts a query to the Microsoft Academic Graph Evaluate API.

    Args:
        expr (:obj:`str`): Expression as built by build_expr.
        fields: (:obj:`list` of `str`): Codes of fields to return, as per mag documentation.
        query_count: (:obj:`int`): Number of items to return.
        offset (:obj:`int`): Offset in the results if paging through them.

    Returns:
        (:obj:`dict`): JSON response from the api containing 'expr' (the original expression)
                and 'entities' (the results) keys.
                If there are no results 'entities' is an empty list.

    """
    headers = {
        "Ocp-Apim-Subscription-Key": subscription_key,
        "Content-Type": "application/x-www-form-urlencoded",
    }
    query = f"{expr}&count={query_count}&offset={offset}&model=latest&attributes={','.join(fields)}&timeout={timeout}"

    r = requests.post(ENDPOINT, data=query.encode("utf-8"), headers=headers)
    # try:
    #     r.raise_for_status()
    # except requests.exceptions.HTTPError as error:
    #     print(error)
    #     print(error.response.text)
    r.raise_for_status()

    return r.json()
