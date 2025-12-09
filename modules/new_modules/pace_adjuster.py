"""
Pace Adjuster Module (FASE 1A)
Ajusta estatísticas baseadas no ritmo do jogo
"""

import pandas as pd
from modules.config import TEAM_PACE_DATA

class PaceAdjuster:
    def __init__(self):
        self.pace_data = TEAM_PACE_DATA
        
    def calculate_game_pace(self, home_team, away_team):
        """Calcula ritmo esperado para o jogo"""
        home_pace = self.pace_data.get(home_team, 100.0)
        away_pace = self.pace_data.get(away_team, 100.0)
        return (home_pace + away_pace) / 2.0
    
    def adjust_player_stats(self, player_stats, home_team, away_team):
        """Aplica ajuste de pace às estatísticas do jogador"""
        if not player_stats or not home_team or not away_team:
            return player_stats
        
        game_pace = self.calculate_game_pace(home_team, away_team)
        pace_factor = game_pace / 100.0
        
        # Criar cópia para não modificar original
        adjusted = player_stats.copy()
        
        # Ajustar stats de volume
        volume_stats = ['pts_L5', 'reb_L5', 'ast_L5', 'pra_L5']
        
        for stat in volume_stats:
            if stat in adjusted and adjusted[stat] > 0:
                adjusted[stat] = round(adjusted[stat] * pace_factor, 1)
        
        # Metadata
        adjusted['pace_adjusted'] = True
        adjusted['game_pace'] = round(game_pace, 1)
        adjusted['pace_factor'] = round(pace_factor, 3)
        
        return adjusted
    
    def adjust_team_context(self, team_context, home_team, away_team):
        """Ajusta contexto do time baseado no pace"""
        if not team_context:
            return team_context
        
        game_pace = self.calculate_game_pace(home_team, away_team)
        
        adjusted = team_context.copy()
        adjusted['game_pace'] = game_pace
        
        # Classificação simples
        if game_pace >= 102:
            adjusted['pace_category'] = 'FAST'
        elif game_pace <= 98:
            adjusted['pace_category'] = 'SLOW'
        else:
            adjusted['pace_category'] = 'AVERAGE'
        
        return adjusted