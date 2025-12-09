class PlayerClassifier:
    CLASSES = {
        "GLASS_BANGERS": ["C", "PF"],  # Rebotes, garrafão
        "FLOOR_GENERALS": ["PG"],      # Assistências, controle
        "SHOOTERS_LINES": ["SG", "SF"], # Pontos, 3pt
        "ALL_AROUND_STARS": [],        # Estrelas completas (identificar)
        "BENCH_BOMBS": [],             # Upside reserva
        "SAFE_PLAYS": [],              # Baixa volatilidade
        "GARBAGE_KINGS": []            # Especialistas garbage time
    }
    
    def classify_player(self, player_ctx):
        """Classifica jogador em categorias úteis para estratégia"""
        classifications = []
        
        # Glass Banger
        if (player_ctx.get("reb_per_min", 0) > 0.2 and
            player_ctx.get("position") in ["C", "PF"]):
            classifications.append("GLASS_BANGER")
        
        # Floor General  
        if (player_ctx.get("ast_per_min", 0) > 0.15 and
            player_ctx.get("position") in ["PG"]):
            classifications.append("FLOOR_GENERAL")
        
        # ... mais regras
        
        return classifications