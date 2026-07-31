from matcher.matcher import normalize_team_name, NBA_TEAMS


def test_official_name_passes_through():
    assert normalize_team_name("Los Angeles Lakers") == "Los Angeles Lakers"


def test_known_alias_lakers():
    assert normalize_team_name("LA Lakers") == "Los Angeles Lakers"
    assert normalize_team_name("Lakers") == "Los Angeles Lakers"


def test_known_alias_thunder():
    assert normalize_team_name("OKC Thunder") == "Oklahoma City Thunder"
    assert normalize_team_name("OKC") == "Oklahoma City Thunder"


def test_known_alias_knicks():
    assert normalize_team_name("NY Knicks") == "New York Knicks"


def test_fuzzy_fallback_for_typo():
    assert normalize_team_name("Bostn Celtics") == "Boston Celtics"


def test_unknown_team_returns_none():
    assert normalize_team_name("Springfield Isotopes") is None


def test_all_teams_present():
    assert len(NBA_TEAMS) == 30
    assert "Boston Celtics" in NBA_TEAMS
