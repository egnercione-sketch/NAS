"""
rotation_ceiling_engine.py

Módulo para calcular probabilidades de teto (ceiling) e avaliar contexto de rotação.
Projetado para ser integrado ao StrategicSystem ou chamado isoladamente.

Classe principal:
- RotationCeilingEngine
"""

from typing import Dict, Any, Tuple
import math

class RotationCeilingEngine:
    # -------------------------
    # Configurações ajustáveis
    # -------------------------
    DEFAULT_PACE_THRESHOLD = 100.0
    DEFAULT_SPREAD_BLOWOUT = 12.0
    MIN_GAMES_HISTORY = 8  # mínimo de jogos para confiar 100% no histórico
    CEILING_BASE_WEIGHT = 0.6  # peso do histórico na probabilidade final
    CONTEXT_WEIGHT = 0.4       # peso do contexto (pace, spread, injuries)
    MIN_PROB = 0.01
    MAX_PROB = 0.99

    # Ajustes por role
    ROLE_MINUTES_THRESHOLDS = {
        "starter": 25,
        "rotation": 18,
        "bench": 12,
        "deep_bench": 0
    }

    # -------------------------
    # Helpers internos
    # -------------------------
    @staticmethod
    def _clamp(v: float, lo: float = MIN_PROB, hi: float = MAX_PROB) -> float:
        return max(lo, min(hi, v))

    @staticmethod
    def _percentile_to_prob(percentile90: float) -> float:
        """
        Converte um valor de percentil histórico (0-1) para probabilidade base.
        Espera percentile90 como fração (ex.: 0.6 significa que o jogador alcança o 90º percentil 60% das vezes historicamente).
        """
        if percentile90 is None:
            return 0.2
        return RotationCeilingEngine._clamp(percentile90)

    @staticmethod
    def _games_confidence(num_games: int) -> float:
        """
        Retorna um multiplicador de confiança baseado no número de jogos históricos disponíveis.
        """
        if num_games >= 30:
            return 1.0
        if num_games >= 15:
            return 0.9
        if num_games >= RotationCeilingEngine.MIN_GAMES_HISTORY:
            return 0.75
        return 0.5

    @staticmethod
    def _adjust_for_pace(base_prob: float, pace: float, stat_type: str) -> float:
        """Ajusta a probabilidade com base no ritmo do jogo."""
        if pace is None:
            return base_prob
        pace_factor = 1.0
        if pace > RotationCeilingEngine.DEFAULT_PACE_THRESHOLD:
            if stat_type in ["pts", "ast", "pra"]:
                pace_factor = 1.0 + (pace - RotationCeilingEngine.DEFAULT_PACE_THRESHOLD) * 0.01
            elif stat_type == "reb":
                pace_factor = 1.0 - (pace - RotationCeilingEngine.DEFAULT_PACE_THRESHOLD) * 0.005
        return base_prob * min(pace_factor, 1.3)

    @staticmethod
    def _adjust_for_blowout(base_prob: float, spread_abs: float, is_losing: bool, stat_type: str) -> float:
        """Ajusta para risco de blowout."""
        if spread_abs is None or spread_abs < RotationCeilingEngine.DEFAULT_SPREAD_BLOWOUT:
            return base_prob
        if is_losing and stat_type in ["pts", "ast", "reb"]:
            # Garbage time pode aumentar minutos para reservas
            return base_prob * 1.2
        elif not is_losing and stat_type in ["pts", "ast"]:
            # Favoritos em blowout podem ver minutos reduzidos
            return base_prob * 0.8
        return base_prob

    @staticmethod
    def _adjust_for_dvp(base_prob: float, dvp_multiplier: float) -> float:
        """Ajusta com base no DvP."""
        if dvp_multiplier is None:
            return base_prob
        return base_prob * dvp_multiplier

    # -------------------------
    # Métodos públicos
    # -------------------------
    @staticmethod
    def calculate_ceiling_probabilities(player_stats: Dict[str, Any], game_ctx: Dict[str, Any]) -> Dict[str, float]:
        """
        Calcula probabilidades de teto para PTS, REB, AST, PRA.

        player_stats deve conter (quando possível):
          - pts_percentile90, reb_percentile90, ast_percentile90, pra_percentile90 (valores 0-1)
          - games_sample (int)
          - recent_trend (dict) opcional com chaves 'pts', 'reb', 'ast', 'pra' com multiplicadores (ex.: 1.1)
          - expected_minutes (float) opcional
          - role (str) opcional

        game_ctx deve conter (quando possível):
          - pace_expected (float)
          - spread_abs (float)
          - is_losing (bool) se o time do jogador está perdendo
          - dvp_adjust (dict) com chaves 'pts','reb','ast','pra' multiplicadores de matchup
          - lineup_shock (bool) se houver mudança de rotação esperada
        """
        # Base histórico
        games_sample = player_stats.get("games_sample", 0)
        confidence_multiplier = RotationCeilingEngine._games_confidence(games_sample)
        
        # Estatísticas base
        stats_config = {
            "pts": player_stats.get("pts_percentile90"),
            "reb": player_stats.get("reb_percentile90"),
            "ast": player_stats.get("ast_percentile90"),
            "pra": player_stats.get("pra_percentile90")
        }
        
        # Contexto do jogo
        pace = game_ctx.get("pace_expected")
        spread_abs = game_ctx.get("spread_abs")
        is_losing = game_ctx.get("is_losing", False)
        dvp_adjust = game_ctx.get("dvp_adjust", {})
        lineup_shock = game_ctx.get("lineup_shock", False)
        
        # Ajuste de linha de base
        recent_trend = player_stats.get("recent_trend", {})
        role = player_stats.get("role", "rotation")
        expected_minutes = player_stats.get("expected_minutes", 0)
        
        # Calcular probabilidades
        ceiling_probs = {}
        
        for stat, base_percentile in stats_config.items():
            # Probabilidade base histórica
            base_prob = RotationCeilingEngine._percentile_to_prob(base_percentile)
            
            # Ajuste por tendência recente
            if stat in recent_trend:
                trend_factor = recent_trend[stat]
                base_prob *= trend_factor
            
            # Ajuste por minutos esperados
            min_threshold = RotationCeilingEngine.ROLE_MINUTES_THRESHOLDS.get(role, 18)
            if expected_minutes < min_threshold:
                base_prob *= 0.7
            elif expected_minutes > min_threshold * 1.2:
                base_prob *= 1.1
            
            # Ajuste contextual
            base_prob = RotationCeilingEngine._adjust_for_pace(base_prob, pace, stat)
            base_prob = RotationCeilingEngine._adjust_for_blowout(base_prob, spread_abs, is_losing, stat)
            base_prob = RotationCeilingEngine._adjust_for_dvp(base_prob, dvp_adjust.get(stat, 1.0))
            
            # Fator de lineup shock (aumenta volatilidade e teto)
            if lineup_shock:
                base_prob *= 1.15
            
            # Aplicar peso histórico vs contexto
            final_prob = (base_prob * RotationCeilingEngine.CEILING_BASE_WEIGHT) + (base_prob * RotationCeilingEngine.CONTEXT_WEIGHT)
            
            # Aplicar confiança baseada em amostra
            final_prob *= confidence_multiplier
            
            # Clamp final
            ceiling_probs[f"prob_ceiling_{stat}"] = RotationCeilingEngine._clamp(final_prob)
        
        return ceiling_probs

    @staticmethod
    def evaluate_rotation_context(player_data: Dict[str, Any], injury_report: Dict, 
                                lineup_info: Dict, team_context: Dict) -> Dict[str, Any]:
        """
        Avalia o contexto de rotação para um jogador.
        
        Args:
            player_data: Dados do jogador
            injury_report: Relatório de lesões do time
            lineup_info: Informações de lineups recentes
            team_context: Contexto do time
            
        Returns:
            Dicionário com contexto de rotação
        """
        player_name = player_data.get("name", "")
        position = player_data.get("position", "")
        team = player_data.get("team", "")
        
        # Verificar lesões na mesma posição
        same_pos_injuries = 0
        if team in injury_report:
            for injured_player in injury_report[team]:
                if injured_player.get("position") == position:
                    same_pos_injuries += 1
        
        # Analisar lineups
        lineup_confidence = 0.0
        expected_minutes_from_lineup = player_data.get("expected_minutes", 0)
        minutes_together = 0
        lineup_shock = False
        
        if lineup_info:
            player_lineups = [l for l in lineup_info.get("stable_lineups", []) 
                             if player_name in l.get("lineup", [])]
            if player_lineups:
                # Usar o lineup mais estável
                best_lineup = max(player_lineups, key=lambda x: x.get("minutes_together", 0))
                minutes_together = best_lineup.get("minutes_together", 0)
                lineup_confidence = best_lineup.get("confidence", 0.5)
                expected_minutes_from_lineup = best_lineup.get("expected_minutes", expected_minutes_from_lineup)
            
            # Verificar lineup shock
            lineup_shocks = lineup_info.get("lineup_shocks", [])
            lineup_shock = any(shock.get("team") == team for shock in lineup_shocks)
        
        # Determinar role baseado em minutos
        role = "deep_bench"
        if expected_minutes_from_lineup >= 25:
            role = "starter"
        elif expected_minutes_from_lineup >= 18:
            role = "rotation"
        elif expected_minutes_from_lineup >= 12:
            role = "bench"
        
        return {
            "rotation_role": role,
            "lineup_confidence": lineup_confidence,
            "expected_minutes": expected_minutes_from_lineup,
            "minutes_together": minutes_together,
            "same_pos_injuries": same_pos_injuries,
            "lineup_shock": lineup_shock,
            "rotation_context": {
                "stable_lineup": len(player_lineups) > 0,
                "role": role,
                "injury_impact": same_pos_injuries > 0,
                "minutes_certainty": min(lineup_confidence, 1.0)
            }
        }