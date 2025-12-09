# Adicionar import
from modules.new_modules.vacuum_matrix import VacuumMatrixAnalyzer

# Modificar método de projeção
class HybridProjectionEngine:
    def __init__(self):
        # ... código existente
        self.vacuum_analyzer = VacuumMatrixAnalyzer()
    
    def enhance_with_contextual_factors(self, projection, player_ctx, game_context):
        """
        Versão aprimorada com Vacuum Matrix
        """
        enhanced = projection.copy()
        
        # 1. Fatores existentes (manter)
        # ...
        
        # 2. Vacuum Matrix (NOVO)
        if hasattr(self, 'vacuum_analyzer') and player_ctx.get("team"):
            # Buscar roster do time (simplificado)
            team_roster = self._get_team_roster(player_ctx["team"])
            if team_roster:
                vacuum_data = self.vacuum_analyzer.analyze_team_vacuum(team_roster, player_ctx["team"])
                if player_ctx.get("name") in vacuum_data:
                    boost_factor = vacuum_data[player_ctx["name"]]["boost"]
                    enhanced["projection"] *= boost_factor
                    enhanced["vacuum_boost"] = boost_factor
        
        return enhanced