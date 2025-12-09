# modules/data_fetchers.py
import os
import time
import requests
import pandas as pd
from datetime import datetime
import json

# ============================================================================
# FUNÇÕES DE CACHE BÁSICAS (sem importar utils)
# ============================================================================

def _load_json_simple(path):
    """Carrega JSON sem dependências circulares"""
    try:
        if not os.path.exists(path): return None
        with open(path, "r", encoding="utf-8") as f: 
            return json.load(f)
    except Exception:
        return None

def _save_json_simple(path, obj):
    """Salva JSON sem dependências circulares"""
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False

def _load_pickle_simple(path):
    """Carrega pickle sem dependências circulares"""
    import pickle
    try:
        if not os.path.exists(path): return None
        with open(path, "rb") as f: return pickle.load(f)
    except Exception:
        return None

# ============================================================================
# CONFIGURAÇÕES (sem importar modules.config completo)
# ============================================================================

# Configurações básicas que precisamos
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
CACHE_DIR = os.path.join(BASE_DIR, "cache")
os.makedirs(CACHE_DIR, exist_ok=True)

L5_CACHE_FILE = os.path.join(CACHE_DIR, "l5_players.pkl")
SCOREBOARD_JSON_FILE = os.path.join(CACHE_DIR, "scoreboard_today.json")
TEAM_ADVANCED_FILE = os.path.join(CACHE_DIR, "team_advanced.json")
TEAM_OPPONENT_FILE = os.path.join(CACHE_DIR, "team_opponent.json")
ODDS_CACHE_FILE = os.path.join(CACHE_DIR, "odds_today.json")

TODAY_YYYYMMDD = datetime.now().strftime("%Y%m%d")
ESPN_SCOREBOARD_URL = "https://site.web.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard"
ESPN_TEAM_ROSTER_TEMPLATE = "https://site.web.api.espn.com/apis/site/v2/sports/basketball/nba/teams/{team}/roster"
ODDS_API_KEY = "8173a928aa76a59f5aa16bb71666fb8d"
ODDS_API_URL = "https://api.the-odds-api.com/v4/sports/basketball_nba/odds"
HEADERS = {"User-Agent": "Mozilla/5.0"}

# ============================================================================
# FUNÇÕES PRINCIPAIS DE FETCH DE DADOS
# ============================================================================

def fetch_espn_scoreboard(date_yyyymmdd=None, progress_ui=True):
    """Busca scoreboard do ESPN"""
    date_yyyymmdd = date_yyyymmdd or TODAY_YYYYMMDD
    params = {"dates": date_yyyymmdd}
    
    try:
        r = requests.get(ESPN_SCOREBOARD_URL, params=params, timeout=10, headers=HEADERS)
        r.raise_for_status()
        j = r.json()
        
        # Salvar em cache
        _save_json_simple(SCOREBOARD_JSON_FILE, j)
        
        games = []
        for ev in j.get("events", []):
            comp_list = ev.get("competitions", []) or []
            if not comp_list: continue
            comp = comp_list[0]
            teams_comp = comp.get("competitors", []) or []
            if len(teams_comp) < 2: continue
            
            home_team = next((t for t in teams_comp if t.get("homeAway") == "home"), teams_comp[0])
            away_team = next((t for t in teams_comp if t.get("homeAway") == "away"), teams_comp[-1])
            
            home = home_team.get("team", {}).get("abbreviation")
            away = away_team.get("team", {}).get("abbreviation")
            
            games.append({
                "gameId": ev.get("id"), 
                "away": away, 
                "home": home,
                "status": comp.get("status", {}).get("type", {}).get("description", ""),
                "startTimeUTC": comp.get("date"), 
                "raw": comp
            })
        
        return games
        
    except Exception as e:
        # Tentar usar cache se a requisição falhar
        cached = _load_json_simple(SCOREBOARD_JSON_FILE)
        if cached:
            games = []
            for ev in cached.get("events", []):
                comp_list = ev.get("competitions", []) or []
                if not comp_list: continue
                comp = comp_list[0]
                teams_comp = comp.get("competitors", []) or []
                if len(teams_comp) < 2: continue
                
                home_team = next((t for t in teams_comp if t.get("homeAway") == "home"), teams_comp[0])
                away_team = next((t for t in teams_comp if t.get("homeAway") == "away"), teams_comp[-1])
                
                home = home_team.get("team", {}).get("abbreviation")
                away = away_team.get("team", {}).get("abbreviation")
                
                games.append({
                    "gameId": ev.get("id"), 
                    "away": away, 
                    "home": home,
                    "status": comp.get("status", {}).get("type", {}).get("description", ""),
                    "startTimeUTC": comp.get("date"), 
                    "raw": comp
                })
            return games
        
        return []

def fetch_team_roster(team_abbr_or_id, progress_ui=True):
    """Busca roster de um time específico"""
    cache_path = os.path.join(CACHE_DIR, f"roster_{team_abbr_or_id}.json")
    
    # Tentar cache primeiro
    cached = _load_json_simple(cache_path)
    if cached:
        return cached
    
    # Mapear código ESPN
    espn_codes = {
        "ATL": "atl", "BOS": "bos", "BKN": "bkn", "CHA": "cha", "CHI": "chi",
        "CLE": "cle", "DAL": "dal", "DEN": "den", "DET": "det", "GSW": "gsw",
        "HOU": "hou", "IND": "ind", "LAC": "lac", "LAL": "lal", "MEM": "mem",
        "MIA": "mia", "MIL": "mil", "MIN": "min", "NOP": "no", "NO": "no",
        "NYK": "ny", "OKC": "okc", "ORL": "orl", "PHI": "phi", "PHX": "phx",
        "POR": "por", "SAC": "sac", "SAS": "sa", "TOR": "tor", "UTA": "uta",
        "WAS": "wsh", "UTAH": "uta", "NY": "ny", "SA": "sa"
    }
    
    espn_code = espn_codes.get(team_abbr_or_id, team_abbr_or_id.lower())
    url = ESPN_TEAM_ROSTER_TEMPLATE.format(team=espn_code)
    
    try:
        r = requests.get(url, timeout=10, headers=HEADERS)
        r.raise_for_status()
        jr = r.json()
        
        # Salvar em cache
        _save_json_simple(cache_path, jr)
        return jr
        
    except Exception as e:
        return {}

def fetch_odds_for_today():
    """Busca odds dos jogos do dia"""
    params = {
        "apiKey": ODDS_API_KEY, 
        "regions": "us", 
        "markets": "spreads,totals", 
        "oddsFormat": "decimal"
    }
    
    try:
        r = requests.get(ODDS_API_URL, params=params, timeout=15)
        r.raise_for_status()
        data = r.json()
        
        odds_map = {}
        team_mapping = {
            "ATL": "Atlanta Hawks", "BOS": "Boston Celtics", "BKN": "Brooklyn Nets",
            "CHA": "Charlotte Hornets", "CHI": "Chicago Bulls", "CLE": "Cleveland Cavaliers",
            "DAL": "Dallas Mavericks", "DEN": "Denver Nuggets", "DET": "Detroit Pistons",
            "GSW": "Golden State Warriors", "HOU": "Houston Rockets", "IND": "Indiana Pacers",
            "LAC": "Los Angeles Clippers", "LAL": "Los Angeles Lakers", "MEM": "Memphis Grizzlies",
            "MIA": "Miami Heat", "MIL": "Milwaukee Bucks", "MIN": "Minnesota Timberwolves",
            "NOP": "New Orleans Pelicans", "NYK": "New York Knicks", "OKC": "Oklahoma City Thunder",
            "ORL": "Orlando Magic", "PHI": "Philadelphia 76ers", "PHX": "Phoenix Suns",
            "POR": "Portland Trail Blazers", "SAC": "Sacramento Kings", "SAS": "San Antonio Spurs",
            "TOR": "Toronto Raptors", "UTA": "Utah Jazz", "WAS": "Washington Wizards"
        }
        
        for game in data:
            home_full = game.get("home_team")
            away_full = game.get("away_team")
            
            if not home_full or not away_full: 
                continue
            
            key_full = f"{away_full}@{home_full}"
            markets = game.get("bookmakers", [])
            
            if not markets: 
                continue
            
            bm = markets[0]
            spread_val = None
            total_val = None
            
            for market in bm.get("markets", []):
                if market.get("key") == "spreads":
                    outcomes = market.get("outcomes", [])
                    for o in outcomes:
                        if o.get("name") == home_full: 
                            spread_val = o.get("point")
                
                if market.get("key") == "totals":
                    outcomes = market.get("outcomes", [])
                    for o in outcomes:
                        if o.get("name") == "Over": 
                            total_val = o.get("point")
            
            odds_map[key_full] = {
                "home_full": home_full, 
                "away_full": away_full,
                "spread": spread_val, 
                "total": total_val,
                "bookmaker": bm.get("title", "unknown"), 
                "last_update": bm.get("last_update", "")
            }
        
        # Salvar em cache
        _save_json_simple(ODDS_CACHE_FILE, odds_map)
        return odds_map
        
    except Exception as e:
        # Usar cache se disponível
        cached = _load_json_simple(ODDS_CACHE_FILE)
        return cached or {}

def fetch_team_advanced_stats():
    """Busca estatísticas avançadas dos times (do cache)"""
    return _load_json_simple(TEAM_ADVANCED_FILE) or {}

def fetch_team_opponent_stats():
    """Busca estatísticas de oponentes dos times (do cache)"""
    return _load_json_simple(TEAM_OPPONENT_FILE) or {}

# ============================================================================
# L5 (NBA API)
# ============================================================================

def fetch_player_stats_safe(pid, name):
    """Busca estatísticas de um jogador específico"""
    try:
        from nba_api.stats.endpoints import commonplayerinfo, playergamelog
        
        info_df = commonplayerinfo.CommonPlayerInfo(player_id=pid).get_data_frames()[0]
        team = info_df["TEAM_ABBREVIATION"].iloc[0] if "TEAM_ABBREVIATION" in info_df.columns else None
        exp = int(info_df["SEASON_EXP"].iloc[0]) if "SEASON_EXP" in info_df.columns else 0
        
        logs = playergamelog.PlayerGameLog(player_id=pid, season="2025-26").get_data_frames()[0]
        if logs is None or logs.empty: 
            return None
        
        logs = logs.head(10)
        for c in ["PTS", "REB", "AST", "MIN"]:
            if c in logs.columns: 
                logs[c] = pd.to_numeric(logs[c], errors="coerce")
        
        last5 = logs.head(5)
        
        def cv_of(s):
            s = s.dropna()
            if s.size == 0 or s.mean() == 0: 
                return 1.0
            return float(s.std(ddof=0) / s.mean())
        
        pts_avg = float(last5["PTS"].mean()) if "PTS" in last5.columns else 0.0
        reb_avg = float(last5["REB"].mean()) if "REB" in last5.columns else 0.0
        ast_avg = float(last5["AST"].mean()) if "AST" in last5.columns else 0.0
        min_avg = float(last5["MIN"].mean()) if "MIN" in last5.columns else 0.0
        
        pra_avg = float((last5["PTS"] + last5["REB"] + last5["AST"]).mean()) if all(x in last5.columns for x in ["PTS", "REB", "AST"]) else 0.0
        
        pts_cv = cv_of(last5["PTS"]) if "PTS" in last5.columns else 1.0
        reb_cv = cv_of(last5["REB"]) if "REB" in last5.columns else 1.0
        ast_cv = cv_of(last5["AST"]) if "AST" in last5.columns else 1.0
        min_cv = cv_of(last5["MIN"]) if "MIN" in last5.columns else 1.0
        
        last_min = float(last5["MIN"].iloc[0]) if "MIN" in last5.columns and not last5["MIN"].isna().all() else min_avg
        
        return {
            "PLAYER_ID": int(pid), "PLAYER": name, "TEAM": team, "EXP": exp,
            "MIN_AVG": min_avg, "PTS_AVG": pts_avg, "REB_AVG": reb_avg,
            "AST_AVG": ast_avg, "PRA_AVG": pra_avg,
            "MIN_CV": min_cv, "PTS_CV": pts_cv, "REB_CV": reb_cv, "AST_CV": ast_cv,
            "LAST_MIN": last_min,
            "min_L5": min_avg, "pts_L5": pts_avg, "reb_L5": reb_avg,
            "ast_L5": ast_avg, "pra_L5": pra_avg,
        }
        
    except Exception:
        return None

def try_fetch_with_retry(pid, name, tries=3, delay=0.6):
    """Tenta buscar stats com retry"""
    for attempt in range(tries):
        res = fetch_player_stats_safe(pid, name)
        if res: 
            return res
        time.sleep(delay * (attempt + 1))
    return None

def get_players_l5(progress_ui=True, batch_size=5):
    """Coleta dados L5 de todos os jogadores ativos"""
    from nba_api.stats.static import players
    
    # Carregar cache existente
    saved = _load_pickle_simple(L5_CACHE_FILE)
    df_cached = saved.get("df") if saved and isinstance(saved, dict) else pd.DataFrame()
    df_final = df_cached.copy() if isinstance(df_cached, pd.DataFrame) else pd.DataFrame()
    
    existing_ids = set(df_final["PLAYER_ID"].astype(int).tolist()) if not df_final.empty else set()
    
    # Obter jogadores ativos
    act_players = players.get_active_players()
    dfp = pd.DataFrame(act_players)[["id", "full_name"]].rename(columns={"id": "PLAYER_ID", "full_name": "PLAYER"})
    
    total = len(dfp)
    attempted = 0
    success = 0
    fail = 0
    
    for _, row in dfp.iterrows():
        attempted += 1
        pid = int(row["PLAYER_ID"])
        pname = row["PLAYER"]
        
        if pid in existing_ids:
            continue
        
        stats = try_fetch_with_retry(pid, pname, tries=3, delay=0.5)
        
        if stats:
            df_final = pd.concat([df_final, pd.DataFrame([stats])], ignore_index=True)
            existing_ids.add(pid)
            success += 1
        else:
            fail += 1
        
        # Salvar backup periódico
        if attempted % batch_size == 0:
            try:
                if not df_final.empty:
                    df_final["PLAYER_ID"] = df_final["PLAYER_ID"].astype(int)
                    df_final = df_final.drop_duplicates(subset="PLAYER_ID", keep="first").reset_index(drop=True)
                
                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_data = {"df": df_final, "timestamp": datetime.now()}
                import pickle
                with open(os.path.join(CACHE_DIR, f"l5_players_backup_{ts}.pkl"), "wb") as f:
                    pickle.dump(backup_data, f)
                    
            except Exception:
                pass
    
    # Salvar final
    if not df_final.empty:
        try:
            df_final["PLAYER_ID"] = df_final["PLAYER_ID"].astype(int)
            df_final = df_final.drop_duplicates(subset="PLAYER_ID", keep="first").reset_index(drop=True)
        except Exception:
            pass
    
    # Salvar no cache principal
    final_data = {"df": df_final, "timestamp": datetime.now()}
    import pickle
    with open(L5_CACHE_FILE, "wb") as f:
        pickle.dump(final_data, f)
    
    return df_final