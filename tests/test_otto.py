from otto import build_otto, OttoConfig, SPECIALISTS
from otto.graph import _route


def test_roster_nonempty():
    assert len(SPECIALISTS) >= 5
    assert "o7" in SPECIALISTS and "devil" in SPECIALISTS


def test_build_compiles():
    assert build_otto(OttoConfig()) is not None


def test_build_with_persistence():
    assert build_otto(OttoConfig(persist=True)) is not None


def test_route_to_specialist():
    assert _route({"next": "o7"}) == "o7"


def test_route_done_goes_to_finalize():
    assert _route({"next": "done"}) == "finalize"


def test_route_unknown_falls_back_to_finalize():
    assert _route({"next": "not_a_real_agent"}) == "finalize"
