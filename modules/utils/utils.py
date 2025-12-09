# modules/utils.py
import os
import pickle
import json
import re
import tempfile
import unicodedata
import difflib
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from itertools import combinations

# Injuries (flexível)
try:
    from injuries import InjuryMonitor
except Exception:
    InjuryMonitor = None

from modules.config import *

# ============================================================================
# FUNÇÕES UTILITÁRIAS BÁSICAS
# ============================================================================

def normalize_name(n: str) -> str:
    if not n: return ""
    n = str(n).lower()
    n = n.replace(".", " ").replace(",", " ").replace("-", " ")
    n = re.sub(r"\b(jr|sr|ii|iii|iv)\b", "", n)
    n = unicodedata.normalize("NFKD", n).encode("ascii","ignore").decode("ascii")
    return " ".join(n.split())

def safe_abs_spread(val):
    if val is None: return 0.0
    try: return abs(float(val))
    except Exception: return 0.0

def _status_is_out_or_questionable(status: str) -> bool:
    s = (status or "").lower()
    return ("out" in s) or ("questionable" in s) or ("injur" in s) or ("ir" in s)

def atomic_save(path, obj_bytes):
    dirpath = os.path.dirname(path) or "."
    fd, tmp = tempfile.mkstemp(dir=dirpath)
    try:
        with os.fdopen(fd, "wb") as f: f.write(obj_bytes)
        os.replace(tmp, path); return True
    except Exception:
        try:
            if os.path.exists(tmp): os.remove(tmp)
        except Exception: pass
        return False

def save_pickle(path, obj):
    try:
        data = pickle.dumps(obj)
        return atomic_save(path, data)
    except Exception:
        return False

def load_pickle(path):
    try:
        if not os.path.exists(path): return None
        with open(path, "rb") as f: return pickle.load(f)
    except Exception:
        return None

def save_json(path, obj):
    try:
        data = json.dumps(obj, ensure_ascii=False, indent=2).encode("utf-8")
        return atomic_save(path, data)
    except Exception:
        return False

def load_json(path):
    try:
        if not os.path.exists(path): return None
        with open(path, "r", encoding="utf-8") as f: return json.load(f)
    except Exception:
        return None

def init_injury_monitor_flexible():
    if InjuryMonitor is None: return None
    tries = [
        {"cache_file": INJURIES_CACHE_FILE, "ttl_hours": 24},
        {"cache_path": INJURIES_CACHE_FILE, "ttl_hours": 24},
        {"cache_file": INJURIES_CACHE_FILE},
        {"cache_path": INJURIES_CACHE_FILE},
        {}
    ]
    for kwargs in tries:
        try:
            im = InjuryMonitor(**kwargs) if kwargs else InjuryMonitor()
            return im
        except TypeError:
            continue
        except Exception:
            return None
    try:
        return InjuryMonitor()
    except Exception:
        return None

def load_name_overrides():
    data = load_json(NAME_OVERRIDES_FILE)
    return data or {}

def save_name_overrides(overrides):
    save_json(NAME_OVERRIDES_FILE, overrides)

# ============================================================================
# FUNÇÕES DE CARREGAMENTO DE DADOS (SEM IMPORTAR DATA_FETCHERS)
# ============================================================================

def safe_load_initial_data():
    """Carrega dados iniciais no session_state - SEM importação circular"""
    import streamlit as st
    
    # Primeiro, carregar funções básicas de fetch diretamente
    from modules.data_fetchers_simple import (
        fetch_espn_scoreboard_simple, fetch_team_advanced_stats_simple,
        fetch_team_opponent_stats_simple, fetch_odds_for_today_simple
    )
    
    if "scoreboard" not in st.session_state:
        st.session_state.scoreboard = fetch_espn_scoreboard_simple(progress_ui=False)
    
    if "team_advanced" not in st.session_state:
        st.session_state.team_advanced = fetch_team_advanced_stats_simple()
    
    if "team_opponent" not in st.session_state:
        st.session_state.team_opponent = fetch_team_opponent_stats_simple()
    
    if "odds" not in st.session_state:
        st.session_state.odds = fetch_odds_for_today_simple()
    
    if "name_overrides" not in st.session_state:
        st.session_state.name_overrides = load_name_overrides()
    
    if "df_l5" not in st.session_state:
        saved = load_pickle(L5_CACHE_FILE)
        st.session_state.df_l5 = saved.get("df") if saved and isinstance(saved, dict) else pd.DataFrame()
    
    if "injuries_monitor" not in st.session_state or st.session_state.injuries_monitor is None:
        st.session_state.injuries_monitor = init_injury_monitor_flexible()
    
    if "injuries_data" not in st.session_state:
        st.session_state.injuries_data = {}
    
    if "momentum_data" not in st.session_state:
        st.session_state.momentum_data = get_momentum_data()
    
    # Importar DvPAnalyzer somente agora (não tem dependência circular)
    try:
        from modules.dvp_module import DvPAnalyzer
        if "dvp_analyzer" not in st.session_state:
            st.session_state.dvp_analyzer = DvPAnalyzer()
    except ImportError:
        st.session_state.dvp_analyzer = None
    
    # Importar ProjectionEngine somente agora
    try:
        from modules.projection_engine import ProjectionEngine
        if "projection_engine" not in st.session_state:
            st.session_state.projection_engine = ProjectionEngine()
    except ImportError:
        st.session_state.projection_engine = None
    
    # Carregar lesões se houver monitor
    im = st.session_state.injuries_monitor
    if im:
        try:
            if hasattr(im, "get_all_injuries"):
                st.session_state.injuries_data = im.get_all_injuries()
        except Exception:
            st.session_state.injuries_data = {}

# ============================================================================
# MOMENTUM FUNCTIONS
# ============================================================================

def calculate_momentum_score(player_stats):
    """Calcula score de momentum baseado em stats do jogador"""
    if not player_stats:
        return 50.0
    
    try:
        if 'PTS_AVG' not in player_stats:
            return 50.0
        
        score = 50.0
        min_avg = player_stats.get('MIN_AVG', 0)
        if min_avg >= 30:
            score += 10
        elif min_avg >= 20:
            score += 5
        
        pra_avg = player_stats.get('PRA_AVG', 0)
        if pra_avg >= 25:
            score += 15
        elif pra_avg >= 15:
            score += 5
        elif pra_avg < 5:
            score -= 10
        
        min_cv = player_stats.get('MIN_CV', 1.0)
        if min_cv < 0.3:
            score += 10
        elif min_cv > 0.7:
            score -= 10
        
        score = max(0.0, min(100.0, score))
        
        return round(score, 1)
    except Exception:
        return 50.0

def get_momentum_data():
    """Retorna dados de momentum baseados em cache ou cálculo em tempo real"""
    cached = load_json(MOMENTUM_CACHE_FILE)
    if cached:
        return cached
    
    saved = load_pickle(L5_CACHE_FILE)
    df_l5 = saved.get("df") if saved and isinstance(saved, dict) else pd.DataFrame()
    
    momentum_data = {}
    if not df_l5.empty:
        for _, row in df_l5.iterrows():
            player_id = row.get("PLAYER_ID")
            player_name = row.get("PLAYER")
            if player_id and player_name:
                momentum_score = calculate_momentum_score(row.to_dict())
                momentum_data[player_name] = {
                    "score": momentum_score,
                    "team": row.get("TEAM"),
                    "min_avg": row.get("MIN_AVG"),
                    "pra_avg": row.get("PRA_AVG")
                }
    
    save_json(MOMENTUM_CACHE_FILE, momentum_data)
    return momentum_data

# ============================================================================
# VALIDAÇÃO DE PIPELINE
# ============================================================================

def validate_pipeline_integrity(required_components=None):
    """
    Valida se os dados necessários para o pipeline estão disponíveis.
    """
    import streamlit as st
    
    if required_components is None:
        required_components = ['l5', 'scoreboard']
    
    checks = {
        'l5': {
            'name': 'Dados L5 (últimos 5 jogos)',
            'critical': True,
            'status': False,
            'message': ''
        },
        'scoreboard': {
            'name': 'Scoreboard do dia',
            'critical': True,
            'status': False,
            'message': ''
        },
        'odds': {
            'name': 'Odds das casas',
            'critical': False,
            'status': False,
            'message': ''
        },
        'dvp': {
            'name': 'Dados Defense vs Position',
            'critical': False,
            'status': False,
            'message': ''
        },
        'injuries': {
            'name': 'Dados de lesões',
            'critical': False,
            'status': False,
            'message': ''
        }
    }
    
    # Validar L5
    if 'l5' in required_components:
        df_l5 = st.session_state.get('df_l5')
        if df_l5 is not None and hasattr(df_l5, 'shape') and not df_l5.empty:
            checks['l5']['status'] = True
            checks['l5']['message'] = f'Carregados {len(df_l5)} jogadores'
        else:
            checks['l5']['message'] = 'Dados L5 não disponíveis'
    
    # Validar scoreboard
    if 'scoreboard' in required_components:
        scoreboard = st.session_state.get('scoreboard')
        if scoreboard and len(scoreboard) > 0:
            checks['scoreboard']['status'] = True
            checks['scoreboard']['message'] = f'{len(scoreboard)} jogos hoje'
        else:
            checks['scoreboard']['message'] = 'Nenhum jogo encontrado para hoje'
    
    # Validar odds
    if 'odds' in required_components:
        odds = st.session_state.get('odds')
        if odds and len(odds) > 0:
            checks['odds']['status'] = True
            checks['odds']['message'] = f'{len(odds)} jogos com odds'
        else:
            checks['odds']['message'] = 'Odds não disponíveis'
    
    # Validar DvP
    if 'dvp' in required_components:
        dvp_analyzer = st.session_state.get('dvp_analyzer')
        if dvp_analyzer and hasattr(dvp_analyzer, 'defense_data') and dvp_analyzer.defense_data:
            checks['dvp']['status'] = True
            checks['dvp']['message'] = f'Dados de {len(dvp_analyzer.defense_data)} times'
        else:
            checks['dvp']['message'] = 'Dados DvP não disponíveis'
    
    # Validar lesões
    if 'injuries' in required_components:
        injuries = st.session_state.get('injuries_data')
        if injuries and len(injuries) > 0:
            checks['injuries']['status'] = True
            checks['injuries']['message'] = f'Lesões carregadas'
        else:
            checks['injuries']['message'] = 'Dados de lesões não disponíveis'
    
    # Determinar se todos os componentes críticos estão ok
    all_critical_ok = all(
        check['status'] for key, check in checks.items() 
        if key in required_components and check['critical']
    )
    
    return all_critical_ok, checks

# ============================================================================
# CLASSES UTILITÁRIAS
# ============================================================================

class SafetyUtils:
    @staticmethod
    def safe_get(data, keys, default=None):
        try:
            if isinstance(keys, str):
                keys = [keys]
            current = data
            for key in keys:
                if isinstance(current, dict) and key in current:
                    current = current[key]
                elif isinstance(current, list) and isinstance(key, int) and 0 <= key < len(current):
                    current = current[key]
                else:
                    return default
            return current if current is not None else default
        except:
            return default
    
    @staticmethod
    def safe_float(value, default=0.0):
        try:
            if value is None:
                return default
            if isinstance(value, (int, float)):
                return float(value)
            if isinstance(value, str):
                cleaned = ''.join(c for c in value if c.isdigit() or c in '.-')
                return float(cleaned) if cleaned else default
            return float(value)
        except:
            return default

def safe_get(dictionary, key, default=None):
    """Acesso seguro a dicionários com fallback"""
    return dictionary.get(key, default)

def calculate_percentiles(values, percentiles=[90, 95]):
    """Calcula percentis de uma lista de valores"""
    if not values:
        return {}
    
    results = {}
    for p in percentiles:
        results[f'p{p}'] = np.percentile(values, p)
    
    return results

def exponential_backoff(attempt, max_delay=60):
    """Calcula delay para retry com backoff exponencial"""
    return min(max_delay, (2 ** attempt))