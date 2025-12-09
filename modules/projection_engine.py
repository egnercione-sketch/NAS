# modules/projection_engine.py
import os
import json
from datetime import datetime
import pandas as pd

# IMPORTAR DO UTILS_FIX (sem problemas de importação circular)
try:
    from modules.utils_fix import load_pickle, save_json, load_json, SafetyUtils
except ImportError:
    # Fallback local
    import pickle
    
    def load_pickle(path):
        try:
            if not os.path.exists(path): return None
            with open(path, "rb") as f: return pickle.load(f)
        except Exception:
            return None
    
    def save_json(path, obj):
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(obj, f, ensure_ascii=False, indent=2)
            return True
        except Exception:
            return False
    
    def load_json(path):
        try:
            if not os.path.exists(path): return None
            with open(path, "r", encoding="utf-8") as f: return json.load(f)
        except Exception:
            return None
    
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

from modules.config import CACHE_DIR, L5_CACHE_FILE

# ============================================================================
# PROJECTION ENGINE
# ============================================================================

class ProjectionEngine:
    """
    Engine de projeções avançadas
    """
    
    def __init__(self, cache_dir=CACHE_DIR):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
        
        self.season_cache_file = os.path.join(cache_dir, "season_stats_cache.json")
        self.projections_cache_file = os.path.join(cache_dir, "projections_cache.json")
        
        self.season_stats = self._load_season_stats()
        self.projections_cache = self._load_projections_cache()
        
        self.safety = SafetyUtils()
        
    def _load_season_stats(self):
        """Carrega stats da temporada do cache"""
        try:
            if os.path.exists(self.season_cache_file):
                with open(self.season_cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception:
            pass
        return {}
    
    def _load_projections_cache(self):
        """Carrega cache de projeções"""
        try:
            if os.path.exists(self.projections_cache_file):
                with open(self.projections_cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                    # Verificar se o cache não está muito antigo (< 6 horas)
                    cache_time = datetime.fromisoformat(cache_data.get("timestamp", "1970-01-01"))
                    if (datetime.now() - cache_time).total_seconds() < 21600:  # 6 horas
                        return cache_data.get("projections", {})
        except Exception:
            pass
        return {}
    
    def _save_projections_cache(self, projections):
        """Salva projeções no cache"""
        try:
            cache_data = {
                "timestamp": datetime.now().isoformat(),
                "projections": projections
            }
            with open(self.projections_cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
        except Exception:
            pass
    
    def _fetch_season_stats_for_player(self, player_id, player_name):
        """
        Busca stats da temporada para um jogador.
        Por enquanto, simula com base nos dados L5.
        """
        saved = load_pickle(L5_CACHE_FILE)
        df_l5 = saved.get("df") if saved and isinstance(saved, dict) else pd.DataFrame()
        
        if df_l5.empty:
            return None
        
        player_data = df_l5[df_l5["PLAYER_ID"] == player_id]
        if player_data.empty:
            player_data = df_l5[df_l5["PLAYER"] == player_name]
        
        if player_data.empty:
            return None
        
        row = player_data.iloc[0].to_dict()
        
        # Simular season stats
        season_stats = {
            "GP": 45,
            "MIN": row.get("MIN_AVG", 25) * 1.1,
            "PTS": row.get("PTS_AVG", 15) * 0.9,
            "REB": row.get("REB_AVG", 5) * 1.05,
            "AST": row.get("AST_AVG", 3) * 1.05,
            "FG3M": row.get("PTS_AVG", 15) * 0.3,
            "STL": 1.2,
            "BLK": 0.8,
            "TOV": 2.0,
            "PRA": row.get("PRA_AVG", 23) * 0.95
        }
        
        return season_stats
    
    def _calculate_base_projection(self, season_stats, recent_stats, weight_season=0.7, weight_recent=0.3):
        """
        Calcula projeção base combinando season stats com recent stats
        """
        if not season_stats and not recent_stats:
            return None
        
        if not season_stats:
            base_stats = recent_stats.copy()
            base_stats["source"] = "recent_only"
        elif not recent_stats:
            base_stats = season_stats.copy()
            base_stats["source"] = "season_only"
        else:
            base_stats = {}
            for stat in ["MIN", "PTS", "REB", "AST", "FG3M", "STL", "BLK", "PRA"]:
                season_val = self.safety.safe_float(season_stats.get(stat, 0))
                recent_val = self.safety.safe_float(recent_stats.get(stat, 0))
                
                if season_val > 0 and recent_val > 0:
                    base_stats[stat] = (season_val * weight_season) + (recent_val * weight_recent)
                elif season_val > 0:
                    base_stats[stat] = season_val
                else:
                    base_stats[stat] = recent_val
            
            base_stats["source"] = f"hybrid_{int(weight_season*100)}_{int(weight_recent*100)}"
        
        return base_stats
    
    def _apply_dvp_adjustments(self, base_projection, opponent_team, player_position, dvp_analyzer):
        """
        Aplica ajustes baseados em Defense vs Position
        """
        if not base_projection or not opponent_team or not player_position or not dvp_analyzer:
            return base_projection
        
        adjusted = base_projection.copy()
        
        dvp_multipliers = {
            "PTS": dvp_analyzer.get_dvp_multiplier(opponent_team, player_position, "points"),
            "REB": dvp_analyzer.get_dvp_multiplier(opponent_team, player_position, "rebounds"),
            "AST": dvp_analyzer.get_dvp_multiplier(opponent_team, player_position, "assists"),
            "FG3M": dvp_analyzer.get_dvp_multiplier(opponent_team, player_position, "points") * 0.95,
            "STL": dvp_analyzer.get_dvp_multiplier(opponent_team, player_position, "assists") * 1.1,
            "BLK": dvp_analyzer.get_dvp_multiplier(opponent_team, player_position, "rebounds") * 1.05
        }
        
        for stat, multiplier in dvp_multipliers.items():
            if stat in adjusted:
                adjusted[stat] *= multiplier
        
        if "PTS" in adjusted and "REB" in adjusted and "AST" in adjusted:
            adjusted["PRA"] = adjusted["PTS"] + adjusted["REB"] + adjusted["AST"]
        
        adjusted["dvp_applied"] = True
        adjusted["dvp_multipliers"] = dvp_multipliers
        
        return adjusted
    
    def _apply_contextual_factors(self, projection, team_context, player_context):
        """
        Aplica fatores contextuais como B2B, travel, injuries
        """
        if not projection:
            return projection
        
        contextual = projection.copy()
        
        b2b_factor = 1.0
        if player_context.get("is_b2b", False):
            if player_context.get("is_veteran", False):
                b2b_factor = 0.85
            elif player_context.get("is_young", False):
                b2b_factor = 0.95
            else:
                b2b_factor = 0.90
        
        travel_factor = 1.0
        timezones = player_context.get("timezones_traveled", 0)
        if timezones >= 3:
            travel_factor = 0.88
        elif timezones >= 2:
            travel_factor = 0.93
        
        injury_factor = 1.0
        team_injuries = player_context.get("team_injuries", 0)
        if team_injuries >= 2:
            if player_context.get("role") in ["star", "starter"]:
                injury_factor = 1.15
            else:
                injury_factor = 1.25
        
        combined_factor = b2b_factor * travel_factor * injury_factor
        
        if "MIN" in contextual:
            contextual["MIN"] *= combined_factor
        
        minute_ratio = combined_factor
        for stat in ["PTS", "REB", "AST", "FG3M", "STL", "BLK"]:
            if stat in contextual:
                contextual[stat] *= minute_ratio
        
        if "PTS" in contextual and "REB" in contextual and "AST" in contextual:
            contextual["PRA"] = contextual["PTS"] + contextual["REB"] + contextual["AST"]
        
        contextual["context_factors"] = {
            "b2b_factor": b2b_factor,
            "travel_factor": travel_factor,
            "injury_factor": injury_factor,
            "combined_factor": combined_factor
        }
        
        return contextual
    
    def _calculate_ceilings(self, projection, volatility=0.3):
        """
        Calcula ceilings (percentis 90, 95, absoluto)
        """
        if not projection:
            return {}
        
        ceilings = {}
        
        volatility_factor = 1.0 + (volatility * 0.5)
        
        stat_configs = {
            "PTS": {"90p": 1.3, "95p": 1.5, "abs": 1.8},
            "REB": {"90p": 1.4, "95p": 1.7, "abs": 2.0},
            "AST": {"90p": 1.4, "95p": 1.6, "abs": 1.9},
            "FG3M": {"90p": 1.5, "95p": 1.8, "abs": 2.2},
            "STL": {"90p": 1.6, "95p": 2.0, "abs": 2.5},
            "BLK": {"90p": 1.6, "95p": 2.0, "abs": 2.5},
            "PRA": {"90p": 1.3, "95p": 1.5, "abs": 1.8}
        }
        
        for stat, config in stat_configs.items():
            base_value = projection.get(stat, 0)
            if base_value > 0:
                for percentile, multiplier in config.items():
                    key = f"{stat}_{percentile}"
                    ceilings[key] = base_value * multiplier * volatility_factor
        
        if "MIN" in projection:
            min_base = projection["MIN"]
            ceilings["MIN_90p"] = min(min_base * 1.25, 48)
            ceilings["MIN_95p"] = min(min_base * 1.35, 48)
            ceilings["MIN_abs"] = min(min_base * 1.5, 48)
        
        return ceilings
    
    def get_player_projection(self, player_id, player_name, team, opponent, position, 
                            player_context=None, dvp_analyzer=None):
        """
        Retorna projeção completa para um jogador
        """
        cache_key = f"{player_id}_{team}_{opponent}"
        if cache_key in self.projections_cache:
            cached_proj = self.projections_cache[cache_key]
            cache_time = datetime.fromisoformat(cached_proj.get("cache_time", "1970-01-01"))
            if (datetime.now() - cache_time).total_seconds() < 7200:
                return cached_proj
        
        season_stats = self.season_stats.get(str(player_id))
        if not season_stats:
            season_stats = self._fetch_season_stats_for_player(player_id, player_name)
            if season_stats:
                self.season_stats[str(player_id)] = season_stats
        
        recent_stats = {}
        if player_context:
            recent_stats = {
                "MIN": player_context.get("min_L5", 0),
                "PTS": player_context.get("pts_L5", 0),
                "REB": player_context.get("reb_L5", 0),
                "AST": player_context.get("ast_L5", 0),
                "PRA": player_context.get("pra_L5", 0)
            }
        
        base_projection = self._calculate_base_projection(season_stats, recent_stats)
        if not base_projection:
            return None
        
        dvp_adjusted = self._apply_dvp_adjustments(base_projection, opponent, position, dvp_analyzer)
        
        contextual_projection = self._apply_contextual_factors(
            dvp_adjusted, 
            {"team": team, "opponent": opponent},
            player_context or {}
        )
        
        volatility = player_context.get("volatility_score", 0.3) if player_context else 0.3
        ceilings = self._calculate_ceilings(contextual_projection, volatility)
        
        final_projection = {
            "player_id": player_id,
            "player_name": player_name,
            "team": team,
            "opponent": opponent,
            "position": position,
            "base_projection": base_projection,
            "dvp_adjusted": dvp_adjusted != base_projection,
            "contextual_projection": contextual_projection,
            "ceilings": ceilings,
            "volatility": volatility,
            "cache_time": datetime.now().isoformat(),
            "projection_time": datetime.now().strftime("%Y-%m-d %H:%M:%S")
        }
        
        for stat in ["MIN", "PTS", "REB", "AST", "FG3M", "STL", "BLK", "PRA"]:
            final_projection[f"{stat}_proj"] = contextual_projection.get(stat, 0)
        
        self.projections_cache[cache_key] = final_projection
        self._save_projections_cache(self.projections_cache)
        
        return final_projection