# modules/dvp_module.py
import os
import json
from datetime import datetime

# IMPORTAR FUNÇÕES DE UTILS DIRETAMENTE
try:
    # Tentar importar do módulo utils
    from modules.utils import load_pickle, load_json, save_json, SafetyUtils
except ImportError:
    # Fallback: criar funções básicas localmente
    import pickle
    
    def load_pickle(path):
        try:
            if not os.path.exists(path): return None
            with open(path, "rb") as f: return pickle.load(f)
        except Exception:
            return None
    
    def load_json(path):
        try:
            if not os.path.exists(path): return None
            with open(path, "r", encoding="utf-8") as f: return json.load(f)
        except Exception:
            return None
    
    def save_json(path, obj):
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(obj, f, ensure_ascii=False, indent=2)
            return True
        except Exception:
            return False
    
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

from modules.config import *

# ============================================================================
# DvP MODULE - CORRIGIDO
# ============================================================================

class DefenseDataFetcher:
    def __init__(self):
        self.safety = SafetyUtils()
    
    def fetch_defense_vs_position_data(self, use_cache=True):
        if use_cache:
            cached = load_json(DVP_CACHE_FILE)
            if cached and "data" in cached:
                last_update = datetime.fromisoformat(cached.get("last_updated", "1970-01-01"))
                if (datetime.now() - last_update).total_seconds() < 86400:
                    return cached["data"]
        
        return self._generate_from_l5_data()
    
    def _generate_from_l5_data(self):
        try:
            saved = load_pickle(L5_CACHE_FILE)
            df_l5 = saved.get("df") if saved and isinstance(saved, dict) else pd.DataFrame()
            
            if df_l5.empty:
                return self._get_fallback_data()
            
            dvp_data = {}
            teams = df_l5["TEAM"].unique()
            
            for team in teams:
                team_data = df_l5[df_l5["TEAM"] == team]
                
                dvp_data[team] = {
                    "PG": {
                        "points": round(team_data["PTS_AVG"].quantile(0.8), 1) if len(team_data) > 0 else 25.0,
                        "rebounds": round(team_data["REB_AVG"].quantile(0.3), 1) if len(team_data) > 0 else 5.2,
                        "assists": round(team_data["AST_AVG"].quantile(0.9), 1) if len(team_data) > 0 else 8.5
                    },
                    "SG": {
                        "points": round(team_data["PTS_AVG"].quantile(0.7), 1) if len(team_data) > 0 else 24.0,
                        "rebounds": round(team_data["REB_AVG"].quantile(0.4), 1) if len(team_data) > 0 else 6.0,
                        "assists": round(team_data["AST_AVG"].quantile(0.6), 1) if len(team_data) > 0 else 4.3
                    },
                    "SF": {
                        "points": round(team_data["PTS_AVG"].quantile(0.6), 1) if len(team_data) > 0 else 23.0,
                        "rebounds": round(team_data["REB_AVG"].quantile(0.5), 1) if len(team_data) > 0 else 7.0,
                        "assists": round(team_data["AST_AVG"].quantile(0.4), 1) if len(team_data) > 0 else 3.5
                    },
                    "PF": {
                        "points": round(team_data["PTS_AVG"].quantile(0.5), 1) if len(team_data) > 0 else 22.0,
                        "rebounds": round(team_data["REB_AVG"].quantile(0.7), 1) if len(team_data) > 0 else 8.5,
                        "assists": round(team_data["AST_AVG"].quantile(0.3), 1) if len(team_data) > 0 else 2.8
                    },
                    "C": {
                        "points": round(team_data["PTS_AVG"].quantile(0.4), 1) if len(team_data) > 0 else 21.0,
                        "rebounds": round(team_data["REB_AVG"].quantile(0.9), 1) if len(team_data) > 0 else 11.5,
                        "assists": round(team_data["AST_AVG"].quantile(0.2), 1) if len(team_data) > 0 else 2.3
                    }
                }
            
            cache_obj = {
                "data": dvp_data,
                "last_updated": datetime.now().isoformat(),
                "source": "Generated from L5 data"
            }
            save_json(DVP_CACHE_FILE, cache_obj)
            
            return dvp_data
            
        except Exception as e:
            return self._get_fallback_data()
    
    def _get_fallback_data(self):
        return {
            "ATL": {"PG": {"points": 26.3, "rebounds": 5.2, "assists": 8.7},
                   "SG": {"points": 25.1, "rebounds": 6.3, "assists": 4.5},
                   "SF": {"points": 24.8, "rebounds": 7.4, "assists": 3.8},
                   "PF": {"points": 23.5, "rebounds": 9.2, "assists": 2.9},
                   "C": {"points": 22.1, "rebounds": 12.8, "assists": 2.4}},
            "LAL": {"PG": {"points": 25.9, "rebounds": 5.4, "assists": 8.5},
                   "SG": {"points": 24.7, "rebounds": 6.4, "assists": 4.3},
                   "SF": {"points": 24.1, "rebounds": 7.6, "assists": 3.6},
                   "PF": {"points": 22.8, "rebounds": 9.3, "assists": 2.7},
                   "C": {"points": 21.5, "rebounds": 12.3, "assists": 2.2}},
            "GSW": {"PG": {"points": 27.5, "rebounds": 5.8, "assists": 9.3},
                   "SG": {"points": 26.2, "rebounds": 6.7, "assists": 4.9},
                   "SF": {"points": 25.6, "rebounds": 7.9, "assists": 4.1},
                   "PF": {"points": 24.3, "rebounds": 9.8, "assists": 3.2},
                   "C": {"points": 23.8, "rebounds": 13.5, "assists": 2.7}}
        }

class DvPAnalyzer:
    def __init__(self, cache_dir="cache"):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
        self.cache_file = DVP_CACHE_FILE
        self.defense_data = {}
        self.safety = SafetyUtils()
        self.data_fetcher = DefenseDataFetcher()
        self._load_or_fetch_data()
    
    def _load_or_fetch_data(self):
        try:
            if os.path.exists(self.cache_file):
                cache_data = json.load(open(self.cache_file, 'r', encoding='utf-8'))
                last_update = datetime.fromisoformat(cache_data.get("last_updated", "1970-01-01"))
                if (datetime.now() - last_update).total_seconds() < 86400:
                    self.defense_data = cache_data.get("data", {})
                    return True
            
            raw_data = self.data_fetcher.fetch_defense_vs_position_data(use_cache=True)
            
            if raw_data:
                self.defense_data = self._normalize_defense_data(raw_data)
                cache_obj = {
                    "data": self.defense_data,
                    "last_updated": datetime.now().isoformat(),
                    "source": "NBA.com / Basketball Reference"
                }
                with open(self.cache_file, 'w', encoding='utf-8') as f:
                    json.dump(cache_obj, f, indent=2, ensure_ascii=False)
                return True
            else:
                self.defense_data = {}
                return False
        except Exception:
            self.defense_data = {}
            return False
    
    def _normalize_defense_data(self, raw_data):
        normalized = {}
        for team_abbr, stats in raw_data.items():
            normalized[team_abbr] = {
                "points_allowed_pg": {
                    "PG": self.safety.safe_float(self.safety.safe_get(stats, ["PG", "points"], 25.0)),
                    "SG": self.safety.safe_float(self.safety.safe_get(stats, ["SG", "points"], 24.0)),
                    "SF": self.safety.safe_float(self.safety.safe_get(stats, ["SF", "points"], 23.0)),
                    "PF": self.safety.safe_float(self.safety.safe_get(stats, ["PF", "points"], 22.0)),
                    "C": self.safety.safe_float(self.safety.safe_get(stats, ["C", "points"], 21.0))
                },
                "rebounds_allowed_pg": {
                    "PG": self.safety.safe_float(self.safety.safe_get(stats, ["PG", "rebounds"], 5.0)),
                    "SG": self.safety.safe_float(self.safety.safe_get(stats, ["SG", "rebounds"], 6.0)),
                    "SF": self.safety.safe_float(self.safety.safe_get(stats, ["SF", "rebounds"], 7.0)),
                    "PF": self.safety.safe_float(self.safety.safe_get(stats, ["PF", "rebounds"], 9.0)),
                    "C": self.safety.safe_float(self.safety.safe_get(stats, ["C", "rebounds"], 12.0))
                },
                "assists_allowed_pg": {
                    "PG": self.safety.safe_float(self.safety.safe_get(stats, ["PG", "assists"], 8.0)),
                    "SG": self.safety.safe_float(self.safety.safe_get(stats, ["SG", "assists"], 4.0)),
                    "SF": self.safety.safe_float(self.safety.safe_get(stats, ["SF", "assists"], 3.0)),
                    "PF": self.safety.safe_float(self.safety.safe_get(stats, ["PF", "assists"], 2.5)),
                    "C": self.safety.safe_float(self.safety.safe_get(stats, ["C", "assists"], 2.0))
                }
            }
        return normalized

    def get_position_rank(self, team_abbr, position, metric="points"):
        if team_abbr not in self.defense_data:
            return 15
        
        allowed = self.defense_data[team_abbr].get(f"{metric}_allowed_pg", {})
        value = allowed.get(position, 20.0)
        
        teams = list(self.defense_data.keys())
        values = []
        
        for team in teams:
            if team in self.defense_data:
                team_allowed = self.defense_data[team].get(f"{metric}_allowed_pg", {})
                team_value = team_allowed.get(position, 20.0)
                values.append((team, team_value))
        
        values.sort(key=lambda x: x[1], reverse=True)
        
        for rank, (team, _) in enumerate(values, 1):
            if team == team_abbr:
                return rank
        
        return 15

    def get_dvp_multiplier(self, opponent_team, player_position, stat_category):
        if not opponent_team or not player_position:
            return 1.0
        
        pos_map = {
            "point guard": "PG", "pg": "PG", "guard": "PG",
            "shooting guard": "SG", "sg": "SG", "g": "SG",
            "small forward": "SF", "sf": "SF", "forward": "SF",
            "power forward": "PF", "pf": "PF", "f": "PF",
            "center": "C", "c": "C"
        }
        
        pos_key = player_position.lower().strip()
        pos_abbr = pos_map.get(pos_key, None)
        
        if not pos_abbr:
            for k, v in pos_map.items():
                if k in pos_key:
                    pos_abbr = v
                    break
            if not pos_abbr:
                return 1.0
        
        metric_map = {
            "pts": "points", "points": "points", "scoring": "points",
            "reb": "rebounds", "rebounds": "rebounds", "boards": "rebounds",
            "ast": "assists", "assists": "assists", "dimes": "assists",
            "fg%": "points", "fgp": "points",
            "ft%": "points", "ftp": "points",
            "3pm": "points", "threes": "points",
            "stl": "assists",
            "blk": "rebounds",
            "to": "assists"
        }
        
        metric = metric_map.get(stat_category.lower(), "points")
        
        rank = self.get_position_rank(opponent_team, pos_abbr, metric)
        
        if rank <= 5:
            return 1.15
        elif rank <= 10:
            return 1.08
        elif rank >= 25:
            return 0.85
        elif rank >= 20:
            return 0.92
        else:
            return 1.0
    
    def get_matchup_analysis(self, opponent_team, player_position):
        analysis = {
            "team": opponent_team,
            "position": player_position,
            "rankings": {},
            "multipliers": {},
            "overall": 1.0
        }
        
        for metric in ["points", "rebounds", "assists"]:
            rank = self.get_position_rank(opponent_team, player_position, metric)
            analysis["rankings"][metric] = {
                "rank": rank,
                "tier": self._rank_to_tier(rank)
            }
        
        categories = ["pts", "reb", "ast", "stl", "blk", "to"]
        multipliers = []
        
        for category in categories:
            mult = self.get_dvp_multiplier(opponent_team, player_position, category)
            analysis["multipliers"][category] = mult
            multipliers.append(mult)
        
        analysis["overall"] = round(sum(multipliers) / len(multipliers), 3) if multipliers else 1.0
        
        return analysis
    
    def _rank_to_tier(self, rank):
        if rank <= 5:
            return "Muito Favorável"
        elif rank <= 10:
            return "Favorável"
        elif rank <= 20:
            return "Neutro"
        elif rank <= 25:
            return "Desfavorável"
        else:
            return "Muito Desfavorável"

# ============================================================================
# FUNÇÕES DvP (para teses)
# ============================================================================

def tese_dvp_points_matchup(p, game_ctx, opp_ctx):
    dvp_data = p.get("dvp_data", {})
    if not dvp_data:
        return False
    
    points_rank = dvp_data.get("rankings", {}).get("points", {}).get("rank", 15)
    points_tier = dvp_data.get("rankings", {}).get("points", {}).get("tier", "Neutro")
    
    return points_rank <= 10 or points_tier in ["Muito Favorável", "Favorável"]

def tese_dvp_rebound_matchup(p, game_ctx, opp_ctx):
    dvp_data = p.get("dvp_data", {})
    if not dvp_data:
        return False
    
    reb_rank = dvp_data.get("rankings", {}).get("rebounds", {}).get("rank", 15)
    reb_tier = dvp_data.get("rankings", {}).get("rebounds", {}).get("tier", "Neutro")
    
    return (reb_rank <= 10 or reb_tier in ["Muito Favorável", "Favorável"]) and p.get("reb_L5", 0) >= 4

def tese_dvp_assist_matchup(p, game_ctx, opp_ctx):
    dvp_data = p.get("dvp_data", {})
    if not dvp_data:
        return False
    
    ast_rank = dvp_data.get("rankings", {}).get("assists", {}).get("rank", 15)
    ast_tier = dvp_data.get("rankings", {}).get("assists", {}).get("tier", "Neutro")
    
    return (ast_rank <= 10 or ast_tier in ["Muito Favorável", "Favorável"]) and p.get("ast_L5", 0) >= 3