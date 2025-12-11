"""
CONFIGURAÇÃO DAS ESTRATÉGIAS PARA TRIXIES
Define regras, pesos e critérios para as 4 categorias estratégicas
"""

STRATEGY_CONFIG = {
    "conservadora": {
        "nome": "🛡️ Conservadora (Safe Play)",
        "descricao": "Titulares com baixa volatilidade, DvP favorável, linhas padrão",
        "critérios": {
            "min_confidence": 0.7,
            "max_players_per_team": 2,
            "required_role": ["starter", "rotation"],
            "preferred_markets": ["PTS", "REB", "AST"],
            "max_volatility": 0.3,
            "min_minutes": 25,
            "max_spread_tolerance": 12
        },
        "pesos": {
            "dvp_favoravel": 1.3,
            "role_starter": 1.2,
            "consistency": 1.4,
            "low_volatility": 1.25,
            "pace_neutral": 1.1
        },
        "regras_exclusao": [
            "BlowoutRisk",
            "InjuryRisk"
        ]
    },
    
    "ousada": {
        "nome": "🎯 Ousada (Upside Play)",
        "descricao": "PRA ou combos para jogadores com múltiplas teses e contexto favorável",
        "critérios": {
            "min_confidence": 0.6,
            "max_players_per_team": 2,
            "required_role": ["starter", "rotation"],
            "preferred_markets": ["PRA", "REB+AST", "PTS+REB", "PTS+AST"],
            "min_upside_score": 1.5,
            "min_theses_count": 2,
            "pace_preference": "high"
        },
        "pesos": {
            "multi_theses": 1.4,
            "high_pace": 1.3,
            "clutch_performer": 1.25,
            "upside_potential": 1.5,
            "close_game": 1.3
        },
        "regras_exclusao": [
            "LowUsage",
            "BlowoutRisk"
        ]
    },
    
    "banco": {
        "nome": "💰 Banco (Value Hunter)",
        "descricao": "Reservas com PRA/min alto e minutos ascendentes ou garbage time",
        "critérios": {
            "min_confidence": 0.5,
            "max_players_per_team": 1,
            "required_role": ["bench", "rotation"],
            "preferred_markets": ["PRA", "PTS", "REB"],
            "min_pra_per_min": 0.8,
            "max_minutes": 28,
            "min_expected_minutes_increase": 0.1,
            "blowout_tolerance": "high"
        },
        "pesos": {
            "value_score": 1.6,
            "garbage_time": 1.4,
            "minutes_trend": 1.3,
            "efficiency": 1.25,
            "bench_role": 1.2
        },
        "regras_exclusao": [
            "StarterCompetition",
            "LowEfficiency"
        ]
    },
    
    "explosao": {
        "nome": "⚡ Explosão (Boost Play)",
        "descricao": "Mercado específico ativado por contexto situacional único",
        "critérios": {
            "min_confidence": 0.55,
            "max_players_per_team": 1,
            "required_role": ["starter", "rotation", "bench"],
            "preferred_markets": ["AST", "3PTM", "BLK", "STL"],
            "situational_boost_required": True,
            "min_pace_boost": 1.1,
            "max_spread_tolerance": 8
        },
        "pesos": {
            "situational_boost": 1.7,
            "high_pace": 1.4,
            "defensive_matchup": 1.3,
            "clutch_context": 1.35,
            "unique_factor": 1.5
        },
        "regras_exclusao": [
            "NeutralContext",
            "LowVolume"
        ]
    }
}

# Estratégias identificáveis
STRATEGY_IDENTIFIERS = {
    "GLASS_BANGERS_TRIO": {
        "descricao": "Big men com foco em rebotes e defesa",
        "categorias": ["conservadora", "ousada"],
        "required_archetypes": ["GLASS_BANGER", "PAINT_BEAST"],
        "min_players": 2,
        "max_players": 3
    },
    "THE_BATTERY": {
        "descricao": "Armador principal + scorer secundário do mesmo time",
        "categorias": ["ousada", "explosao"],
        "required_roles": ["starter", "starter"],
        "preferred_markets": ["AST", "PTS"]
    },
    "SHOOTOUT_PAIR": {
        "descricao": "Scorers de times opostos em jogo de alto pace",
        "categorias": ["explosao", "ousada"],
        "required_conditions": ["high_pace", "close_spread"],
        "team_diversity": True
    },
    "BLOWOUT_SPECIAL": {
        "descricao": "Reservas que se beneficiam de garbage time",
        "categorias": ["banco"],
        "required_conditions": ["high_spread", "bench_role"],
        "preferred_markets": ["PRA", "PTS"]
    },
    "PACE_PUSHERS": {
        "descricao": "Jogadores que se beneficiam de ritmo acelerado",
        "categorias": ["explosao", "ousada"],
        "required_stats": ["pace_advantage"],
        "min_pace_boost": 1.15
    },
    "CLUTCH_PERFORMERS": {
        "descricao": "Jogadores com histórico em finais apertados",
        "categorias": ["conservadora", "ousada"],
        "required_metrics": ["clutch_performance"],
        "preferred_context": ["close_game", "high_stakes"]
    }
}

# Multiplicadores por archetype
ARCHETYPE_MULTIPLIERS = {
    "GLASS_BANGER": {"REB": 1.3, "PTS": 1.1, "AST": 0.9},
    "FLOOR_GENERAL": {"AST": 1.4, "PTS": 1.1, "REB": 0.9},
    "SHARPSHOOTER": {"PTS": 1.35, "3PTM": 1.5, "AST": 1.0},
    "ALL_AROUND": {"PRA": 1.4, "PTS": 1.2, "REB": 1.2, "AST": 1.2},
    "BENCH_SPARK": {"PRA": 1.3, "PTS": 1.25, "per_minute": 1.4},
    "DEFENSIVE_ANCHOR": {"REB": 1.25, "BLK": 1.5, "STL": 1.3},
    "PAINT_BEAST": {"PTS": 1.2, "REB": 1.35, "BLK": 1.4},
    "CLUTCH_PERFORMER": {"PTS": 1.4, "AST": 1.3, "fourth_quarter": 1.5}
}

# Regras de validação e penalizações
VALIDATION_RULES = {
    "critical_violations": {
        "same_team_trio": {"penalty": 0.5, "message": "3+ jogadores do mesmo time"},
        "position_cannibalism": {"penalty": 0.4, "message": "PG+PG ou C+C no mesmo time"},
        "blowout_risk_high": {"penalty": 0.6, "message": "Spread muito alto (>15)"},
        "injury_risk": {"penalty": 0.7, "message": "Jogador com risco de lesão"}
    },
    "soft_violations": {
        "low_diversity": {"penalty": 0.1, "message": "Baixa diversidade de teses"},
        "market_overlap": {"penalty": 0.15, "message": "Mercados muito similares"},
        "role_concentration": {"penalty": 0.2, "message": "Muitos jogadores com mesma role"}
    },
    "bonus_factors": {
        "team_diversity": {"bonus": 0.15, "message": "Boa diversidade de times"},
        "market_diversity": {"bonus": 0.2, "message": "Mercados diversificados"},
        "role_diversity": {"bonus": 0.1, "message": "Roles diversificadas"},
        "thesis_variety": {"bonus": 0.25, "message": "Variedade de teses reforçadas"}
    }
}

# Fallbacks para dados ausentes
FALLBACK_VALUES = {
    "missing_usg": 20.0,
    "missing_dvp": 0.0,
    "missing_pace": 100.0,
    "missing_minutes": 24.0,
    "default_confidence": 0.5
}