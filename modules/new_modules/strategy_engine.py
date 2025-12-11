# modules/new_modules/strategy_engine.py
"""
Strategy Engine - Composição de Recomendações Estratégicas
Transforma teses em 4 categorias distintas: Conservadora, Ousada, Banco, Explosão
Garante diversidade e não repetição de jogadores
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from collections import defaultdict
import random

class StrategyEngine:
    """
    Engine que compõe recomendações estratégicas baseadas em teses
    Categorias: Conservadora (Safe), Ousada (Upside), Banco (Value), Explosão (Boost)
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """Inicializa o motor estratégico"""
        self.config = config or {}
        
        # Configurações por categoria
        self.category_configs = {
            'conservadora': {
                'min_confidence': 0.65,
                'max_players': 4,
                'allowed_markets': ['PTS', 'REB'],
                'allowed_roles': ['starter'],
                'priority_theses': ['BigRebound', 'ScorerLine'],
                'description': 'Safe Play - Aposta conservadora com baixa volatilidade',
                'color': '🟢'
            },
            'ousada': {
                'min_confidence': 0.6,
                'max_players': 3,
                'allowed_markets': ['PRA', 'REB+AST', 'PTS+REB'],
                'allowed_roles': ['starter', 'rotation'],
                'priority_theses': ['AssistMatchup', 'PaceBoost'],
                'description': 'Upside Play - Maior risco, maior retorno potencial',
                'color': '🟡'
            },
            'banco': {
                'min_confidence': 0.55,
                'max_players': 3,
                'allowed_markets': ['PRA', 'PTS', 'REB'],
                'allowed_roles': ['bench', 'rotation'],
                'priority_theses': ['ValueHunter'],
                'description': 'Value Play - Aposta no banco com bom custo-benefício',
                'color': '🔵'
            },
            'explosao': {
                'min_confidence': 0.6,
                'max_players': 2,
                'allowed_markets': ['AST', 'PTS', 'REB'],
                'allowed_roles': ['starter', 'rotation', 'bench'],
                'priority_theses': ['PaceBoost', 'AssistMatchup', 'ScorerLine'],
                'description': 'Boost Play - Situações específicas de alto potencial',
                'color': '🟠'
            }
        }
        
        # Estratégias identificáveis (para usar com strategy_identifier)
        self.strategy_templates = {
            'GLASS_BANGERS_TRIO': {
                'description': 'Tripla de jogadores dominantes no garrafão',
                'required_players': 3,
                'required_positions': ['C', 'PF', 'C/PF'],
                'market_focus': 'REB'
            },
            'THE_BATTERY': {
                'description': 'Armador + Scorer do mesmo time',
                'required_players': 2,
                'required_positions': [['PG', 'SG'], ['PG', 'SF']],
                'market_focus': 'AST/PTS'
            },
            'BENCH_MOB': {
                'description': 'Reservas com alto upside em garbage time',
                'required_players': 2,
                'required_roles': ['bench', 'rotation'],
                'market_focus': 'PRA'
            },
            'SHOOTOUT_PAIR': {
                'description': 'Scorers de times opostos em jogo rápido',
                'required_players': 2,
                'required_teams': 'different',
                'market_focus': 'PTS'
            },
            'BLOWOUT_SPECIAL': {
                'description': 'Jogadores beneficiados por blowout/garbage time',
                'required_players': 2,
                'required_context': 'high_spread',
                'market_focus': 'PRA'
            }
        }
        
        # Controle de diversidade
        self.used_players = set()
        self.used_teams = defaultdict(int)
        self.used_markets = defaultdict(int)
        
    def reset_selection(self):
        """Reseta o controle de seleção para nova composição"""
        self.used_players.clear()
        self.used_teams.clear()
        self.used_markets.clear()
    
    def categorize_theses(self, all_theses: Dict[str, List[Dict]], game_ctx: Dict) -> Dict[str, List[Dict]]:
        """
        Categoriza teses por tipo estratégico
        """
        categorized = {
            'conservadora_candidates': [],
            'ousada_candidates': [],
            'banco_candidates': [],
            'explosao_candidates': []
        }
        
        for player_name, player_theses in all_theses.items():
            player_team = None
            player_role = None
            
            for thesis in player_theses:
                # Pula teses de risco
                if thesis.get('thesis_type') == 'BlowoutRisk':
                    continue
                
                # Extrai contexto do jogador
                player_ctx = thesis.get('player_ctx', {})
                player_team = player_ctx.get('team', '')
                player_role = player_ctx.get('role', '')
                
                # Determina categoria com base em múltiplos fatores
                category = self._determine_category(thesis, player_ctx, game_ctx)
                
                if category:
                    # Adiciona contexto adicional
                    enhanced_thesis = thesis.copy()
                    enhanced_thesis['category'] = category
                    enhanced_thesis['player_team'] = player_team
                    enhanced_thesis['player_role'] = player_role
                    
                    categorized[f'{category}_candidates'].append(enhanced_thesis)
        
        return categorized
    
    def _determine_category(self, thesis: Dict, player_ctx: Dict, game_ctx: Dict) -> Optional[str]:
        """
        Determina a categoria estratégica para uma tese
        """
        thesis_type = thesis.get('thesis_type', '')
        market = thesis.get('market', '')
        confidence = thesis.get('confidence', 0)
        role = player_ctx.get('role', '')
        
        # 1. Conservadora (Safe)
        if (confidence >= 0.65 and role == 'starter' and 
            market in ['PTS', 'REB'] and
            thesis_type in ['BigRebound', 'ScorerLine']):
            return 'conservadora'
        
        # 2. Ousada (Upside)
        elif (confidence >= 0.6 and role in ['starter', 'rotation'] and
              market in ['PRA', 'REB+AST', 'PTS+REB'] and
              thesis_type in ['AssistMatchup', 'PaceBoost']):
            return 'ousada'
        
        # 3. Banco (Value)
        elif (confidence >= 0.55 and role in ['bench', 'rotation'] and
              thesis_type == 'ValueHunter'):
            return 'banco'
        
        # 4. Explosão (Boost)
        elif (confidence >= 0.6 and 
              thesis_type in ['PaceBoost', 'AssistMatchup']):
            return 'explosao'
        
        # Fallback baseado em confiança e role
        if confidence >= 0.7:
            if role == 'starter':
                return 'conservadora'
            elif role in ['rotation', 'bench']:
                return 'banco'
        
        return None
    
    def select_for_category(self, candidates: List[Dict], category: str, 
                          game_ctx: Dict, num_selections: int = 1) -> List[Dict]:
        """
        Seleciona as melhores teses para uma categoria específica
        """
        config = self.category_configs[category]
        
        # Filtra candidatos elegíveis
        filtered = []
        for thesis in candidates:
            # Verifica jogador já utilizado
            if thesis['player'] in self.used_players:
                continue
            
            # Verifica confiança mínima
            if thesis['confidence'] < config['min_confidence']:
                continue
            
            # Verifica role permitida
            if config['allowed_roles'] and thesis.get('player_role', '') not in config['allowed_roles']:
                continue
            
            # Verifica mercado permitido
            if config['allowed_markets'] and thesis['market'] not in config['allowed_markets']:
                continue
            
            # Prioriza teses preferidas da categoria
            priority_boost = 1.2 if thesis['thesis_type'] in config['priority_theses'] else 1.0
            
            filtered.append((thesis, priority_boost))
        
        if not filtered:
            return []
        
        # Ordena por confiança ajustada
        sorted_candidates = sorted(
            filtered, 
            key=lambda x: x[0]['confidence'] * x[1], 
            reverse=True
        )
        
        # Seleciona os melhores
        selected = []
        for thesis, _ in sorted_candidates[:num_selections]:
            # Marca jogador como utilizado
            self.used_players.add(thesis['player'])
            self.used_teams[thesis.get('player_team', '')] += 1
            self.used_markets[thesis['market']] += 1
            
            # Adiciona metadados da categoria
            enhanced = thesis.copy()
            enhanced['strategy_category'] = category
            enhanced['category_config'] = config
            enhanced['selection_score'] = thesis['confidence'] * priority_boost
            
            selected.append(enhanced)
        
        return selected
    
    def identify_strategy(self, recommendations: List[Dict], game_ctx: Dict) -> str:
        """
        Identifica o tipo de estratégia baseado nas recomendações
        """
        if len(recommendations) == 0:
            return "INDIVIDUAL_PLAY"
        
        players = [r['player'] for r in recommendations]
        markets = [r['market'] for r in recommendations]
        teams = [r.get('player_team', '') for r in recommendations]
        
        # Verifica Glass Bangers (múltiplos big men)
        if len(recommendations) >= 2:
            big_men_count = sum(1 for r in recommendations 
                              if r.get('player_position', '') in ['C', 'PF'] and 
                                 r['market'] == 'REB')
            if big_men_count >= 2:
                return "GLASS_BANGERS_TRIO" if big_men_count >= 3 else "GLASS_BANGER_PAIR"
        
        # Verifica The Battery (armador + scorer)
        if len(recommendations) == 2:
            positions = [r.get('player_position', '') for r in recommendations]
            if ('PG' in positions and any(p in ['SG', 'SF'] for p in positions)):
                if len(set(teams)) == 1:  # Mesmo time
                    return "THE_BATTERY"
        
        # Verifica Bench Mob
        roles = [r.get('player_role', '') for r in recommendations]
        if all(role in ['bench', 'rotation'] for role in roles):
            return "BENCH_MOB"
        
        # Verifica Shootout Pair
        if len(recommendations) == 2 and len(set(teams)) == 2:
            if all(market == 'PTS' for market in markets):
                pace = game_ctx.get('pace', 0)
                if pace > 100:
                    return "SHOOTOUT_PAIR"
        
        # Verifica Blowout Special
        spread = abs(game_ctx.get('spread', 0))
        if spread > 12:
            if any(r.get('thesis_type') == 'ValueHunter' for r in recommendations):
                return "BLOWOUT_SPECIAL"
        
        return "CURATED_COMBO"
    
    def apply_correlation_adjustments(self, recommendation: Dict, game_ctx: Dict) -> Dict:
        """
        Aplica ajustes de correlação ao score
        """
        adjustments = []
        score_adjustment = 0
        
        player_team = recommendation.get('player_team', '')
        market = recommendation['market']
        
        # Penalizações
        # 1. Muitos jogadores do mesmo time
        if self.used_teams[player_team] > 2:
            penalty = -0.15
            adjustments.append(f"Penalidade: -15% (muitos jogadores do {player_team})")
            score_adjustment += penalty
        
        # 2. Muitos mercados iguais
        if self.used_markets[market] > 2:
            penalty = -0.1
            adjustments.append(f"Penalidade: -10% (excesso de {market})")
            score_adjustment += penalty
        
        # 3. Spread alto para starters
        spread = abs(game_ctx.get('spread', 0))
        if spread > 10 and recommendation.get('player_role') == 'starter':
            penalty = -0.1
            adjustments.append(f"Penalidade: -10% (starter em jogo com spread alto)")
            score_adjustment += penalty
        
        # Bônus
        # 1. Diversidade de times
        unique_teams = len(self.used_teams)
        if unique_teams >= 3:
            bonus = 0.1
            adjustments.append(f"Bônus: +10% (diversidade de times: {unique_teams})")
            score_adjustment += bonus
        
        # 2. Diversidade de mercados
        unique_markets = len(self.used_markets)
        if unique_markets >= 3:
            bonus = 0.08
            adjustments.append(f"Bônus: +8% (diversidade de mercados: {unique_markets})")
            score_adjustment += bonus
        
        # 3. Jogo parelho para volume players
        if spread <= 5 and market == 'PTS':
            bonus = 0.05
            adjustments.append(f"Bônus: +5% (jogo parelho bom para volume)")
            score_adjustment += bonus
        
        # Aplica ajuste (limita entre -0.3 e +0.3)
        score_adjustment = max(min(score_adjustment, 0.3), -0.3)
        
        # Atualiza score
        original_confidence = recommendation['confidence']
        adjusted_confidence = original_confidence * (1 + score_adjustment)
        adjusted_confidence = min(max(adjusted_confidence, 0), 1)
        
        enhanced = recommendation.copy()
        enhanced['adjusted_confidence'] = round(adjusted_confidence, 3)
        enhanced['score_adjustment'] = round(score_adjustment, 3)
        enhanced['adjustments'] = adjustments
        
        return enhanced
    
    def compose_recommendations(self, all_theses: Dict[str, List[Dict]], 
                              game_ctx: Dict) -> Dict[str, List[Dict]]:
        """
        Compõe as 4 recomendações estratégicas
        """
        # Reseta seleção
        self.reset_selection()
        
        # Categoriza teses
        categorized = self.categorize_theses(all_theses, game_ctx)
        
        # Composição por categoria
        recommendations = {}
        
        # 1. Conservadora (Safe) - até 4 jogadores
        conservadora = self.select_for_category(
            categorized['conservadora_candidates'], 
            'conservadora', 
            game_ctx,
            num_selections=4
        )
        
        # Aplica validação de correlação
        conservadora = [self.apply_correlation_adjustments(r, game_ctx) for r in conservadora]
        
        # Identifica estratégia
        if conservadora:
            strategy_name = self.identify_strategy(conservadora, game_ctx)
            for r in conservadora:
                r['identified_strategy'] = strategy_name
                r['strategy_description'] = self.strategy_templates.get(strategy_name, {}).get('description', '')
        
        recommendations['conservadora'] = conservadora[:4]
        
        # 2. Ousada (Upside) - até 3 jogadores
        ousada = self.select_for_category(
            categorized['ousada_candidates'], 
            'ousada', 
            game_ctx,
            num_selections=3
        )
        
        # Aplica validação
        ousada = [self.apply_correlation_adjustments(r, game_ctx) for r in ousada]
        
        if ousada:
            strategy_name = self.identify_strategy(ousada, game_ctx)
            for r in ousada:
                r['identified_strategy'] = strategy_name
                r['strategy_description'] = self.strategy_templates.get(strategy_name, {}).get('description', '')
        
        recommendations['ousada'] = ousada[:3]
        
        # 3. Banco (Value) - até 3 jogadores
        banco = self.select_for_category(
            categorized['banco_candidates'], 
            'banco', 
            game_ctx,
            num_selections=3
        )
        
        # Aplica validação
        banco = [self.apply_correlation_adjustments(r, game_ctx) for r in banco]
        
        if banco:
            strategy_name = self.identify_strategy(banco, game_ctx)
            for r in banco:
                r['identified_strategy'] = strategy_name
                r['strategy_description'] = self.strategy_templates.get(strategy_name, {}).get('description', '')
        
        recommendations['banco'] = banco[:3]
        
        # 4. Explosão (Boost) - até 2 jogadores
        explosao = self.select_for_category(
            categorized['explosao_candidates'], 
            'explosao', 
            game_ctx,
            num_selections=2
        )
        
        # Aplica validação
        explosao = [self.apply_correlation_adjustments(r, game_ctx) for r in explosao]
        
        if explosao:
            strategy_name = self.identify_strategy(explosao, game_ctx)
            for r in explosao:
                r['identified_strategy'] = strategy_name
                r['strategy_description'] = self.strategy_templates.get(strategy_name, {}).get('description', '')
        
        recommendations['explosao'] = explosao[:2]
        
        # Garante diversidade entre categorias (evita jogador repetido)
        self._ensure_cross_category_diversity(recommendations)
        
        return recommendations
    
    def _ensure_cross_category_diversity(self, recommendations: Dict[str, List[Dict]]):
        """
        Garante que um jogador não apareça em múltiplas categorias
        Mantém apenas a categoria com maior score
        """
        player_to_category = {}
        player_to_score = {}
        
        # Mapeia jogadores por categoria e score
        for category, recs in recommendations.items():
            for rec in recs:
                player = rec['player']
                score = rec.get('adjusted_confidence', rec['confidence'])
                
                if player in player_to_score:
                    if score > player_to_score[player]:
                        # Remove da categoria anterior
                        old_category = player_to_category[player]
                        recommendations[old_category] = [
                            r for r in recommendations[old_category] 
                            if r['player'] != player
                        ]
                        player_to_category[player] = category
                        player_to_score[player] = score
                    else:
                        # Remove desta categoria (já tem em outra com score maior)
                        recommendations[category] = [
                            r for r in recommendations[category] 
                            if r['player'] != player
                        ]
                else:
                    player_to_category[player] = category
                    player_to_score[player] = score
    
    def generate_multipla_dia(self, all_theses: Dict[str, List[Dict]], 
                            game_ctx: Dict) -> Dict[str, List[Dict]]:
        """
        Gera as múltiplas do dia (conservadora e ousada)
        """
        self.reset_selection()
        
        # Categoriza teses
        categorized = self.categorize_theses(all_theses, game_ctx)
        
        # Múltipla Conservadora: 3-6 entradas de maior confiança
        conservadora_multipla = self.select_for_category(
            categorized['conservadora_candidates'],
            'conservadora',
            game_ctx,
            num_selections=6
        )
        
        # Aplica validação
        conservadora_multipla = [self.apply_correlation_adjustments(r, game_ctx) 
                               for r in conservadora_multipla]
        
        # Limita a 3-6 entradas
        if len(conservadora_multipla) > 6:
            conservadora_multipla = conservadora_multipla[:6]
        
        # Múltipla Ousada: 2-4 entradas com maior upside
        # Reseta apenas os jogadores, mantém diversidade de times/mercados
        ousada_players = set()
        ousada_multipla = []
        
        for thesis in categorized['ousada_candidates']:
            if len(ousada_multipla) >= 4:
                break
            
            if thesis['player'] in self.used_players:
                continue
            
            # Adiciona à seleção
            ousada_players.add(thesis['player'])
            self.used_players.add(thesis['player'])
            
            # Aplica validação
            enhanced = self.apply_correlation_adjustments(thesis, game_ctx)
            ousada_multipla.append(enhanced)
        
        # Adiciona estratégias
        if conservadora_multipla:
            strategy_name = self.identify_strategy(conservadora_multipla, game_ctx)
            for r in conservadora_multipla:
                r['identified_strategy'] = strategy_name
                r['multipla_type'] = 'conservadora'
        
        if ousada_multipla:
            strategy_name = self.identify_strategy(ousada_multipla, game_ctx)
            for r in ousada_multipla:
                r['identified_strategy'] = strategy_name
                r['multipla_type'] = 'ousada'
        
        return {
            'conservadora': conservadora_multipla,
            'ousada': ousada_multipla
        }
    
    def format_recommendation_summary(self, recommendations: Dict[str, List[Dict]]) -> pd.DataFrame:
        """
        Formata resumo das recomendações em DataFrame
        """
        rows = []
        
        for category, recs in recommendations.items():
            for rec in recs:
                rows.append({
                    'Categoria': category.capitalize(),
                    'Jogador': rec['player'],
                    'Mercado': rec['market'],
                    'Linha Sugerida': rec.get('suggested_line', 'N/A'),
                    'Confiança Original': rec['confidence'],
                    'Confiança Ajustada': rec.get('adjusted_confidence', rec['confidence']),
                    'Ajuste': f"{rec.get('score_adjustment', 0)*100:.1f}%" if rec.get('score_adjustment') else '0%',
                    'Tese Principal': rec['thesis_type'],
                    'Estratégia': rec.get('identified_strategy', 'N/A'),
                    'Time': rec.get('player_team', ''),
                    'Role': rec.get('player_role', '')
                })
        
        return pd.DataFrame(rows)


# Função de exemplo para teste
def test_strategy_engine():
    """Testa o motor estratégico com dados de exemplo"""
    from thesis_engine import ThesisEngine
    
    # Cria motor de teses
    thesis_engine = ThesisEngine()
    
    # Dados de exemplo (múltiplos jogadores)
    players_data = [
        {
            'name': 'Bam Adebayo',
            'id': '203112',
            'pos': 'C',
            'role': 'starter',
            'min_avg': 34.5,
            'usg': 22.3,
            'ppg': 20.5,
            'rpg': 9.2,
            'apg': 3.8,
            'pra': 33.5,
            'ast_pct': 18.5,
            'dvp_reb': 1.15,
            'dvp_pts': 1.08,
            'dvp_ast': 0.95,
            'player_class': 'GLASS_BANGER; DEFENSIVE_ANCHOR',
            'team': 'MIA',
            'last_5_ppg': 21.8,
            'last_5_rpg': 10.1,
            'last_5_apg': 4.2,
            'last_5_min_avg': 35.2
        },
        {
            'name': 'Jimmy Butler',
            'id': '202710',
            'pos': 'SF',
            'role': 'starter',
            'min_avg': 33.8,
            'usg': 25.1,
            'ppg': 21.2,
            'rpg': 5.3,
            'apg': 5.0,
            'pra': 31.5,
            'ast_pct': 24.2,
            'dvp_reb': 1.05,
            'dvp_pts': 1.12,
            'dvp_ast': 1.08,
            'player_class': 'ALL_AROUND; CLUTCH',
            'team': 'MIA',
            'last_5_ppg': 22.5,
            'last_5_rpg': 5.8,
            'last_5_apg': 5.5,
            'last_5_min_avg': 34.5
        },
        {
            'name': 'Jaime Jaquez Jr.',
            'id': '1629611',
            'pos': 'SF',
            'role': 'rotation',
            'min_avg': 24.5,
            'usg': 18.5,
            'ppg': 12.3,
            'rpg': 3.8,
            'apg': 2.5,
            'pra': 18.6,
            'ast_pct': 15.2,
            'dvp_reb': 0.98,
            'dvp_pts': 1.05,
            'dvp_ast': 0.92,
            'player_class': 'BENCH_SPARK; YOUNG',
            'team': 'MIA',
            'last_5_ppg': 14.2,
            'last_5_rpg': 4.5,
            'last_5_apg': 3.0,
            'last_5_min_avg': 26.8
        },
        {
            'name': 'Tyler Herro',
            'id': '1629639',
            'pos': 'SG',
            'role': 'starter',
            'min_avg': 32.5,
            'usg': 26.8,
            'ppg': 20.8,
            'rpg': 4.2,
            'apg': 4.5,
            'pra': 29.5,
            'ast_pct': 22.5,
            'dvp_reb': 0.95,
            'dvp_pts': 1.15,
            'dvp_ast': 1.12,
            'player_class': 'SHOOTER; VOLUME_SCORER',
            'team': 'MIA',
            'last_5_ppg': 22.3,
            'last_5_rpg': 4.5,
            'last_5_apg': 5.2,
            'last_5_min_avg': 33.5
        }
    ]
    
    game_ctx = {
        'home_team': 'MIA',
        'away_team': 'BOS',
        'pace': 102.5,
        'spread': -3.5,
        'total': 225.5
    }
    
    # Gera teses para todos os jogadores
    all_theses = {}
    for player_ctx in players_data:
        player_name = player_ctx['name']
        theses = thesis_engine.generate_all_theses(player_ctx, game_ctx)
        if theses:
            # Adiciona contexto do jogador a cada tese
            for thesis in theses:
                thesis['player_ctx'] = player_ctx
            all_theses[player_name] = theses
    
    print(f"Total de jogadores com teses: {len(all_theses)}")
    
    # Cria motor estratégico
    strategy_engine = StrategyEngine()
    
    # Compõe recomendações
    recommendations = strategy_engine.compose_recommendations(all_theses, game_ctx)
    
    print("\n" + "="*80)
    print("RECOMENDAÇÕES ESTRATÉGICAS")
    print("="*80)
    
    for category, recs in recommendations.items():
        print(f"\n{strategy_engine.category_configs[category]['color']} "
              f"{category.upper()}: {strategy_engine.category_configs[category]['description']}")
        print("-" * 40)
        
        if not recs:
            print("  Nenhuma recomendação para esta categoria")
            continue
        
        for rec in recs:
            print(f"\n  Jogador: {rec['player']}")
            print(f"  Mercado: {rec['market']} ({rec.get('suggested_line', 'N/A')})")
            print(f"  Confiança: {rec['confidence']} → {rec.get('adjusted_confidence', rec['confidence'])} "
                  f"(ajuste: {rec.get('score_adjustment', 0)*100:.1f}%)")
            print(f"  Tese: {rec['thesis_type']}")
            print(f"  Estratégia: {rec.get('identified_strategy', 'N/A')}")
            
            if rec.get('adjustments'):
                print(f"  Ajustes: {', '.join(rec['adjustments'])}")
    
    # Testa múltipla do dia
    print("\n" + "="*80)
    print("MÚLTIPLA DO DIA")
    print("="*80)
    
    multipla = strategy_engine.generate_multipla_dia(all_theses, game_ctx)
    
    for multipla_type, recs in multipla.items():
        print(f"\nMúltipla {multipla_type.upper()}: {len(recs)} entradas")
        print("-" * 30)
        
        for rec in recs:
            print(f"  {rec['player']} - {rec['market']} ({rec.get('suggested_line', 'N/A')}) "
                  f"- Conf: {rec.get('adjusted_confidence', rec['confidence'])}")
    
    return recommendations


if __name__ == "__main__":
    # Teste do módulo
    test_strategy_engine()