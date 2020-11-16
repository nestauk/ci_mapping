from itertools import chain, combinations
from collections import OrderedDict, Counter
from datetime import datetime
import numpy as np


def inverted2abstract(obj):
    """Transforms an inverted abstract to abstract.
    
    Args:
        obj (json): Inverted Abstract.

    Returns:
        (str): Formatted abstract.
    
    """
    if isinstance(obj, dict):
        inverted_index = obj["InvertedIndex"]
        d = {}
        for k, v in inverted_index.items():
            if len(v) == 1:
                d[v[0]] = k
            else:
                for idx in v:
                    d[idx] = k

        return " ".join([v for _, v in OrderedDict(sorted(d.items())).items()]).replace(
            "\x00", ""
        )
    else:
        return np.nan


def unique_dicts(d):
    """Removes duplicate dictionaries from a list.

    Args:
        d (:obj:`list` of :obj:`dict`): List of dictionaries with the same keys.
    
    Returns
       (:obj:`list` of :obj:`dict`)
    
    """
    return [dict(y) for y in set(tuple(x.items()) for x in d)]


def unique_dicts_by_value(d, key):
    """Removes duplicate dictionaries from a list by filtering one of the key values.

    Args:
        d (:obj:`list` of :obj:`dict`): List of dictionaries with the same keys.
    
    Returns
       (:obj:`list` of :obj:`dict`)
    
    """
    return list({v[key]: v for v in d}.values())


def flatten_lists(lst):
    """Unpacks nested lists into one list of elements.

    Args:
        lst (:obj:`list` of :obj:`list`)

    Returns
        (list)
    
    """
    return list(chain(*lst))


def cooccurrence_graph(elements):
    """Creates a cooccurrence table from a nested list.

    Args:
        elements (:obj:`list` of :obj:`list`): Nested list.

    Returns:
        (`collections.Counter`) of the form Counter({('country_a, country_b), weight})

    """
    # Get a list of all of the combinations you have
    expanded = [tuple(combinations(d, 2)) for d in elements]
    expanded = chain(*expanded)

    # Sort the combinations so that A,B and B,A are treated the same
    expanded = [tuple(sorted(d)) for d in expanded]

    # count the combinations
    return Counter(expanded)


def allocate_in_group(lst, fos_subset, tag="CI", fos_subset_tag="AI_CI"):
    """Find Fields of Study in a list.

    Args:
        lst (:obj:`list` of str): Fields of Study of a paper.
        group1 (:obj:`list` of str): CI fields of study.
        group2 (:obj:`list` of str): AI fields of study.

    Returns:
        (str)

    """
    if len(set(fos_subset) & set(lst)) > 0:
        return fos_subset_tag
    else:
        return tag


def str2datetime(input_date):
    """Transform a string to datetime object.

    Args:
        input_date (str): String date of the format Y-m-d. It can
            also be 'today' which will return today's date.

    Returns:
        (`datetime.datetime`)

    """
    if input_date == "today":
        return datetime.today()
    else:
        return datetime.strptime(input_date, "%Y-%m-%d")


def date_range(start, end, intv):
    """Splits a date range into intervals.

    Args:
        start (str): Start date of the format (Y-m-d).
        intv (int): Number of intervals.
        end (str): End date of the format (Y-m-d).

    Returns:
        (:obj:`generator` of `str`) Dates with the (Y-m-d) format.

    """
    diff = (end - start) / intv
    for i in range(intv):
        yield (start + diff * i).strftime("%Y-%m-%d")
    yield end.strftime("%Y-%m-%d")
