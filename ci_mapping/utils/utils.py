from itertools import chain


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


def allocate_in_group(lst, group1, group2):
    """Find Fields of Study in a list.

    Args:
        lst (:obj:`list` of str): Fields of Study of a paper.
        group1 (:obj:`list` of str): CI fields of study.
        group2 (:obj:`list` of str): AI fields of study.

    Returns:
        (str)

    """
    if any(fos in lst for fos in group1) and any(fos in lst for fos in group2):
        return "ai_ci"
    elif any(fos in lst for fos in group1):
        return "ci"
    else:
        return "ai"
