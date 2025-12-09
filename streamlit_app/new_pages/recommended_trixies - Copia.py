# Adicionar import
from modules.new_modules.correlation_filters import TrixieCorrelationValidator

# Modificar função de geração
def generate_smart_trixies(team_players_ctx, game_ctx):
    """
    Geração inteligente com filtros de correlação
    """
    # Geração normal
    candidate_trixies = build_trixies_for_game_main(team_players_ctx, game_ctx)
    
    # Validator
    validator = TrixieCorrelationValidator()
    enhanced_trixies = []
    
    for trixie in candidate_trixies:
        is_valid, violations, score_adj = validator.validate_trixie(trixie["players"])
        
        if is_valid:
            # Aplicar ajustes
            diversity_score = validator.calculate_trixie_diversity_score(trixie["players"])
            
            enhanced_score = trixie["score"] * score_adj * diversity_score
            
            enhanced_trixies.append({
                **trixie,
                "score": round(enhanced_score, 2),
                "enhanced": True,
                "diversity_score": round(diversity_score, 3),
                "filters_passed": True
            })
        else:
            # Registrar para debug
            trixie["filtered_out"] = True
            trixie["violations"] = violations
    
    # Ordenar por score aprimorado
    enhanced_trixies.sort(key=lambda x: x["score"], reverse=True)
    return enhanced_trixies[:10]