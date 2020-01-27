import pytest
from unittest import mock

from ci_mapping.data.query_mag_composite import query_mag_api
from ci_mapping.data.query_mag_composite import build_composite_expr


def test_build_composite_queries_correctly():
    assert (
        build_composite_expr(["dog", "cat"], "F.FN", 2000)
        == "expr=OR(And(Composite(F.FN='dog'), Y>=2000), And(Composite(F.FN='cat'), Y>=2000))"
    )


@mock.patch("fnf.data.query_mag_composite.requests.post", autospec=True)
def test_query_mag_api_sends_correct_request(mocked_requests):
    sub_key = 123
    fields = ["Id", "Ti"]
    expr = "expr=OR(And(Composite(F.FN='dog'), Y>=2000), And(Composite(F.FN='cat'), Y>=2000))"
    query_mag_api(expr, fields, sub_key, query_count=10, offset=0)
    expected_call_args = mock.call(
        "https://api.labs.cognitive.microsoft.com/academic/v1.0/evaluate",
        data=b"expr=OR(And(Composite(F.FN='dog'), Y>=2000), And(Composite(F.FN='cat'), Y>=2000))&count=10&offset=0&model=latest&attributes=Id,Ti",
        headers={
            "Ocp-Apim-Subscription-Key": 123,
            "Content-Type": "application/x-www-form-urlencoded",
        },
    )
    assert mocked_requests.call_args == expected_call_args
