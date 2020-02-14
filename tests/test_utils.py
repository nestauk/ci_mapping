import pytest

from ci_mapping.utils.utils import flatten_lists
from ci_mapping.utils.utils import unique_dicts
from ci_mapping.utils.utils import unique_dicts_by_value
from ci_mapping.utils.utils import cooccurrence_graph
from ci_mapping.utils.utils import allocate_in_group

example_list_dict = [
    {"DFN": "Biology", "FId": 86803240},
    {"DFN": "Biofilm", "FId": 58123911},
    {"DFN": "Bacterial growth", "FId": 17741926},
    {"DFN": "Bacteria", "FId": 523546767},
    {"DFN": "Agar plate", "FId": 62643968},
    {"DFN": "Agar", "FId": 2778660310},
    {"DFN": "Agar", "FId": 2778660310},
    {"DFN": "Agar foo bar", "FId": 2778660310},
]


def test_flatten_lists():
    nested_list = [["a"], ["b"], ["c"]]
    result = flatten_lists(nested_list)
    assert result == ["a", "b", "c"]


def test_unique_dicts():
    result = unique_dicts(example_list_dict)
    expected_result = [
        {"DFN": "Biology", "FId": 86803240},
        {"DFN": "Biofilm", "FId": 58123911},
        {"DFN": "Bacterial growth", "FId": 17741926},
        {"DFN": "Bacteria", "FId": 523546767},
        {"DFN": "Agar plate", "FId": 62643968},
        {"DFN": "Agar", "FId": 2778660310},
        {"DFN": "Agar foo bar", "FId": 2778660310},
    ]
    assert sorted([d["FId"] for d in result]) == sorted(
        [d["FId"] for d in expected_result]
    )


def test_unique_dicts_by_value():
    result = unique_dicts_by_value(example_list_dict, "FId")
    expected_result = [
        {"DFN": "Biology", "FId": 86803240},
        {"DFN": "Biofilm", "FId": 58123911},
        {"DFN": "Bacterial growth", "FId": 17741926},
        {"DFN": "Bacteria", "FId": 523546767},
        {"DFN": "Agar plate", "FId": 62643968},
        {"DFN": "Agar foo bar", "FId": 2778660310},
    ]

    assert result == expected_result


def test_cooccurrence_graph():
    data = [["a", "b"], ["a", "b", "c"]]

    expected_result = Counter({("a", "b"): 2, ("a", "c"): 1, ("b", "c"): 1})
    result = cooccurrence_graph(data)


def test_allocate_in_groups_ai():
    lst = ["ai", "foo", "bar"]
    ai_lst = [
        "ai",
    ]
    ci_lst = ["ci"]

    expected_result = "ai"
    result = allocate_in_group(lst, ci_lst, ai_lst)

    assert result == expected_result


def test_allocate_in_groups_ci():
    lst = ["ci", "foo", "bar"]
    ai_lst = [
        "ai",
    ]
    ci_lst = ["ci"]

    expected_result = "ci"
    result = allocate_in_group(lst, ci_lst, ai_lst)

    assert result == expected_result


def test_allocate_in_groups_ai_ci():
    lst = ["ai", "ci", "foo", "bar"]
    ai_lst = [
        "ai",
    ]
    ci_lst = ["ci"]

    expected_result = "ai_ci"
    result = allocate_in_group(lst, ci_lst, ai_lst)
    
    assert result == expected_result
