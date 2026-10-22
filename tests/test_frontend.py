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


def test_text_box_stops_at_the_backend_limit():
    html = client.get("/").text

    assert f'maxlength="{main.MAX_MESSAGE_LENGTH}"' in html


def test_backend_consent_version_is_the_one_product_md_names():
    with open("PRODUCT.md") as f:
        assert f"Current version: `{main.CONSENT_VERSION}`" in f.read()


def test_page_has_a_mic_button():
    html = client.get("/").text

    assert re.search(r'<button type="button"[^>]*id="mic"', html)


def test_script_sends_recordings_to_transcribe_and_marks_voice_messages():
    js = client.get("/app.js").text

    assert 'fetch("/transcribe"' in js
    assert "input_mode: mode" in js


def test_recording_stops_at_60_seconds():
    js = client.get("/app.js").text

    assert "const MAX_RECORD_SECONDS = 60;" in js


def test_script_only_records_types_the_backend_accepts():
    js = client.get("/app.js").text
    recording_types = re.search(r"const RECORDING_TYPES = \[(.*?)\];", js).group(1)

    assert set(re.findall(r'"([^"]+)"', recording_types)) == main.ALLOWED_AUDIO_TYPES


def test_page_has_a_live_wave_and_a_progress_bar_for_voice():
    html = client.get("/").text

    assert re.search(r'<canvas[^>]*id="wave"', html)
    assert re.search(r'role="progressbar"', html)


def test_hidden_attribute_always_hides():
    # Classes like .btn-mic set display, which would otherwise override [hidden].
    css = client.get("/style.css").text

    assert "[hidden] { display: none !important; }" in css
