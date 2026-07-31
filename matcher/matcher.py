import difflib

NBA_TEAMS = [
    "Atlanta Hawks", "Boston Celtics", "Brooklyn Nets", "Charlotte Hornets",
    "Chicago Bulls", "Cleveland Cavaliers", "Dallas Mavericks", "Denver Nuggets",
    "Detroit Pistons", "Golden State Warriors", "Houston Rockets", "Indiana Pacers",
    "LA Clippers", "Los Angeles Lakers", "Memphis Grizzlies", "Miami Heat",
    "Milwaukee Bucks", "Minnesota Timberwolves", "New Orleans Pelicans",
    "New York Knicks", "Oklahoma City Thunder", "Orlando Magic",
    "Philadelphia 76ers", "Phoenix Suns", "Portland Trail Blazers",
    "Sacramento Kings", "San Antonio Spurs", "Toronto Raptors", "Utah Jazz",
    "Washington Wizards",
]

TEAM_ALIASES = {
    "lakers": "Los Angeles Lakers", "la lakers": "Los Angeles Lakers",
    "celtics": "Boston Celtics",
    "warriors": "Golden State Warriors", "gs warriors": "Golden State Warriors",
    "heat": "Miami Heat",
    "thunder": "Oklahoma City Thunder", "okc thunder": "Oklahoma City Thunder", "okc": "Oklahoma City Thunder",
    "nuggets": "Denver Nuggets",
    "bucks": "Milwaukee Bucks",
    "suns": "Phoenix Suns",
    "mavericks": "Dallas Mavericks", "mavs": "Dallas Mavericks",
    "knicks": "New York Knicks", "ny knicks": "New York Knicks",
    "clippers": "LA Clippers", "la clippers": "LA Clippers",
    "hawks": "Atlanta Hawks",
    "nets": "Brooklyn Nets",
    "hornets": "Charlotte Hornets",
    "bulls": "Chicago Bulls",
    "cavaliers": "Cleveland Cavaliers", "cavs": "Cleveland Cavaliers",
    "pistons": "Detroit Pistons",
    "rockets": "Houston Rockets",
    "pacers": "Indiana Pacers",
    "grizzlies": "Memphis Grizzlies",
    "timberwolves": "Minnesota Timberwolves", "wolves": "Minnesota Timberwolves",
    "pelicans": "New Orleans Pelicans",
    "magic": "Orlando Magic",
    "76ers": "Philadelphia 76ers", "sixers": "Philadelphia 76ers",
    "trail blazers": "Portland Trail Blazers", "blazers": "Portland Trail Blazers",
    "kings": "Sacramento Kings",
    "spurs": "San Antonio Spurs",
    "raptors": "Toronto Raptors",
    "jazz": "Utah Jazz",
    "wizards": "Washington Wizards",
}


def normalize_team_name(name: str) -> str | None:
    key = name.strip().lower()
    if key in TEAM_ALIASES:
        return TEAM_ALIASES[key]

    matches = difflib.get_close_matches(name.strip(), NBA_TEAMS, n=1, cutoff=0.6)
    if matches:
        return matches[0]

    return None
