import pytest

from backend.cafes import load_cafe_context


def test_loads_hashtag_context():
    text = load_cafe_context("hashtag")

    with open("cafes/hashtag.md") as f:
        assert text == f.read()


@pytest.mark.parametrize("cafe", ["starbucks", "unknown", "../.env", ""])
def test_unknown_cafe_raises_clear_error(cafe):
    with pytest.raises(ValueError, match="Unknown cafe"):
        load_cafe_context(cafe)
