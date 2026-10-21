from scripts import make_qr


def test_one_link_per_cafe_with_the_cafe_set():
    links = make_qr.cafe_links("https://cafe-chat.onrender.com/")

    assert links == {
        "hashtag": "https://cafe-chat.onrender.com/?cafe=hashtag",
        "coffee_nation": "https://cafe-chat.onrender.com/?cafe=coffee_nation",
        "juice_press": "https://cafe-chat.onrender.com/?cafe=juice_press",
        "barsha": "https://cafe-chat.onrender.com/?cafe=barsha",
    }


def test_writes_one_svg_per_cafe(tmp_path):
    make_qr.write_qr_codes("https://cafe-chat.onrender.com", tmp_path)

    assert sorted(p.name for p in tmp_path.iterdir()) == ["barsha.svg", "coffee_nation.svg", "hashtag.svg", "juice_press.svg"]
    assert (tmp_path / "hashtag.svg").read_text().startswith("<?xml")
