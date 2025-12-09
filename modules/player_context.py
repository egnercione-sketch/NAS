# modules/player_context.py
# -*- coding: utf-8 -*-
"""
Módulo player_context extraído do OficialDeep5.3.py
Contém as funções:
 - build_player_ctx
 - build_player_ctx_super_enhanced

Mantive a lógica idêntica, com proteções mínimas para imports (streamlit, DataEnhancer).
"""

from typing import Dict, Any, Optional
import traceback

# Tentativa de import streamlit (usado no super enhanced)
try:
    import streamlit as st
    _ST_AVAILABLE = True
except Exception:
    st = None
    _ST_AVAILABLE = False

# Tentativa de detectar disponibilidade do DataEnhancer via nome no módulo global (fallback False)
try:
    # quando importado dentro do mesmo processo, o main define DATA_ENHANCER_AVAILABLE
    from modules import teses_engine  # noqa: F401 (apenas tenta garantir import path)
except Exception:
    pass

# Nota: se o ambiente executar o main antes, variáveis como DATA_ENHANCER_AVAILABLE
# podem existir em globals; aqui usamos robustez e checamos st.session_state quando possível.

def derive_availability_and_expected_minutes(roster_entry, df_l5_row, treat_unknown_as_available=True):
    """
    Reimplementação leve de derive_availability_and_expected_minutes caso não exista externamente.
    Mantém comportamento compatível com o main.
    """
    status = (roster_entry.get("STATUS") or "").lower()
    starter = bool(roster_entry.get("STARTER"))
    min_avg = float(df_l5_row.get("MIN_AVG", 0)) if df_l5_row is not None else 0.0
    last_min = float(df_l5_row.get("LAST_MIN", 0)) if df_l5_row is not None else 0.0
    availability = "unknown"; expected_minutes = min_avg
    if any(k in status for k in ("out","ir","injur")):
        availability = "out"; expected_minutes = 0.0
    elif starter:
        availability = "available"; expected_minutes = max(min_avg, last_min, 28.0)
    elif status and any(k in status for k in ("active","available")):
        availability = "available"; expected_minutes = max(min_avg*0.8, last_min*0.9)
    else:
        availability = "probable"; expected_minutes = max(min_avg*0.8, last_min*0.6) if treat_unknown_as_available else min_avg*0.6
    expected_minutes = float(max(0.0, expected_minutes))
    return {"availability": availability, "expected_minutes": expected_minutes}


def build_player_ctx(roster_entry: Dict[str,Any],
                     df_l5_row: Optional[Dict[str,Any]],
                     team_context: Dict[str,Any],
                     opponent_context: Dict[str,Any],
                     dvp_analyzer=None) -> Dict[str,Any]:
    """
    Função idêntica à original — constrói o contexto básico do jogador.
    """
    try:
        name = roster_entry.get("PLAYER", "")
        pos = (roster_entry.get("POSITION", "") or "").upper()
        starter = bool(roster_entry.get("STARTER", False))
        status = (roster_entry.get("STATUS") or "")

        if df_l5_row is None:
            min_L5=min_L10=reb_L5=ast_L5=pts_L5=pra_L5=reb_per_min=ast_per_min=0.0
            reb_cv=ast_cv=pts_cv=min_cv=1.0; exp=99
        else:
            min_L5 = float(df_l5_row.get("MIN_AVG", 0.0)); min_L10 = min_L5
            reb_L5 = float(df_l5_row.get("REB_AVG", 0.0)); ast_L5 = float(df_l5_row.get("AST_AVG", 0.0))
            pts_L5 = float(df_l5_row.get("PTS_AVG", 0.0))
            pra_L5 = float(df_l5_row.get("PRA_AVG", pts_L5+reb_L5+ast_L5))
            reb_per_min = reb_L5/min_L5 if min_L5>0 else 0.0
            ast_per_min = ast_L5/min_L5 if min_L5>0 else 0.0
            reb_cv = float(df_l5_row.get("REB_CV", 1.0)); ast_cv = float(df_l5_row.get("AST_CV", 1.0))
            pts_cv = float(df_l5_row.get("PTS_CV", 1.0)); min_cv = float(df_l5_row.get("MIN_CV", 1.0))
            exp = int(df_l5_row.get("EXP", 99))

        derived = derive_availability_and_expected_minutes(roster_entry, df_l5_row, treat_unknown_as_available=True)
        expected_minutes = derived.get("expected_minutes", 0.0)
        is_young = exp <= 3; is_veteran = exp >= 8
        usage = "high" if pra_L5>=30 else ("medium" if pra_L5>=18 else "low")
        vol_score = (pts_cv + min_cv)/2.0
        volatility = "high" if vol_score>=0.8 else ("medium" if vol_score>=0.5 else "low")

        if starter and usage=="high":
            role="star"
        elif starter and usage!="low":
            role="starter"
        elif not starter and usage=="high":
            role="bench_scorer"
        elif not starter and usage=="medium":
            role="rotation"
        else:
            role="deep_bench"

        if reb_per_min>=0.22 and pts_L5<16:
            style="rebounder"
        elif ast_per_min>=0.18:
            style="playmaker"
        elif pts_L5>=18:
            style="scorer"
        elif reb_per_min>=0.18 and pts_L5>=12:
            style="hustle"
        else:
            style="role"

        garbage_profile = "high" if ((not starter) and is_young and volatility!="low") else ("medium" if ((not starter) and volatility=="medium") else "low")

        dvp_data = {}
        if dvp_analyzer and opponent_context.get("opponent_team"):
            try:
                dvp_data = dvp_analyzer.get_matchup_analysis(
                    opponent_context.get("opponent_team"),
                    pos
                )
            except Exception:
                dvp_data = {}

        return {
            "player_id": int(df_l5_row.get("PLAYER_ID")) if df_l5_row and df_l5_row.get("PLAYER_ID") is not None else None,
            "name": name, "team": team_context.get("team_abbr"), "position": pos,
            "is_starter": starter, "status": status,
            "min_L3": min_L5, "min_L5": min_L5, "min_L10": min_L10, "expected_minutes": expected_minutes,
            "pts_L5": pts_L5, "reb_L5": reb_L5, "ast_L5": ast_L5, "pra_L5": pra_L5,
            "reb_per_min": reb_per_min, "ast_per_min": ast_per_min,
            "reb_cv": reb_cv, "ast_cv": ast_cv, "pts_cv": pts_cv, "min_cv": min_cv, "exp": exp,
            "team_injuries": team_context.get("team_injuries", 0),
            "spread": float(team_context.get("spread") or 0.0),
            "is_underdog": team_context.get("is_underdog", False),
            "is_b2b": team_context.get("is_b2b", False),
            "pace_expected": team_context.get("pace_expected", None),
            "opponent_reb_rank": opponent_context.get("opponent_reb_rank", 0),
            "opponent_ast_rank": opponent_context.get("opponent_ast_rank", 0),
            "games_last_6": team_context.get("games_last_6", 0),
            "timezones_traveled": team_context.get("timezones_traveled", 0),
            "garbage_rate_L10": team_context.get("garbage_rate_L10", 0.0),
            "is_young": is_young, "is_veteran": is_veteran, "usage": usage,
            "volatility": volatility, "role": role, "style": style, "garbage_time_profile": garbage_profile,
            "dvp_data": dvp_data
        }
    except Exception:
        # Em caso de erro inesperado retornamos um contexto mínimo para evitar que o pipeline quebre
        try:
            return {
                "player_id": None,
                "name": roster_entry.get("PLAYER", ""),
                "team": team_context.get("team_abbr"),
                "position": (roster_entry.get("POSITION", "") or "").upper(),
                "is_starter": bool(roster_entry.get("STARTER", False)),
                "status": roster_entry.get("STATUS", ""),
                "min_L5": 0, "pts_L5": 0, "reb_L5": 0, "ast_L5": 0,
                "pra_L5": 0, "expected_minutes": 0
            }
        except Exception:
            return {}


def build_player_ctx_super_enhanced(roster_entry: Dict[str,Any],
                                    df_l5_row: Optional[Dict[str,Any]],
                                    team_context: Dict[str,Any],
                                    opponent_context: Dict[str,Any],
                                    dvp_analyzer=None,
                                    projection_engine=None) -> Dict[str,Any]:
    """
    Versão SUPER aprimorada com todos os novos módulos.
    Mantém comportamento idêntico ao main; tenta usar DataEnhancer via st.session_state se disponível.
    """
    basic_ctx = build_player_ctx(roster_entry, df_l5_row, team_context, opponent_context, dvp_analyzer)

    # Usar DataEnhancer se disponível no session_state (compatível com como o main usava)
    try:
        data_enhancer_available = False
        if _ST_AVAILABLE and hasattr(st, "session_state"):
            data_enhancer_available = bool(st.session_state.get("data_enhancer"))
        # Se data_enhancer estiver disponível na sessão, executar o enhancement
        if data_enhancer_available:
            try:
                basic_ctx = st.session_state.data_enhancer.enhance_player_stats(basic_ctx)
            except Exception as e:
                basic_ctx["enhancement_error"] = str(e)
    except Exception:
        # Se streamlit não existir ou outro erro, apenas ignorar
        pass

    # Usar ProjectionEngine se disponível (passado explicitamente)
    if projection_engine and basic_ctx.get("player_id"):
        try:
            proj = projection_engine.get_player_projection(
                player_id=basic_ctx.get("player_id"),
                player_name=basic_ctx.get("name"),
                team=basic_ctx.get("team"),
                opponent=opponent_context.get("opponent_team"),
                position=basic_ctx.get("position"),
                player_context=basic_ctx,
                dvp_analyzer=dvp_analyzer
            )

            if proj:
                basic_ctx["proj_engine_used"] = True
                basic_ctx["proj_min"] = proj.get("MIN_proj", basic_ctx.get("min_L5", 0))
                basic_ctx["proj_pts"] = proj.get("PTS_proj", basic_ctx.get("pts_L5", 0))
                basic_ctx["proj_reb"] = proj.get("REB_proj", basic_ctx.get("reb_L5", 0))
                basic_ctx["proj_ast"] = proj.get("AST_proj", basic_ctx.get("ast_L5", 0))
                basic_ctx["proj_pra"] = proj.get("PRA_proj", basic_ctx.get("pra_L5", 0))

                ceilings = proj.get("ceilings", {})
                basic_ctx["prob_90p_pts"] = ceilings.get("PTS_90p_prob", 50)
                basic_ctx["prob_95p_pts"] = ceilings.get("PTS_95p_prob", 30)
                basic_ctx["prob_90p_reb"] = ceilings.get("REB_90p_prob", 50)
                basic_ctx["prob_95p_reb"] = ceilings.get("REB_95p_prob", 30)
                basic_ctx["prob_90p_ast"] = ceilings.get("AST_90p_prob", 50)
                basic_ctx["prob_95p_ast"] = ceilings.get("AST_95p_prob", 30)

                basic_ctx["proj_metadata"] = {
                    "projection_time": proj.get("projection_time"),
                    "dvp_applied": proj.get("dvp_adjusted", False),
                    "context_factors": proj.get("contextual_projection", {}).get("context_factors", {})
                }
        except Exception as e:
            basic_ctx["proj_engine_error"] = str(e)
            basic_ctx["proj_engine_]()_
