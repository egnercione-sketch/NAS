# modules/new_modules/multipla_do_dia.py
"""
Módulo para geração da Múltipla do Dia (Conservadora + Ousada)
Integrado ao motor estratégico.
"""
import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Any, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class MultiplaDoDia:
    """
    Sistema para geração de múltiplas diárias com duas versões:
    1. Conservadora: 3-6 entradas, diversificação por confronto
    2. Ousada: 2-4 entradas, inclui bench/rotation
    """
    
    def __init__(self, strategy_engine=None, narrative_formatter=None):
        self.strategy_engine = strategy_engine
        self.narrative_formatter = narrative_formatter
        self.conservadora_bet = []
        self.ousada_bet = []
        self.bet_history = []
        
        # Configurações
        self.max_legs_per_matchup = 6
        self.max_players_per_team = 4
        self.min_legs_conservadora = 3
        self.max_legs_conservadora = 6
        self.min_legs_ousada = 2
        self.max_legs_ousada = 4
        
    def generate_multipla(self, game_data_list: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Gera a Múltipla do Dia com duas versões: conservadora e ousada.
        
        Args:
            game_data_list: Lista de dados dos jogos do dia
            
        Returns:
            Dicionário com as duas versões
        """
        logger.info("Gerando Múltipla do Dia...")
        
        # Inicializar listas
        conservadora = []
        ousada = []
        
        # Se StrategyEngine não está disponível, retornar vazio
        if not self.strategy_engine:
            logger.warning("StrategyEngine não disponível para Múltipla do Dia")
            return {"conservadora": conservadora, "ousada": ousada}
        
        try:
            # Processar cada jogo
            for game_data in game_data_list:
                # Criar contexto do jogo
                matchup_context = {
                    'home_team': game_data.get('home'),
                    'away_team': game_data.get('away'),
                    'spread': game_data.get('spread', 0),
                    'total': game_data.get('total', 220),
                    'pace': game_data.get('pace', 100),
                    'gameId': game_data.get('gameId')
                }
                
                # Criar DataFrame vazio (StrategyEngine lidará com os dados)
                players_data = pd.DataFrame()
                
                # Obter recomendações do StrategyEngine
                recommendations_dict = self.strategy_engine.compose_recommendations(
                    players_data, matchup_context
                )
                
                # Converter para lista plana e adicionar informações de categoria
                all_recommendations = []
                for category, recs in recommendations_dict.items():
                    for rec in recs:
                        rec['strategy'] = category
                        all_recommendations.append(rec)
                
                if not all_recommendations:
                    continue
                
                # Filtrar por categoria
                conservadora_recs = [rec for rec in all_recommendations if rec['strategy'] == 'conservadora']
                ousada_recs = [rec for rec in all_recommendations if rec['strategy'] == 'ousada']
                banco_recs = [rec for rec in all_recommendations if rec['strategy'] == 'banco']
                explosao_recs = [rec for rec in all_recommendations if rec['strategy'] == 'explosao']
                
                # Adicionar à múltipla consolidada
                conservadora.extend(conservadora_recs)
                ousada.extend(ousada_recs + banco_recs + explosao_recs)
            
            # Aplicar diversificação final
            conservadora = self._apply_diversification(conservadora, self.max_legs_conservadora)
            ousada = self._apply_diversification(ousada, self.max_legs_ousada)
            
            # Garantir mínimo de entradas
            if len(conservadora) < self.min_legs_conservadora:
                conservadora = conservadora[:self.min_legs_conservadora]
            if len(ousada) < self.min_legs_ousada:
                ousada = ousada[:self.min_legs_ousada]
            
            # Remover duplicatas entre as duas versões
            conservadora_ids = {rec.get('player_id') for rec in conservadora}
            ousada = [rec for rec in ousada if rec.get('player_id') not in conservadora_ids]
            
            return {
                "conservadora": conservadora,
                "ousada": ousada
            }
            
        except Exception as e:
            logger.error(f"Erro ao gerar Múltipla do Dia: {e}")
            return {"conservadora": [], "ousada": []}
    
    def _apply_diversification(self, recommendations: List[Dict], max_legs: int) -> List[Dict]:
        """Aplica regras de diversificação às recomendações."""
        if not recommendations:
            return recommendations
        
        # Ordenar por confiança
        recommendations.sort(key=lambda x: x.get('confidence', 0), reverse=True)
        
        # Aplicar limites
        selected = []
        team_counts = {}
        
        for rec in recommendations:
            player_id = rec.get('player_id')
            team = rec.get('team')
            
            # Verificar se jogador já foi selecionado
            if player_id in [r.get('player_id') for r in selected]:
                continue
                
            # Verificar limite por time
            if team_counts.get(team, 0) >= self.max_players_per_team:
                continue
            
            selected.append(rec)
            team_counts[team] = team_counts.get(team, 0) + 1
            
            # Parar quando atingir o máximo
            if len(selected) >= max_legs:
                break
        
        return selected
    
    def export_multipla(self, bet_type: str = 'conservadora') -> Dict:
        """
        Exporta bilhete em formato estruturado.
        
        Args:
            bet_type: 'conservadora' ou 'ousada'
            
        Returns:
            Dicionário com dados do bilhete
        """
        if bet_type == 'conservadora':
            bet = self.conservadora_bet
        else:
            bet = self.ousada_bet
        
        export_data = {
            'type': bet_type,
            'generated_at': datetime.now().isoformat(),
            'legs': len(bet),
            'entries': [],
            'summary': {
                'total_players': len(bet),
                'avg_confidence': np.mean([rec.get('confidence', 0) for rec in bet]) * 100 if bet else 0,
            }
        }
        
        for rec in bet:
            entry = {
                'player_id': rec.get('player_id'),
                'name': rec.get('name'),
                'team': rec.get('team'),
                'position': rec.get('position'),
                'target_stat': rec.get('primary_thesis', 'PRA'),
                'projection': rec.get('stats', {}).get('pra_avg', 0),
                'confidence': rec.get('confidence', 0),
                'strategy': rec.get('strategy'),
                'matchup': f"{rec.get('team')} vs {rec.get('opponent', 'N/A')}"
            }
            export_data['entries'].append(entry)
        
        return export_data