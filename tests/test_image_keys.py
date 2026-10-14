from labellens.data.image_keys import choose_key, key_prefix


def test_key_prefix_13_digits()-> None:
    assert key_prefix("4012359114303") == "data/401/235/911/4303/"


def test_key_prefix_12_digit_upc_is_padded()-> None:
    assert key_prefix("012345678905") == "data/001/234/567/8905/"


def test_choose_key_prefers_front_english()-> None:
    keys = [
        "data/1/1.400.jpg",
        "data/1/front_fr.4.400.jpg",
        "data/1/front_en.3.400.jpg",
    ]
    assert choose_key(keys) == "data/1/front_en.3.400.jpg"


def test_choose_key_falls_back_to_numeric() -> None:
    keys = ["data/1/3.400.jpg", "data/1/1.400.jpg"]
    assert choose_key(keys) == "data/1/1.400.jpg"