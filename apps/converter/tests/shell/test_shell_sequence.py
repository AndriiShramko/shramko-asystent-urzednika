"""Integration: slots are given back. Many requests in a row, with and without a context-managed client, never
meet BUSY while nothing runs in parallel (a leaked slot would show here after CONCURRENCY requests)."""
from __future__ import annotations

import factory as fx
import pytest
from test_shell_http import make_client, post, secret_file  # noqa: F401


@pytest.mark.parametrize("managed", [False, True])
def test_sequential_requests_never_meet_busy(tmp_path, secret_file, managed):  # noqa: F811
    client = make_client(tmp_path, secret_file, CONCURRENCY=2)
    data = fx.pdf()
    if managed:
        with client:
            codes = [post(client, "/v1/forms/convert", "a.pdf", data).status_code for _ in range(12)]
    else:
        codes = [post(client, "/v1/forms/convert", "a.pdf", data).status_code for _ in range(12)]
    assert codes == [200] * 12
