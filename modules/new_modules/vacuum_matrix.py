"""
Vacuum Matrix Module (FASE 1B)
Detecta e aplica boost quando jogadores-chave estão ausentes
"""

class VacuumMatrixAnalyzer:
    def __init__(self, injury_monitor=None):
        self.injury_monitor = injury_monitor
        
    def analyze_team_vacuum(self, team_roster, team_abbr):
        """
        Analisa oportunidades de vacuum para um time
        """
        if not team_roster:
            return {}
        
        # Identificar titulares ausentes
        absent_starters = []
        for player in team_roster:
            if player.get("STARTER") and self._is_player_out(player):
                absent_starters.append({
                    "name": player.get("PLAYER"),
                    "position": player.get("POSITION", "").upper()
                })
        
        if not absent_starters:
            return {}
        
        # Mapear substitutos potenciais
        vacuum_opportunities = {}
        
        for starter in absent_starters:
            position = starter["position"]
            
            # Procurar substitutos na mesma posição
            for player in team_roster:
                if (player.get("POSITION", "").upper() == position and 
                    not player.get("STARTER") and 
                    not self._is_player_out(player)):
                    
                    player_name = player.get("PLAYER")
                    if player_name not in vacuum_opportunities:
                        vacuum_opportunities[player_name] = {
                            "reason": f"Substituto de {starter['name']}",
                            "boost": 1.25,  # 25% boost inicial
                            "absent_starter": starter["name"],
                            "position": position
                        }
        
        return vacuum_opportunities
    
    def apply_vacuum_boost(self, player_ctx, vacuum_data):
        """Aplica boost do vacuum matrix ao contexto do jogador"""
        if not player_ctx or not vacuum_data:
            return player_ctx
        
        player_name = player_ctx.get("name")
        if player_name in vacuum_data:
            boost_info = vacuum_data[player_name]
            
            # Aplicar boost aos stats
            stats_to_boost = ['pts_L5', 'reb_L5', 'ast_L5', 'pra_L5']
            for stat in stats_to_boost:
                if stat in player_ctx:
                    player_ctx[stat] = round(player_ctx[stat] * boost_info["boost"], 1)
            
            # Metadata
            player_ctx["vacuum_boost"] = {
                "active": True,
                "boost_factor": boost_info["boost"],
                "reason": boost_info["reason"],
                "replaces": boost_info["absent_starter"]
            }
        
        return player_ctx
    
    def _is_player_out(self, player):
        """Verifica se jogador está fora"""
        status = (player.get("STATUS") or "").lower()
        return any(keyword in status for keyword in ["out", "injured", "ir"])