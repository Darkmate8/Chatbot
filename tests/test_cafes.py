from backend import cafes


def test_includes_every_cafe_with_a_label():
    text = cafes.load_all_cafe_contexts()

    for slug, name in cafes.CAFES.items():
        assert f"## {name} ({slug})" in text


def test_includes_the_real_hashtag_file():
    text = cafes.load_all_cafe_contexts()

    with open("cafes/hashtag.md") as f:
        assert f.read() in text


def test_missing_file_becomes_no_info_note(tmp_path):
    (tmp_path / "juice_press.md").write_text("Juice Press sells fresh juice.")

    text = cafes.load_all_cafe_contexts(cafes_dir=tmp_path)

    assert "Juice Press sells fresh juice." in text
    assert text.count(cafes.NO_INFO) == 3  # hashtag, coffee_nation, barsha
