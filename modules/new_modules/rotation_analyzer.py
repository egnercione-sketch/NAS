# modules/new_modules/rotation_analyzer.py
"""
RotationAnalyzer - Módulo para análise avançada de rotações e formações em quadra
Baseado no mapa lógico fornecido, este módulo processa dados de lineups para gerar
sinais contextuais que enriquecem as recomendações e validação do sistema estratégico.
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any
import json
import logging
import os
from datetime import datetime, timedelta
from collections import defaultdict
import math

logger = logging.getLogger(__name__)

class RotationAnalyzer:
    def __init__(self, cache_dir="cache"):
        """
        Inicializa o analisador de rotações com configurações e cache.
        
        Args:
            cache_dir: Diretório para armazenar caches de análise
        """
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
        self.lineup_cache_file = os.path.join(cache_dir, "lineup_signals.json")
        self.rotation_signals = self._load_cache()
        
        # Configurações ajustáveis
        self.MIN_MINUTES_TOGETHER = 5.0  # minutos mínimos juntos para confiança
        self.MIN_GAMES_SAMPLE = 3  # jogos mínimos para considerar sinal confiável
        self.CONFIDENCE_THRESHOLDS = {
            'high': 0.8,
            'medium': 0.6,
            'low': 0.4
        }
        self.LINEUP_STABILITY_WINDOW = 10  # dias para analisar estabilidade de formações
        
    def _load_cache(self) -> Dict:
        """Carrega sinais de rotação do cache, se disponível."""
        try:
            if os.path.exists(self.lineup_cache_file):
                with open(self.lineup_cache_file, 'r') as f:
                    cache_data = json.load(f)
                    # Verificar se o cache não está muito antigo (menos de 24h)
                    cache_time = datetime.fromisoformat(cache_data.get("timestamp", "1970-01-01"))
                    if (datetime.now() - cache_time).total_seconds() < 86400:  # 24 horas
                        logger.info(f"Cache de lineups carregado com {len(cache_data.get('data', {}))} entradas")
                        return cache_data.get('data', {})
        except Exception as e:
            logger.warning(f"Erro ao carregar cache de lineups: {e}")
        return {}
    
    def _save_cache(self):
        """Salva sinais de rotação no cache."""
        try:
            cache_data = {
                "timestamp": datetime.now().isoformat(),
                "data": self.rotation_signals
            }
            with open(self.lineup_cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
            logger.info("Cache de lineups salvo com sucesso")
        except Exception as e:
            logger.error(f"Erro ao salvar cache de lineups: {e}")
    
    def extract_lineup_snapshots(self, game_data: Dict) -> List[Dict]:
        """
        Extrai snapshots de lineups do play-by-play data.
        
        Args:
            game_data: Dados completos do jogo
            
        Returns:
            Lista de snapshots com dados de minutos, posses, pontos
        """
        pbp_data = game_data.get("play_by_play", [])
        snapshots = []
        
        current_lineup = {
            "home": set(),
            "away": set()
        }
        
        current_period = 1
        last_event_time = None
        
        for event in pbp_data:
            event_type = event.get("event_type")
            period = event.get("period", 1)
            clock = event.get("clock", "12:00")
            
            # Resetar lineup no início de cada período
            if period != current_period:
                current_lineup = {"home": set(), "away": set()}
                current_period = period
            
            # Substituições
            if event_type == "substitution":
                team = event.get("team")
                player_out = event.get("player_out")
                player_in = event.get("player_in")
                
                if team and player_out and player_in:
                    if player_out in current_lineup[team]:
                        current_lineup[team].remove(player_out)
                    current_lineup[team].add(player_in)
            
            # Eventos de pontuação ou posse
            elif event_type in ["shot", "free_throw", "turnover", "rebound"]:
                # Capturar snapshot do lineup atual
                if len(current_lineup["home"]) == 5 and len(current_lineup["away"]) == 5:
                    snapshot = {
                        "timestamp": event.get("timestamp"),
                        "period": period,
                        "clock": clock,
                        "home_lineup": frozenset(current_lineup["home"]),
                        "away_lineup": frozenset(current_lineup["away"]),
                        "event_type": event_type,
                        "team": event.get("team"),
                        "points_scored": event.get("points", 0)
                    }
                    snapshots.append(snapshot)
        
        logger.info(f"Extraídos {len(snapshots)} snapshots de lineup para o jogo")
        return snapshots
    
    def _aggregate_lineup_data(self, snapshots: List[Dict]) -> Dict:
        """
        Agrega dados de snapshots para calcular métricas por lineup.
        
        Args:
            snapshots: Lista de snapshots extraídos
            
        Returns:
            Dicionário com dados agregados por lineup
        """
        lineup_data = defaultdict(lambda: {
            "minutes_together": 0.0,
            "possessions": 0,
            "points_for": 0,
            "points_against": 0,
            "games": set(),
            "players": set()
        })
        
        # Processar snapshots para calcular tempo juntos
        for i in range(len(snapshots) - 1):
            current = snapshots[i]
            next_event = snapshots[i + 1]
            
            # Calcular tempo entre eventos
            time_diff = self._calculate_time_between_events(current, next_event)
            
            # Adicionar minutos para cada lineup
            for team in ["home", "away"]:
                lineup_key = tuple(sorted(current[f"{team}_lineup"]))
                if len(lineup_key) == 5:
                    lineup_data[lineup_key]["minutes_together"] += time_diff
                    lineup_data[lineup_key]["players"].update(lineup_key)
                    lineup_data[lineup_key]["games"].add(current.get("game_id", "unknown"))
            
            # Calcular posses e pontos
            if current.get("event_type") in ["shot", "free_throw", "turnover"]:
                for team in ["home", "away"]:
                    lineup_key = tuple(sorted(current[f"{team}_lineup"]))
                    if len(lineup_key) == 5:
                        lineup_data[lineup_key]["possessions"] += 1
                        # Pontos para o time que fez a cesta
                        if current.get("points", 0) > 0 and current.get("team") == team:
                            lineup_data[lineup_key]["points_for"] += current.get("points", 0)
                        # Pontos contra quando o outro time pontua
                        elif current.get("points", 0) > 0 and current.get("team") != team:
                            lineup_data[lineup_key]["points_against"] += current.get("points", 0)
        
        # Calcular métricas derivadas
        for lineup_key, data in lineup_data.items():
            if data["possessions"] > 0:
                data["points_per_100"] = (data["points_for"] / data["possessions"]) * 100
                data["points_against_per_100"] = (data["points_against"] / data["possessions"]) * 100
                data["net_rating"] = data["points_per_100"] - data["points_against_per_100"]
            
            data["games_count"] = len(data["games"])
            data["cv_minutes"] = self._calculate_cv(data["minutes_together"]) if data["games_count"] > 1 else 1.0
        
        logger.info(f"Agregados dados para {len(lineup_data)} lineups únicos")
        return lineup_data
    
    def _calculate_time_between_events(self, current_event: Dict, next_event: Dict) -> float:
        """
        Calcula o tempo em minutos entre dois eventos do jogo.
        
        Args:
            current_event: Evento atual
            next_event: Próximo evento
            
        Returns:
            Tempo em minutos entre os eventos
        """
        try:
            # Extrair minutos e segundos do clock
            current_clock = current_event.get("clock", "12:00")
            next_clock = next_event.get("clock", "12:00")
            
            current_minutes, current_seconds = map(int, current_clock.split(':'))
            next_minutes, next_seconds = map(int, next_clock.split(':'))
            
            # Calcular diferença em segundos
            current_total_seconds = current_minutes * 60 + current_seconds
            next_total_seconds = next_minutes * 60 + next_seconds
            
            # Se o próximo evento é em período diferente, considerar tempo restante
            if current_event.get("period") != next_event.get("period"):
                time_diff_seconds = current_total_seconds
            else:
                time_diff_seconds = abs(current_total_seconds - next_total_seconds)
            
            # Converter para minutos
            return time_diff_seconds / 60.0
            
        except Exception as e:
            logger.warning(f"Erro ao calcular tempo entre eventos: {e}")
            return 0.0
    
    def _calculate_cv(self, values: float) -> float:
        """
        Calcula o coeficiente de variação (CV) para um valor.
        
        Args:
            values: Valor único ou lista de valores
            
        Returns:
            Coeficiente de variação
        """
        # Para este uso simples, CV é 0 para valores únicos
        return 0.0
    
    def process_game_lineups(self, game_data: Dict) -> Dict:
        """
        Analisa os lineups de um jogo específico e gera sinais de rotação.
        
        Args:
            game_data: Dados do jogo contendo boxscore e play-by-play
            
        Returns:
            Dicionário com sinais de rotação para o jogo
        """
        game_id = game_data.get("game_id")
        home_team = game_data.get("home_team")
        away_team = game_data.get("away_team")
        
        logger.info(f"Analisando lineups para jogo {game_id}: {away_team} @ {home_team}")
        
        # Extrair snapshots de lineups do play-by-play
        lineup_snapshots = self.extract_lineup_snapshots(game_data)
        
        # Agregar dados por lineup
        lineup_aggregates = self._aggregate_lineup_data(lineup_snapshots)
        
        # Gerar sinais de rotação
        rotation_signals = self._generate_rotation_signals(lineup_aggregates, game_data)
        
        # Identificar lineup shocks (mudanças significativas)
        rotation_signals["lineup_shocks"] = self._detect_lineup_shocks(lineup_aggregates, game_data)
        
        # Armazenar no cache
        cache_key = f"{game_id}_{away_team}_{home_team}"
        self.rotation_signals[cache_key] = {
            "timestamp": datetime.now().isoformat(),
            "signals": rotation_signals,
            "game_info": {
                "game_id": game_id,
                "home_team": home_team,
                "away_team": away_team,
                "date": game_data.get("date")
            }
        }
        
        # Atualizar cache
        self._save_cache()
        
        return rotation_signals
    
    def _generate_rotation_signals(self, lineup_aggregates: Dict, game_data: Dict) -> Dict:
        """
        Gera sinais de rotação com base nos dados agregados.
        
        Args:
            lineup_aggregates: Dados agregados por lineup
            game_data: Dados do jogo
            
        Returns:
            Dicionário com sinais de rotação
        """
        signals = {
            "stable_lineups": [],
            "role_definitions": {},
            "minutes_projections": {},
            "ceiling_indicators": {},
            "confidence_scores": {}
        }
        
        home_team = game_data.get("home_team")
        away_team = game_data.get("away_team")
        
        # Processar lineups por time
        for team in [home_team, away_team]:
            team_lineups = [
                (lineup, data) for lineup, data in lineup_aggregates.items()
                if any(player.startswith(f"{team}_") for player in lineup)
            ]
            
            # Identificar lineups estáveis
            stable_lineups = [
                (lineup, data) for lineup, data in team_lineups
                if data["minutes_together"] >= self.MIN_MINUTES_TOGETHER and
                   data["games_count"] >= self.MIN_GAMES_SAMPLE and
                   data["cv_minutes"] <= 0.3
            ]
            
            # Ordenar por minutos juntos
            stable_lineups.sort(key=lambda x: x[1]["minutes_together"], reverse=True)
            
            # Adicionar top 3 lineups estáveis
            for lineup, data in stable_lineups[:3]:
                signals["stable_lineups"].append({
                    "team": team,
                    "lineup": lineup,
                    "minutes_together": data["minutes_together"],
                    "games_count": data["games_count"],
                    "net_rating": data.get("net_rating", 0),
                    "confidence": self._calculate_lineup_confidence(data)
                })
            
            # Definir roles dos jogadores
            self._define_player_roles(team, team_lineups, signals)
            
            # Projetar minutos
            self._project_player_minutes(team, team_lineups, signals)
            
            # Calcular indicadores de teto
            self._calculate_ceiling_indicators(team, team_lineups, signals)
        
        logger.info(f"Gerados sinais de rotação para {home_team} @ {away_team}")
        return signals
    
    def _define_player_roles(self, team: str, team_lineups: List, signals: Dict):
        """
        Define os roles dos jogadores com base nos lineups.
        
        Args:
            team: Time a ser analisado
            team_lineups: Dados dos lineups do time
            signals: Dicionário de sinais a ser atualizado
        """
        player_minutes = defaultdict(float)
        player_starts = defaultdict(int)
        player_games = defaultdict(set)
        
        for lineup, data in team_lineups:
            minutes = data["minutes_together"]
            games = data["games"]
            
            for player in lineup:
                if player.startswith(f"{team}_"):
                    player_minutes[player] += minutes
                    player_games[player].update(games)
                    
                    # Verificar se é starter (presente nos primeiros minutos do 1º quarto)
                    if data.get("first_quarter_start", False):
                        player_starts[player] += 1
        
        # Classificar roles
        for player, minutes in player_minutes.items():
            games_count = len(player_games[player])
            avg_minutes = minutes / max(games_count, 1)
            
            role = "deep_bench"
            if avg_minutes >= 25:
                role = "starter"
            elif avg_minutes >= 18:
                role = "rotation"
            elif avg_minutes >= 12:
                role = "bench"
            
            # Ajustar para jogadores que sempre começam jogos
            if player_starts[player] >= games_count * 0.8 and games_count > 2:
                role = "starter"
            
            signals["role_definitions"][player] = {
                "role": role,
                "avg_minutes": avg_minutes,
                "games_played": games_count,
                "total_minutes": minutes,
                "starter_confidence": player_starts[player] / max(games_count, 1)
            }
    
    def _project_player_minutes(self, team: str, team_lineups: List, signals: Dict):
        """
        Projeta minutos esperados para cada jogador.
        
        Args:
            team: Time a ser analisado
            team_lineups: Dados dos lineups do time
            signals: Dicionário de sinais a ser atualizado
        """
        # Projeção simples baseada no histórico recente
        for player, role_data in signals["role_definitions"].items():
            if not player.startswith(f"{team}_"):
                continue
            
            base_minutes = role_data["avg_minutes"]
            role = role_data["role"]
            
            # Ajustes por role
            if role == "starter":
                projected = max(28, min(36, base_minutes * 1.05))
            elif role == "rotation":
                projected = max(18, min(28, base_minutes * 1.0))
            elif role == "bench":
                projected = max(10, min(18, base_minutes * 0.95))
            else:
                projected = max(5, min(10, base_minutes * 0.9))
            
            signals["minutes_projections"][player] = {
                "projected_minutes": round(projected, 1),
                "base_minutes": base_minutes,
                "role": role,
                "confidence": self.CONFIDENCE_THRESHOLDS["high"] if role in ["starter", "rotation"] else self.CONFIDENCE_THRESHOLDS["medium"]
            }
    
    def _calculate_ceiling_indicators(self, team: str, team_lineups: List, signals: Dict):
        """
        Calcula indicadores de teto estatístico com base nos lineups.
        
        Args:
            team: Time a ser analisado
            team_lineups: Dados dos lineups do time
            signals: Dicionário de sinais a ser atualizado
        """
        # Para cada jogador, analisar seu melhor lineup
        for player, role_data in signals["role_definitions"].items():
            if not player.startswith(f"{team}_"):
                continue
            
            # Encontrar lineups onde o jogador tem melhor performance
            best_lineups = []
            for lineup, data in team_lineups:
                if player in lineup and data["possessions"] > 10:
                    points_per_100 = data.get("points_per_100", 0)
                    if points_per_100 > 0:
                        best_lineups.append((lineup, data))
            
            if best_lineups:
                # Ordenar pelo melhor rating
                best_lineups.sort(key=lambda x: x[1].get("net_rating", 0), reverse=True)
                best_lineup, best_data = best_lineups[0]
                
                # Calcular indicadores de teto
                ceiling_factor = 1.0
                
                # Fator de minutos: lineups com mais minutos juntos
                if best_data["minutes_together"] > 15:
                    ceiling_factor *= 1.15
                elif best_data["minutes_together"] > 10:
                    ceiling_factor *= 1.1
                
                # Fator de performance: lineups com bom rating
                if best_data.get("net_rating", 0) > 5:
                    ceiling_factor *= 1.2
                elif best_data.get("net_rating", 0) > 2:
                    ceiling_factor *= 1.1
                
                # Fator de consistência: baixo CV
                if best_data["cv_minutes"] < 0.2:
                    ceiling_factor *= 1.1
                
                signals["ceiling_indicators"][player] = {
                    "best_lineup": best_lineup,
                    "minutes_together": best_data["minutes_together"],
                    "net_rating": best_data.get("net_rating", 0),
                    "ceiling_factor": round(ceiling_factor, 2),
                    "confidence": self._calculate_lineup_confidence(best_data)
                }
    
    def _calculate_lineup_confidence(self, data: Dict) -> float:
        """
        Calcula score de confiança para um lineup baseado em múltiplos fatores.
        
        Args:
            data: Dados agregados do lineup
            
        Returns:
            Score de confiança entre 0 e 1
        """
        confidence = 0.0
        weight_sum = 0.0
        
        # Fator 1: Minutos juntos (peso 0.4)
        minutes_factor = min(data["minutes_together"] / 20.0, 1.0) if data["minutes_together"] > 0 else 0.0
        confidence += minutes_factor * 0.4
        weight_sum += 0.4
        
        # Fator 2: Número de jogos (peso 0.3)
        games_factor = min(data["games_count"] / 5.0, 1.0) if data["games_count"] > 0 else 0.0
        confidence += games_factor * 0.3
        weight_sum += 0.3
        
        # Fator 3: Consistência (CV) (peso 0.3)
        cv = data["cv_minutes"]
        cv_factor = max(0.0, 1.0 - cv) if cv <= 1.0 else 0.0
        confidence += cv_factor * 0.3
        weight_sum += 0.3
        
        # Normalizar
        return confidence / weight_sum if weight_sum > 0 else 0.0
    
    def _detect_lineup_shocks(self, lineup_aggregates: Dict, game_data: Dict) -> List[Dict]:
        """
        Detecta shocks na rotação (mudanças significativas esperadas).
        
        Args:
            lineup_aggregates: Dados agregados por lineup
            game_data: Dados do jogo
            
        Returns:
            Lista de shocks detectados
        """
        shocks = []
        injuries = game_data.get("injuries", {})
        home_team = game_data.get("home_team")
        away_team = game_data.get("away_team")
        
        # Verificar shocks por lesões
        for team in [home_team, away_team]:
            team_injuries = injuries.get(team, [])
            if team_injuries:
                for injury in team_injuries:
                    injured_player = injury.get("player")
                    position = injury.get("position")
                    
                    if injured_player:
                        shocks.append({
                            "type": "injury_shock",
                            "team": team,
                            "injured_player": injured_player,
                            "position": position,
                            "impact": "high" if position in ["PG", "C"] else "medium",
                            "description": f"Lesão em {injured_player} pode alterar rotação significativamente"
                        })
        
        # Verificar shocks por desempenho recente
        for team in [home_team, away_team]:
            # Analisar últimos jogos para detectar mudanças de rotação
            recent_games = game_data.get("recent_games", {}).get(team, [])
            if len(recent_games) >= 3:
                # Verificar se há jogadores com minutos crescentes
                minutes_trend = defaultdict(list)
                for game in recent_games:
                    for player, stats in game.get("player_stats", {}).items():
                        if player.startswith(f"{team}_"):
                            minutes_trend[player].append(stats.get("minutes", 0))
                
                for player, minutes_list in minutes_trend.items():
                    if len(minutes_list) >= 3:
                        # Calcular tendência
                        trend = (minutes_list[-1] - minutes_list[0]) / max(minutes_list[0], 1)
                        if trend > 0.3:  # Aumento de 30% nos minutos
                            shocks.append({
                                "type": "minutes_shock",
                                "team": team,
                                "player": player,
                                "trend": trend,
                                "impact": "medium",
                                "description": f"{player} com aumento significativo de minutos recentemente"
                            })
        
        logger.info(f"Detectados {len(shocks)} shocks de rotação")
        return shocks
    
    def enhance_player_context(self, player_ctx: Dict, matchup_context: Dict) -> Dict:
        """
        Enriquece o contexto do jogador com sinais de rotação.
        
        Args:
            player_ctx: Contexto do jogador
            matchup_context: Contexto do confronto
            
        Returns:
            Contexto do jogador enriquecido
        """
        player_id = player_ctx.get("player_id")
        team = player_ctx.get("team")
        name = player_ctx.get("name")
        
        # Buscar sinais de rotação para este jogador
        cache_key = matchup_context.get("cache_key")
        if cache_key and cache_key in self.rotation_signals:
            signals = self.rotation_signals[cache_key]["signals"]
            
            # Adicionar role da rotação
            player_key = f"{team}_{name}"
            role_info = signals["role_definitions"].get(player_key)
            if role_info:
                player_ctx["rotation_role"] = role_info["role"]
                player_ctx["rotation_minutes_avg"] = role_info["avg_minutes"]
                player_ctx["rotation_confidence"] = role_info["starter_confidence"] if role_info["role"] == "starter" else 0.7
            
            # Adicionar projeção de minutos
            minutes_proj = signals["minutes_projections"].get(player_key)
            if minutes_proj:
                player_ctx["expected_minutes"] = max(
                    player_ctx.get("expected_minutes", 0),
                    minutes_proj["projected_minutes"]
                )
                player_ctx["rotation_confidence"] = max(
                    player_ctx.get("rotation_confidence", 0),
                    minutes_proj["confidence"]
                )
            
            # Adicionar indicadores de teto
            ceiling_ind = signals["ceiling_indicators"].get(player_key)
            if ceiling_ind:
                player_ctx["lineup_ceiling_factor"] = ceiling_ind["ceiling_factor"]
                player_ctx["best_lineup_minutes"] = ceiling_ind["minutes_together"]
                player_ctx["best_lineup_rating"] = ceiling_ind["net_rating"]
            
            # Verificar lineup shocks
            shocks = signals.get("lineup_shocks", [])
            player_shocks = [
                shock for shock in shocks
                if shock.get("team") == team and
                (shock.get("player") == player_key or
                 shock.get("injured_player") and player_key not in shock.get("injured_player", ""))
            ]
            
            if player_shocks:
                player_ctx["lineup_shocks"] = player_shocks
                player_ctx["lineup_shock_level"] = max(
                    shock.get("impact", "low") for shock in player_shocks
                )
        
        # Fallback se não houver sinais específicos
        if "rotation_role" not in player_ctx:
            self._infer_rotation_role(player_ctx)
        
        return player_ctx
    
    def _infer_rotation_role(self, player_ctx: Dict):
        """
        Infere role de rotação baseado em estatísticas quando não há dados de lineup.
        
        Args:
            player_ctx: Contexto do jogador
        """
        minutes = player_ctx.get("min_L5", 0)
        usage = player_ctx.get("usage", "low")
        starter = player_ctx.get("is_starter", False)
        
        if starter and minutes >= 28:
            role = "starter"
        elif minutes >= 20:
            role = "rotation"
        elif minutes >= 12:
            role = "bench"
        else:
            role = "deep_bench"
        
        player_ctx["rotation_role"] = role
        player_ctx["rotation_confidence"] = 0.6  # Confiança moderada sem dados de lineup
    
    def validate_lineup_compatibility(self, player_ids: List[str], matchup_context: Dict) -> Dict:
        """
        Valida a compatibilidade de jogadores em uma trixie baseado nos lineups.
        
        Args:
            player_ids: Lista de IDs dos jogadores
            matchup_context: Contexto do confronto
            
        Returns:
            Dicionário com resultados de validação
        """
        cache_key = matchup_context.get("cache_key")
        if not cache_key or cache_key not in self.rotation_signals:
            return {
                "compatible": True,
                "score_adjustment": 1.0,
                "reasons": ["Sem dados de lineup para validação"]
            }
        
        signals = self.rotation_signals[cache_key]["signals"]
        validation = {
            "compatible": True,
            "score_adjustment": 1.0,
            "reasons": [],
            "problematic_pairs": []
        }
        
        # Mapear IDs para players
        player_map = {}
        for player_id in player_ids:
            # Encontrar player no contexto (simplificado para este exemplo)
            player_map[player_id] = f"player_{player_id}"
        
        # Verificar pares de jogadores
        for i in range(len(player_ids)):
            for j in range(i + 1, len(player_ids)):
                player1 = player_map[player_ids[i]]
                player2 = player_map[player_ids[j]]
                
                compatibility = self._check_player_pair_compatibility(player1, player2, signals)
                
                if not compatibility["compatible"]:
                    validation["compatible"] = False
                    validation["problematic_pairs"].append((player1, player2))
                    validation["score_adjustment"] *= compatibility["adjustment"]
                    validation["reasons"].append(
                        f"{player1} e {player2}: {compatibility['reason']}"
                    )
        
        # Aplicar bônus por diversidade de times/roles
        if validation["compatible"]:
            diversity_bonus = self._calculate_diversity_bonus(player_ids, signals)
            validation["score_adjustment"] *= diversity_bonus
            if diversity_bonus > 1.0:
                validation["reasons"].append(f"Bônus por diversidade: {diversity_bonus:.2f}x")
        
        return validation
    
    def _check_player_pair_compatibility(self, player1: str, player2: str, signals: Dict) -> Dict:
        """
        Verifica compatibilidade entre dois jogadores baseado nos lineups.
        
        Args:
            player1: Primeiro jogador
            player2: Segundo jogador
            signals: Sinais de rotação
            
        Returns:
            Dicionário com resultado de compatibilidade
        """
        # Verificar se são do mesmo time e posição
        if player1.split('_')[0] == player2.split('_')[0]:  # Mesmo time
            team = player1.split('_')[0]
            
            # Obter posições (simplificado)
            pos1 = self._get_player_position(player1, signals)
            pos2 = self._get_player_position(player2, signals)
            
            # Verificar se são da mesma posição e competem por minutos
            if pos1 == pos2:
                # Verificar histórico de minutos juntos
                minutes_together = self._get_minutes_together(player1, player2, signals)
                if minutes_together < 5.0:  # Pouco tempo juntos
                    return {
                        "compatible": False,
                        "adjustment": 0.6,
                        "reason": f"Competição por minutos na mesma posição ({pos1})"
                    }
        
        # Verificar canibalismo estatístico
        stats1 = self._get_player_stats(player1, signals)
        stats2 = self._get_player_stats(player2, signals)
        
        if stats1 and stats2:
            # Verificar correlação negativa em pontos/rebotes/assistências
            correlation = self._calculate_stat_correlation(stats1, stats2)
            if correlation < -0.3:  # Correlação negativa forte
                return {
                    "compatible": False,
                    "adjustment": 0.7,
                    "reason": "Canibalismo estatístico detectado"
                }
        
        return {
            "compatible": True,
            "adjustment": 1.0,
            "reason": "Jogadores compatíveis"
        }
    
    def _get_player_position(self, player: str, signals: Dict) -> str:
        """Obtém posição do jogador (placeholder para implementação real)"""
        # Em implementação real, buscaria dos dados do jogador
        return "PG"
    
    def _get_minutes_together(self, player1: str, player2: str, signals: Dict) -> float:
        """Calcula minutos que dois jogadores ficaram juntos em quadra"""
        # Placeholder - em implementação real calcularia dos lineups
        return 15.0
    
    def _get_player_stats(self, player: str, signals: Dict) -> Dict:
        """Obtém estatísticas do jogador (placeholder)"""
        return {
            "pts": 15.0,
            "reb": 5.0,
            "ast": 4.0
        }
    
    def _calculate_stat_correlation(self, stats1: Dict, stats2: Dict) -> float:
        """Calcula correlação entre estatísticas de dois jogadores"""
        # Placeholder - implementação simplificada
        return 0.2
    
    def _calculate_diversity_bonus(self, player_ids: List[str], signals: Dict) -> float:
        """
        Calcula bônus por diversidade de times e roles nos jogadores selecionados.
        
        Args:
            player_ids: Lista de IDs dos jogadores
            signals: Sinais de rotação
            
        Returns:
            Fator de bônus (>= 1.0)
        """
        teams = set()
        roles = set()
        
        for player_id in player_ids:
            player = f"player_{player_id}"
            team = player.split('_')[0]
            role = signals["role_definitions"].get(player, {}).get("role", "unknown")
            
            teams.add(team)
            roles.add(role)
        
        bonus = 1.0
        
        # Bônus por diversidade de times
        if len(teams) >= 2:
            bonus *= 1.05
        if len(teams) >= 3:
            bonus *= 1.05
        
        # Bônus por diversidade de roles
        if len(roles) >= 3:
            bonus *= 1.08
        elif len(roles) >= 2:
            bonus *= 1.03
        
        return min(bonus, 1.2)  # Limite máximo de 20% de bônus
    
    def get_lineup_insights(self, team: str, matchup_context: Dict) -> str:
        """
        Gera insights textuais sobre os lineups de um time para exibição na UI.
        
        Args:
            team: Time a ser analisado
            matchup_context: Contexto do confronto
            
        Returns:
            String com insights formatados
        """
        # Gerar cache_key corretamente
        cache_key = matchup_context.get("cache_key")
        if not cache_key:
            away = matchup_context.get("away_team", "")
            home = matchup_context.get("home_team", "")
            game_id = matchup_context.get("gameId", "unknown")
            cache_key = f"{game_id}_{away}_{home}"
            matchup_context["cache_key"] = cache_key
        
        if not cache_key or cache_key not in self.rotation_signals:
            return "Dados de rotação não disponíveis para este jogo."
        
        signals = self.rotation_signals[cache_key]["signals"]
        insights = []
        
        # Lineups estáveis
        team_lineups = [l for l in signals["stable_lineups"] if l["team"] == team]
        if team_lineups:
            insights.append(f"✅ **Formações estáveis identificadas:** {len(team_lineups)} lineups com consistência")
            
            for lineup in team_lineups[:2]:  # Top 2 mais relevantes
                players = ", ".join(lineup["lineup"])
                minutes = lineup["minutes_together"]
                rating = lineup["net_rating"]
                insights.append(f"  • {players}: {minutes:.1f} minutos juntos, rating +{rating:.1f}")
        
        # Roles definidos
        team_roles = {p: r for p, r in signals["role_definitions"].items() if p.startswith(f"{team}_")}
        if team_roles:
            starter_count = sum(1 for r in team_roles.values() if r["role"] == "starter")
            rotation_count = sum(1 for r in team_roles.values() if r["role"] == "rotation")
            insights.append(f"📊 **Roles definidos:** {starter_count} titulares, {rotation_count} rotação")
        
        # Shocks detectados
        shocks = [s for s in signals.get("lineup_shocks", []) if s["team"] == team]
        if shocks:
            insights.append(f"⚠️ **Atenção:** {len(shocks)} shocks de rotação detectados")
            for shock in shocks[:2]:
                insights.append(f"  • {shock['description']}")
        
        return "\n".join(insights) if insights else "Análise de rotação completa disponível."
    
    def prepare_rotation_sidebar(self, matchup_context: Dict) -> Dict:
        """
        Prepara dados para exibição no painel lateral de rotações.
        
        Args:
            matchup_context: Contexto do confronto
            
        Returns:
            Dicionário com dados formatados para UI
        """
        # Gerar cache_key corretamente
        cache_key = matchup_context.get("cache_key")
        if not cache_key:
            away = matchup_context.get("away_team", "")
            home = matchup_context.get("home_team", "")
            game_id = matchup_context.get("gameId", "unknown")
            cache_key = f"{game_id}_{away}_{home}"
            matchup_context["cache_key"] = cache_key
        
        if not cache_key or cache_key not in self.rotation_signals:
            return {
                "status": "no_data",
                "message": "Sem dados de rotação disponíveis"
            }
        
        signals = self.rotation_signals[cache_key]["signals"]
        game_info = self.rotation_signals[cache_key]["game_info"]
        
        home_team = game_info["home_team"]
        away_team = game_info["away_team"]
        
        sidebar_data = {
            "status": "ready",
            "home_team": home_team,
            "away_team": away_team,
            "last_updated": datetime.now().strftime("%H:%M"),
            "home_insights": self.get_lineup_insights(home_team, matchup_context),
            "away_insights": self.get_lineup_insights(away_team, matchup_context),
            "stable_lineups_count": {
                "home": len([l for l in signals["stable_lineups"] if l["team"] == home_team]),
                "away": len([l for l in signals["stable_lineups"] if l["team"] == away_team])
            }
        }
        
        return sidebar_data