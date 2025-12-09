import os
from datetime import datetime

# ============================================================================
# CONFIGURAÇÃO
# ============================================================================
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
CACHE_DIR = os.path.join(BASE_DIR, "cache")
os.makedirs(CACHE_DIR, exist_ok=True)

L5_CACHE_FILE = os.path.join(CACHE_DIR, "l5_players.pkl")
SCOREBOARD_JSON_FILE = os.path.join(CACHE_DIR, "scoreboard_today.json")
TEAM_ADVANCED_FILE = os.path.join(CACHE_DIR, "team_advanced.json")
TEAM_OPPONENT_FILE = os.path.join(CACHE_DIR, "team_opponent.json")
NAME_OVERRIDES_FILE = os.path.join(CACHE_DIR, "name_overrides.json")
ODDS_CACHE_FILE = os.path.join(CACHE_DIR, "odds_today.json")
INJURIES_CACHE_FILE = os.path.join(CACHE_DIR, "injuries_cache_v44.json")
MOMENTUM_CACHE_FILE = os.path.join(CACHE_DIR, "momentum_cache.json")
TESES_CACHE_FILE = os.path.join(CACHE_DIR, "teses_cache.json")
DVP_CACHE_FILE = os.path.join(CACHE_DIR, "dvp_cache.json")

SEASON = "2025-26"
TODAY = datetime.now().strftime("%Y-%m-%d")
TODAY_YYYYMMDD = datetime.now().strftime("%Y%m%d")

ESPN_SCOREBOARD_URL = "https://site.web.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard"
ESPN_TEAM_ROSTER_TEMPLATE = "https://site.web.api.espn.com/apis/site/v2/sports/basketball/nba/teams/{team}/roster"

ODDS_API_KEY = "8173a928aa76a59f5aa16bb71666fb8d"
ODDS_API_URL = "https://api.the-odds-api.com/v4/sports/basketball_nba/odds"

HEADERS = {"User-Agent": "Mozilla/5.0"}

TEAM_ABBR_TO_ODDS = {
    "ATL": "Atlanta Hawks","BOS": "Boston Celtics","BKN": "Brooklyn Nets","CHA": "Charlotte Hornets",
    "CHI": "Chicago Bulls","CLE": "Cleveland Cavaliers","DAL": "Dallas Mavericks","DEN": "Denver Nuggets",
    "DET": "Detroit Pistons","GSW": "Golden State Warriors","HOU": "Houston Rockets","IND": "Indiana Pacers",
    "LAC": "Los Angeles Clippers","LAL": "Los Angeles Lakers","MEM": "Memphis Grizzlies","MIA": "Miami Heat",
    "MIL": "Milwaukee Bucks","MIN": "Minnesota Timberwolves","NOP": "New Orleans Pelicans","NYK": "New York Knicks",
    "OKC": "Oklahoma City Thunder","ORL": "Orlando Magic","PHI": "Philadelphia 76ers","PHX": "Phoenix Suns",
    "POR": "Portland Trail Blazers","SAC": "Sacramento Kings","SAS": "San Antonio Spurs","TOR": "Toronto Raptors",
    "UTA": "Utah Jazz","WAS": "Washington Wizards",
    # Variações ESPN
    "UTAH": "Utah Jazz","NY": "New York Knicks","SA": "San Antonio Spurs","NO": "New Orleans Pelicans"
}

# Adicionar após TEAM_ABBR_TO_ODDS
TEAM_PACE_DATA = {
    "ATL": 101.2, "BOS": 99.8, "BKN": 98.5, "CHA": 100.5,
    "CHI": 99.2, "CLE": 98.0, "DAL": 100.8, "DEN": 102.1,
    "DET": 100.3, "GSW": 102.5, "HOU": 101.7, "IND": 103.2,
    "LAC": 100.9, "LAL": 101.3, "MEM": 99.5, "MIA": 98.8,
    "MIL": 101.0, "MIN": 100.2, "NOP": 101.4, "NYK": 99.1,
    "OKC": 102.3, "ORL": 99.4, "PHI": 100.7, "PHX": 101.6,
    "POR": 102.0, "SAC": 103.1, "SAS": 100.1, "TOR": 101.9,
    "UTA": 101.5, "WAS": 102.2
}

# Adicionar nas feature flags
FEATURE_FLAGS = {
    # ... existentes
    "PACE_ADJUSTER": True,
    "VACUUM_MATRIX": True,
    "CORRELATION_FILTERS": True
}

ESPN_TEAM_CODES = {
    "ATL": "atl", "BOS": "bos", "BKN": "bkn", "CHA": "cha", "CHI": "chi",
    "CLE": "cle", "DAL": "dal", "DEN": "den", "DET": "det", "GSW": "gsw",
    "HOU": "hou", "IND": "ind", "LAC": "lac", "LAL": "lal", "MEM": "mem",
    "MIA": "mia", "MIL": "mil", "MIN": "min",
    "NOP": "no", "NO": "no",
    "NYK": "ny", "OKC": "okc", "ORL": "orl", "PHI": "phi", "PHX": "phx",
    "POR": "por", "SAC": "sac", "SAS": "sa", "TOR": "tor", "UTA": "uta",
    "WAS": "wsh",
    "UTAH": "uta", "NY": "ny", "SA": "sa"
}

TESE_LIST = [
    "MinutesSafe", "BigRebound", "UsageSpike", "SynergyRebAst", "LowVariance",
    "TripleThreat", "HiddenReboundValue", "HiddenAssistValue",
    "ReboundMatchup", "AssistMatchup", "HybridRole",
    "RookieBlindado", "BenchMonster", "B2BAzarao",
    "GarbageTimeHistorico", "ViagemLonga", "PivoSobrevivente",
    "DVPPointsMatchup", "DVPReboundMatchup", "DVPAssistMatchup"
]

UPSIDE_TESES = [
    "RookieBlindado", "BenchMonster", "UsageSpike",
    "HiddenReboundValue", "HiddenAssistValue",
    "GarbageTimeHistorico", "PivoSobrevivente", "HybridRole",
    "DVPPointsMatchup", "DVPReboundMatchup", "DVPAssistMatchup"
]

HIGHVALUE_TESES = [
    "MinutesSafe", "LowVariance", "TripleThreat",
    "SynergyRebAst", "ReboundMatchup", "AssistMatchup",
    "DVPPointsMatchup", "DVPReboundMatchup", "DVPAssistMatchup"
]

# ADICIONAR NO FINAL DO ARQUIVO

# Feature Flags (nova seção)
FEATURE_FLAGS = {
    "ADVANCED_PROJECTIONS": True,
    "INJURY_RIPPLE_EFFECT": True,
    "USAGE_SPIKE_DETECTOR": True,
    "MATCHUP_CLASSIFIER": True,
    "SAVE_FAVORITES": True,
    "AUDIT_SYSTEM": False  # Inicialmente desligado
}

# Novos caminhos de cache
CACHE_PATHS_V2 = {
    "projections": os.path.join(CACHE_DIR, "v2", "projections"),
    "advanced_stats": os.path.join(CACHE_DIR, "v2", "advanced_stats"),
    "favorites": os.path.join(CACHE_DIR, "v2", "favorites"),
    "quality_metrics": os.path.join(CACHE_DIR, "v2", "quality_metrics")
}

# Configurações de performance
PERFORMANCE_CONFIG = {
    "max_api_calls_per_minute": 60,
    "cache_ttl_minutes": {
        "injuries": 5,
        "odds": 2,
        "stats": 30,
        "projections": 60
    }
}