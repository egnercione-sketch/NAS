"""
Módulo para criação da Múltipla do Dia.
Seleciona as melhores recomendações das estratégias para formar bilhetes múltiplos.
"""

import random
from typing import List, Dict, Any, Tuple
import streamlit as st

class DailyMultipleEngine:
    """
    Engine para criar as múltiplas do dia (conservadora e ousada).
    """
    
    def __init__(self, strategy_engine, correlation_validator):
        self.strategy_engine = strategy_engine
        self.correlation_validator = correlation_validator
        self.conservative_multiple = []
        self.aggressive_multiple = []
        
    def compose_daily_multiples(self, all_recommendations: Dict[str, List[Dict]]) -> Dict[str, List[Dict]]:
        """
        Compõe as múltiplas do dia a partir de todas as recomendações estratégicas.
        
        Args:
            all_recommendations: Dicionário com listas de recomendações por categoria.
                                Chaves: 'conservadora', 'ousada', 'banco', 'explosao'
        
        Returns:
            Dicionário com as múltiplas do dia: {'conservadora': [], 'ousada': []}
        """
        
        # Extrair todas as recomendações, mantendo a categoria de origem
        all_recs = []
        for category, recs in all_recommendations.items():
            for rec in recs:
                rec['original_category'] = category
                all_recs.append(rec)
        
        # Ordenar por confiança ajustada (score_final)
        all_recs_sorted = sorted(all_recs, key=lambda x: x.get('score_final', 0), reverse=True)
        
        # Separar por confronto (usando matchup_id ou time)
        # Vamos agrupar por confronto para garantir diversidade
        confrontos = {}
        for rec in all_recs_sorted:
            # Extrair confronto (assumindo que temos home_team e away_team no contexto do matchup)
            matchup_ctx = rec.get('matchup_ctx', {})
            matchup_key = f"{matchup_ctx.get('away_team', 'UNK')}@{matchup_ctx.get('home_team', 'UNK')}"
            if matchup_key not in confrontos:
                confrontos[matchup_key] = []
            confrontos[matchup_key].append(rec)
        
        # Critérios para seleção:
        # 1. Máximo de 1 recomendação por jogador
        # 2. Máximo de 2 recomendações por time (considerando times opostos no mesmo confronto)
        # 3. Diversidade de mercados (PTS, REB, AST, PRA, etc.)
        # 4. Preferência por categorias originais: conservadora e ousada para a múltipla conservadora,
        #    ousada, banco e explosão para a múltipla ousada.
        
        conservative_candidates = [r for r in all_recs_sorted if r['original_category'] in ['conservadora', 'ousada']]
        aggressive_candidates = [r for r in all_recs_sorted if r['original_category'] in ['ousada', 'banco', 'explosao']]
        
        # Filtrar candidatos para remover duplicatas e aplicar validação
        conservative_selected = self._select_for_multiple(conservative_candidates, max_legs=6, max_per_team=2)
        aggressive_selected = self._select_for_multiple(aggressive_candidates, max_legs=4, max_per_team=1)
        
        # Aplicar validação de correlação para as múltiplas
        conservative_validated = self._validate_multiple(conservative_selected)
        aggressive_validated = self._validate_multiple(aggressive_selected)
        
        return {
            'conservadora': conservative_validated,
            'ousada': aggressive_validated
        }
    
    def _select_for_multiple(self, candidates: List[Dict], max_legs: int, max_per_team: int) -> List[Dict]:
        """
        Seleciona as melhores recomendações para uma múltipla, aplicando regras de diversidade.
        """
        selected = []
        used_players = set()
        used_teams = {}
        used_markets = set()
        
        for rec in candidates:
            if len(selected) >= max_legs:
                break
            
            player_id = rec.get('player_id')
            team = rec.get('team')
            market = rec.get('market')
            
            # Verificar se o jogador já foi selecionado
            if player_id in used_players:
                continue
            
            # Verificar limite por time
            if used_teams.get(team, 0) >= max_per_team:
                continue
            
            # Adicionar à seleção
            selected.append(rec)
            used_players.add(player_id)
            used_teams[team] = used_teams.get(team, 0) + 1
            used_markets.add(market)
        
        return selected
    
    def _validate_multiple(self, multiple: List[Dict]) -> List[Dict]:
        """
        Aplica validação de correlação a uma múltipla.
        """
        if not multiple:
            return []
        
        # Validar cada par de pernas na múltipla
        violations = []
        for i in range(len(multiple)):
            for j in range(i+1, len(multiple)):
                rec1 = multiple[i]
                rec2 = multiple[j]
                
                # Validar correlação entre as duas pernas
                violation = self.correlation_validator.validate_pair(rec1, rec2)
                if violation:
                    violations.append(violation)
        
        # Se houver violações críticas, remover a perna com menor confiança
        critical_violations = [v for v in violations if v.get('severity') == 'critical']
        if critical_violations:
            # Remover a perna com menor score_final
            multiple_sorted = sorted(multiple, key=lambda x: x.get('score_final', 0))
            multiple.remove(multiple_sorted[0])
            # Chamar recursivamente até não haver violações críticas
            return self._validate_multiple(multiple)
        
        return multiple
    
    def format_multiple_for_display(self, multiple: List[Dict], category: str) -> str:
        """
        Formata uma múltipla para exibição na interface.
        
        Returns:
            String formatada em HTML/markdown.
        """
        if not multiple:
            return "Nenhuma recomendação adequada para a múltipla do dia."
        
        # Cabeçalho
        if category == 'conservadora':
            title = "## 🛡️ Múltipla Conservadora do Dia"
            desc = "Bilhete com as recomendações de maior confiança, focando em segurança e diversificação."
        else:
            title = "## 🎯 Múltipla Ousada do Dia"
            desc = "Bilhete com maior potencial de retorno, aceitando mais risco por mais upside."
        
        # Calcular odds aproximadas (supondo odds fixas para cada mercado)
        # Na prática, isso viria de uma API de odds
        total_odds = 1.0
        for rec in multiple:
            market_odds = self._estimate_odds(rec.get('market'), rec.get('line'))
            total_odds *= market_odds
        
        # Construir a tabela
        table_lines = []
        table_lines.append("| Jogador | Mercado | Linha | Confiança | Estratégia |")
        table_lines.append("|---------|---------|-------|-----------|------------|")
        
        for rec in multiple:
            player = rec.get('player_name', 'N/A')
            market = rec.get('market', 'N/A')
            line = rec.get('line', 'N/A')
            confidence = rec.get('confidence', 0)
            strategy = rec.get('strategy_identified', 'N/A')
            
            table_lines.append(f"| {player} | {market} | {line} | {confidence:.2f} | {strategy} |")
        
        # Montar o texto final
        formatted = f"{title}\n\n{desc}\n\n"
        formatted += f"**Total de pernas:** {len(multiple)}\n\n"
        formatted += f"**Odd aproximada:** {total_odds:.2f}\n\n"
        formatted += "\n".join(table_lines)
        
        # Adicionar racional
        formatted += "\n\n### 🧠 Racional da Múltipla\n"
        for rec in multiple:
            narrative = rec.get('narrative', '')
            if narrative:
                formatted += f"- {narrative}\n"
        
        return formatted
    
    def _estimate_odds(self, market: str, line: Any) -> float:
        """
        Estima as odds para um mercado e linha específicos.
        Em produção, isso viria de uma API de odds.
        """
        # Valores fictícios para exemplo
        odds_map = {
            'PTS': 1.8,
            'REB': 1.9,
            'AST': 2.0,
            'PRA': 2.5,
            'PTS+REB': 2.2,
            'PTS+AST': 2.3,
            'REB+AST': 2.4,
            '3PTM': 2.1,
            'BLK': 2.3,
            'STL': 2.5
        }
        
        return odds_map.get(market, 1.9)