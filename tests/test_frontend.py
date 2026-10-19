import re

import pytest
from fastapi.testclient import TestClient

from backend import cafes, main

client = TestClient(main.app)


def product_md_block(heading):
    with open("PRODUCT.md") as f:
        section = f.read().split(heading)[1]
    return [line for line in re.search(r"```\n(.*?)```", section, re.S).group(1).splitlines() if line]


def test_page_is_served_at_root():
    res = client.get("/")

    assert res.status_code == 200
    assert "text/html" in res.headers["content-type"]


def test_page_shows_the_product_md_consent_text():
    html = client.get("/").text

    for paragraph in product_md_block("Consent text, one paragraph per line:"):
        assert paragraph.replace("'", "&#39;") in html or paragraph in html


def test_page_consent_version_matches_backend():
    html = client.get("/").text

    assert f'data-consent-version="{main.CONSENT_VERSION}"' in html


def test_script_knows_every_cafe_and_both_greetings():
    js = client.get("/app.js").text

    for slug, name in cafes.CAFES.items():
        assert f'{slug}: "{name}"' in js
    for greeting in product_md_block("Greeting (fixed, shown by the page, not stored)"):
        assert greeting in js


@pytest.mark.parametrize("path", ["/", "/app.js", "/style.css"])
def test_no_third_party_requests(path):
    # Any external URL (font, CDN, analytics) would send the student's IP elsewhere.
    res = client.get(path)

    assert res.status_code == 200
    assert not re.search(r"https?://", res.text)
