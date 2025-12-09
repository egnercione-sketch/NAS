class EnhancedTrixieSystem:
    """
    Sistema unificado com todas as melhorias da FASE 1
    """
    def __init__(self):
        from modules.new_modules.pace_adjuster import PaceAdjuster
        from modules.new_modules.vacuum_matrix import VacuumMatrixAnalyzer
        from modules.new_modules.correlation_filters import TrixieCorrelationValidator
        
        self.pace_adjuster = PaceAdjuster()
        self.vacuum_analyzer = VacuumMatrixAnalyzer()
        self.correlation_validator = TrixieCorrelationValidator()
        
        # Feature flags
        from modules.config import FEATURE_FLAGS
        self.features = FEATURE_FLAGS
    
    def build_enhanced_player_context(self, roster_entry, df_l5_row, 
                                      team_context, opponent_context, 
                                      game_context, dvp_analyzer=None):
        """
        Contexto do jogador com todas as melhorias
        """
        # Contexto básico
        from modules.utils import build_player_ctx
        player_ctx = build_player_ctx(roster_entry, df_l5_row, 
                                      team_context, opponent_context, 
                                      dvp_analyzer)
        
        # 1. Pace Adjuster
        if self.features.get("PACE_ADJUSTER", False):
            player_ctx = self.pace_adjuster.adjust_player_stats(
                player_ctx, 
                game_context.get("home_abbr"), 
                game_context.get("away_abbr")
            )
        
        # 2. Vacuum Matrix
        if self.features.get("VACUUM_MATRIX", False):
            # Analisar roster do time
            team_roster = self._get_team_roster(player_ctx.get("team"))
            if team_roster:
                vacuum_data = self.vacuum_analyzer.analyze_team_vacuum(
                    team_roster, 
                    player_ctx.get("team")
                )
                player_ctx = self.vacuum_analyzer.apply_vacuum_boost(
                    player_ctx, 
                    vacuum_data
                )
        
        return player_ctx
    
    def generate_enhanced_trixies(self, team_players_ctx, game_ctx):
        """
        Gera trixies com todas as melhorias
        """
        # 1. Contextos aprimorados
        enhanced_players = []
        for team, players in team_players_ctx.items():
            for player in players:
                enhanced = self.build_enhanced_player_context(
                    # ... parâmetros
                )
                enhanced_players.append(enhanced)
        
        # 2. Geração tradicional com dados aprimorados
        trixies = self._generate_traditional_trixies(enhanced_players, game_ctx)
        
        # 3. Correlation Filters
        if self.features.get("CORRELATION_FILTERS", False):
            trixies = self._apply_correlation_filters(trixies)
        
        return trixies
    
    def _apply_correlation_filters(self, trixies):
        """Aplica filtros de correlação"""
        filtered = []
        
        for trixie in trixies:
            is_valid, violations, score_adj = self.correlation_validator.validate_trixie(
                trixie["players"]
            )
            
            if is_valid:
                # Bônus por diversidade
                diversity_score = self.correlation_validator.calculate_trixie_diversity_score(
                    trixie["players"]
                )
                
                trixie["score"] *= score_adj * diversity_score
                trixie["diversity_bonus"] = diversity_score
                trixie["enhanced"] = True
                
                filtered.append(trixie)
        
        return sorted(filtered, key=lambda x: x["score"], reverse=True)[:8]