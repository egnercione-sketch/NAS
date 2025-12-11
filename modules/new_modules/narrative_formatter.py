# modules/new_modules/narrative_formatter.py
"""
Narrative Formatter - Formatação de Narrativas Explicativas
Transforma recomendações em narrativas textuais claras e explicativas
"""

import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime

class NarrativeFormatter:
    """
    Formata recomendações em narrativas textuais explicativas
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """Inicializa o formatador de narrativas"""
        self.config = config or {}
        
        # Templates de narrativa por categoria
        self.narrative_templates = {
            'conservadora': {
                'title': "🎯 Trixie Conservadora (Safe Play)",
                'intro': "Aposta segura com baixa volatilidade, foco em titulares com matchup favorável.",
                'template': """**{player}** ({position} - {archetype})
📊 Mercado: **{market_line}**
⚖️ Confiança: **{confidence}** {confidence_emoji}
📈 Tese: {thesis_explanation}
🎯 Estratégia: {strategy_description}
✅ Validação: {validation_summary}
👉 Narrativa: "{narrative_text}""""
            },
            'ousada': {
                'title': "🚀 Trixie Ousada (Upside Play)",
                'intro': "Maior risco, maior retorno potencial. Foco em upside e situações específicas.",
                'template': """**{player}** ({position} - {archetype})
📊 Mercado: **{market_line}**
⚖️ Confiança: **{confidence}** {confidence_emoji}
📈 Tese: {thesis_explanation}
🎯 Estratégia: {strategy_description}
✅ Validação: {validation_summary}
👉 Narrativa: "{narrative_text}""""
            },
            'banco': {
                'title': "💰 Trixie Banco (Value Hunter)",
                'intro': "Aposta no banco com bom custo-benefício, foco em reservas com upside.",
                'template': """**{player}** ({position} - {archetype})
📊 Mercado: **{market_line}**
⚖️ Confiança: **{confidence}** {confidence_emoji}
📈 Tese: {thesis_explanation}
🎯 Estratégia: {strategy_description}
✅ Validação: {validation_summary}
👉 Narrativa: "{narrative_text}""""
            },
            'explosao': {
                'title': "⚡ Trixie Explosão (Boost Play)",
                'intro': "Situações específicas de alto potencial, ativadas por contexto do jogo.",
                'template': """**{player}** ({position} - {archetype})
📊 Mercado: **{market_line}**
⚖️ Confiança: **{confidence}** {confidence_emoji}
📈 Tese: {thesis_explanation}
🎯 Estratégia: {strategy_description}
✅ Validação: {validation_summary}
👉 Narrativa: "{narrative_text}""""
            }
        }
        
        # Mapeamento de emojis para confiança
        self.confidence_emojis = {
            'very_high': '🟢🟢🟢',
            'high': '🟢🟢⚪',
            'medium': '🟡🟡⚪',
            'low': '🔴🔴⚪'
        }
        
        # Explicações de teses
        self.thesis_explanations = {
            'BigRebound': "Jogador dominante no garrafão com matchup favorável para rebotes",
            'AssistMatchup': "Armador com alto AST% em jogo competitivo e defesa vulnerável",
            'ScorerLine': "Scorer de volume contra defesa fraca no perímetro",
            'ValueHunter': "Reserva com bom valor PRA/min e minutos crescentes",
            'PaceBoost': "Jogador beneficiado pelo ritmo acelerado do jogo",
            'BlowoutRisk': "Alerta de risco por possível blowout"
        }
        
        # Templates de narrativa textual
        self.narrative_text_templates = {
            'BigRebound': [
                "Entrar em {market_line} para {player}, que domina o garrafão contra defesa vulnerável e reforça teses de rebote.",
                "{player} tem matchup favorável para explorar rebotes, com ritmo de jogo acelerado ajudando.",
                "Aposta conservadora em {player} para rebotes, aproveitando defesa frágil no garrafão adversário."
            ],
            'AssistMatchup': [
                "Explorar {market_line} de {player} em jogo parelho, reforçando teses de criação ofensiva.",
                "{player} como principal criador em jogo competitivo, com defesa adversária permitindo assistências.",
                "Aposta em {player} para assistências extras em jogo com ritmo acelerado e defesa vulnerável."
            ],
            'ScorerLine': [
                "{player} como opção sólida para {market_line}, explorando defesa fraca no perímetro.",
                "Scorer de volume em boa fase, com matchup favorável para pontuação contra {team}.",
                "Entrar em {market_line} para {player}, que tem USG% alto e defesa adversária frágil."
            ],
            'ValueHunter': [
                "Colocar um dinheirinho em {player}, reserva com perfil de garbage time e upside em {market}.",
                "Value play em {player}, que vem mostrando bom aproveitamento de minutos como reserva.",
                "Aposta no banco com {player}, que tem PRA/min alto e pode se beneficiar de minutos extras."
            ],
            'PaceBoost': [
                "Apostar em {player} para {market_line} extras em jogo acelerado e parelho, reforçando teses de pace.",
                "{player} se beneficia do ritmo alto, com histórico de bom desempenho em jogos rápidos.",
                "Explorar o pace acelerado com {player}, que tem perfil ideal para jogos de transição."
            ]
        }
        
        # Mapeamento de posições para nomes completos
        self.position_names = {
            'PG': 'Armador',
            'SG': 'Ala-armador',
            'SF': 'Ala',
            'PF': 'Ala-pivô',
            'C': 'Pivô'
        }
    
    def get_confidence_level(self, confidence: float) -> Tuple[str, str]:
        """Determina nível e emoji de confiança"""
        if confidence >= 0.75:
            return 'very_high', self.confidence_emojis['very_high']
        elif confidence >= 0.65:
            return 'high', self.confidence_emojis['high']
        elif confidence >= 0.55:
            return 'medium', self.confidence_emojis['medium']
        else:
            return 'low', self.confidence_emojis['low']
    
    def format_market_line(self, recommendation: Dict) -> str:
        """Formata a linha de mercado"""
        market = recommendation['market']
        suggested_line = recommendation.get('suggested_line', '')
        
        if market == 'PTS':
            return f"{suggested_line} pontos"
        elif market == 'REB':
            return f"{suggested_line} rebotes"
        elif market == 'AST':
            return f"{suggested_line} assistências"
        elif market == 'PRA':
            return f"{suggested_line} PRA"
        elif market == 'REB+AST':
            reb_line = recommendation.get('suggested_reb_line', '')
            ast_line = recommendation.get('suggested_ast_line', '')
            return f"{reb_line} rebotes + {ast_line} assistências"
        elif market == 'PTS+REB':
            pts_line = recommendation.get('suggested_pts_line', '')
            reb_line = recommendation.get('suggested_reb_line', '')
            return f"{pts_line} pontos + {reb_line} rebotes"
        else:
            return f"{suggested_line} {market}"
    
    def generate_narrative_text(self, recommendation: Dict, game_ctx: Dict) -> str:
        """Gera o texto narrativo para uma recomendação"""
        thesis_type = recommendation['thesis_type']
        player = recommendation['player']
        market_line = self.format_market_line(recommendation)
        
        # Seleciona template baseado na tese
        templates = self.narrative_text_templates.get(thesis_type, [])
        if not templates:
            # Template padrão
            return f"Entrar em {market_line} para {player}, reforçando teses de {thesis_type}."
        
        # Seleciona template aleatório para variedade
        import random
        template = random.choice(templates)
        
        # Adiciona contexto específico
        narrative = template.format(
            player=player,
            market_line=market_line,
            market=recommendation['market'],
            team=game_ctx.get('opponent_team', 'o adversário')
        )
        
        # Adiciona detalhes específicos se disponíveis
        adjustments = recommendation.get('adjustments', [])
        if adjustments:
            # Extrai apenas os ajustes positivos/negativos
            bonuses = [a for a in adjustments if 'Bônus' in a]
            penalties = [a for a in adjustments if 'Penalidade' in a]
            
            if bonuses:
                bonus_reason = bonuses[0].split(': ')[1] if ': ' in bonuses[0] else ''
                narrative += f" {bonus_reason}"
            elif penalties:
                narrative += " Atenção para fatores de risco."
        
        return narrative
    
    def format_thesis_explanation(self, recommendation: Dict) -> str:
        """Formata a explicação da tese"""
        thesis_type = recommendation['thesis_type']
        base_explanation = self.thesis_explanations.get(thesis_type, thesis_type)
        
        # Adiciona evidências se disponíveis
        evidences = recommendation.get('evidences', [])
        if evidences:
            # Limita a 2 evidências principais
            key_evidences = evidences[:2]
            evidence_text = '; '.join(key_evidences)
            return f"{base_explanation}. ({evidence_text})"
        
        return base_explanation
    
    def format_validation_summary(self, recommendation: Dict) -> str:
        """Formata o resumo da validação"""
        adjustments = recommendation.get('adjustments', [])
        score_adjustment = recommendation.get('score_adjustment', 0)
        
        if not adjustments:
            return "✅ Validação OK, sem violações críticas"
        
        # Separa bônus e penalidades
        bonuses = [a for a in adjustments if 'Bônus' in a]
        penalties = [a for a in adjustments if 'Penalidade' in a]
        
        summary_parts = []
        
        if bonuses:
            bonus_count = len(bonuses)
            summary_parts.append(f"✅ {bonus_count} bônus aplicados")
        
        if penalties:
            penalty_count = len(penalties)
            summary_parts.append(f"⚠️ {penalty_count} penalizações")
        
        if score_adjustment > 0:
            summary_parts.append(f"📈 Score ajustado +{score_adjustment*100:.0f}%")
        elif score_adjustment < 0:
            summary_parts.append(f"📉 Score ajustado {score_adjustment*100:.0f}%")
        
        return "; ".join(summary_parts) if summary_parts else "Validação padrão"
    
    def get_archetype_display(self, player_ctx: Dict) -> str:
        """Obtém o archetype para display"""
        player_class = player_ctx.get('player_class', '')
        
        # Mapeamento de classes para archetypes mais amigáveis
        archetype_map = {
            'GLASS_BANGER': 'Dominador do Garrafão',
            'FLOOR_GENERAL': 'General de Quadra',
            'SCORER': 'Scorer de Volume',
            'SHOOTER': 'Arremessador',
            'DEFENSIVE_ANCHOR': 'Âncora Defensiva',
            'PLAYMAKER': 'Criador de Jogo',
            'ALL_AROUND': 'Completo',
            'CLUTCH': 'Clutch',
            'BENCH_SPARK': 'Faísca do Banco',
            'YOUNG': 'Jovem Talento',
            'VETERAN': 'Veterano',
            'ATHLETIC': 'Atlético',
            'TRANSITION': 'Jogador de Transição'
        }
        
        # Pega a primeira classe e mapeia
        if player_class:
            classes = player_class.split(';')
            first_class = classes[0].strip()
            return archetype_map.get(first_class, first_class)
        
        return 'Perfil Padrão'
    
    def format_recommendation(self, recommendation: Dict, game_ctx: Dict, 
                            category: str) -> Dict[str, Any]:
        """Formata uma recomendação individual"""
        # Obtém contexto do jogador
        player_ctx = recommendation.get('player_ctx', {})
        
        # Prepara os dados para o template
        position = player_ctx.get('pos', '')
        position_display = self.position_names.get(position, position)
        
        archetype = self.get_archetype_display(player_ctx)
        market_line = self.format_market_line(recommendation)
        
        # Usa confiança ajustada se disponível
        confidence = recommendation.get('adjusted_confidence', recommendation['confidence'])
        confidence_level, confidence_emoji = self.get_confidence_level(confidence)
        
        thesis_explanation = self.format_thesis_explanation(recommendation)
        strategy_description = recommendation.get('strategy_description', 'Estratégia personalizada')
        validation_summary = self.format_validation_summary(recommendation)
        narrative_text = self.generate_narrative_text(recommendation, game_ctx)
        
        # Formata usando template da categoria
        template_data = {
            'player': recommendation['player'],
            'position': position_display,
            'archetype': archetype,
            'market_line': market_line,
            'confidence': f"{confidence:.0%}",
            'confidence_emoji': confidence_emoji,
            'thesis_explanation': thesis_explanation,
            'strategy_description': strategy_description,
            'validation_summary': validation_summary,
            'narrative_text': narrative_text,
            'team': player_ctx.get('team', ''),
            'role': player_ctx.get('role', '').capitalize()
        }
        
        # Aplica ao template
        category_template = self.narrative_templates[category]['template']
        formatted_text = category_template.format(**template_data)
        
        return {
            'title': self.narrative_templates[category]['title'],
            'intro': self.narrative_templates[category]['intro'],
            'formatted_text': formatted_text,
            'raw_data': recommendation,
            'metadata': {
                'player': recommendation['player'],
                'market': recommendation['market'],
                'confidence': confidence,
                'thesis': recommendation['thesis_type'],
                'strategy': recommendation.get('identified_strategy', ''),
                'category': category
            }
        }
    
    def format_all_recommendations(self, recommendations: Dict[str, List[Dict]], 
                                 game_ctx: Dict) -> Dict[str, List[Dict]]:
        """Formata todas as recomendações por categoria"""
        formatted = {}
        
        for category, recs in recommendations.items():
            formatted[category] = []
            
            for rec in recs:
                formatted_rec = self.format_recommendation(rec, game_ctx, category)
                formatted[category].append(formatted_rec)
        
        return formatted
    
    def format_multipla_dia(self, multipla_recommendations: Dict[str, List[Dict]], 
                          game_ctx: Dict) -> Dict[str, Dict]:
        """Formata as múltiplas do dia"""
        formatted = {}
        
        for multipla_type, recs in multipla_recommendations.items():
            if not recs:
                continue
            
            # Ordena por confiança ajustada
            sorted_recs = sorted(
                recs,
                key=lambda x: x.get('adjusted_confidence', x['confidence']),
                reverse=True
            )
            
            # Formata cada recomendação
            formatted_recs = []
            for rec in sorted_recs:
                # Usa categoria correspondente para a formatação
                category = 'conservadora' if multipla_type == 'conservadora' else 'ousada'
                formatted_rec = self.format_recommendation(rec, game_ctx, category)
                formatted_recs.append(formatted_rec)
            
            # Cria cabeçalho da múltipla
            header = self._create_multipla_header(multipla_type, formatted_recs, game_ctx)
            
            formatted[multipla_type] = {
                'header': header,
                'recommendations': formatted_recs,
                'summary': self._create_multipla_summary(formatted_recs)
            }
        
        return formatted
    
    def _create_multipla_header(self, multipla_type: str, 
                              recommendations: List[Dict], 
                              game_ctx: Dict) -> str:
        """Cria cabeçalho para a múltipla do dia"""
        num_entries = len(recommendations)
        avg_confidence = sum(r['metadata']['confidence'] for r in recommendations) / num_entries
        
        if multipla_type == 'conservadora':
            title = "🎯 MÚLTIPLA CONSERVADORA DO DIA"
            description = f"{num_entries} entradas selecionadas para baixa volatilidade e confiança média de {avg_confidence:.0%}"
        else:
            title = "🚀 MÚLTIPLA OUSADA DO DIA"
            description = f"{num_entries} entradas com maior upside e confiança média de {avg_confidence:.0%}"
        
        # Adiciona contexto do jogo
        home_team = game_ctx.get('home_team', '')
        away_team = game_ctx.get('away_team', '')
        spread = game_ctx.get('spread', 0)
        total = game_ctx.get('total', 0)
        pace = game_ctx.get('pace', 0)
        
        context_lines = [
            f"**Confronto:** {away_team} @ {home_team}",
            f"**Spread:** {spread} | **Total:** {total} | **Pace:** {pace}"
        ]
        
        context_text = " | ".join(context_lines)
        
        return f"""
### {title}
{description}

{context_text}

---
"""
    
    def _create_multipla_summary(self, recommendations: List[Dict]) -> str:
        """Cria resumo estatístico da múltipla"""
        if not recommendations:
            return ""
        
        # Estatísticas
        total_entries = len(recommendations)
        avg_confidence = sum(r['metadata']['confidence'] for r in recommendations) / total_entries
        
        # Contagem por mercado
        markets = {}
        for r in recommendations:
            market = r['metadata']['market']
            markets[market] = markets.get(market, 0) + 1
        
        market_summary = ", ".join([f"{count}×{market}" for market, count in markets.items()])
        
        # Times envolvidos
        teams = set()
        for r in recommendations:
            team = r.get('raw_data', {}).get('player_team', '')
            if team:
                teams.add(team)
        
        team_summary = ", ".join(sorted(teams))
        
        return f"""
**📊 Resumo da Múltipla:**
- **Entradas:** {total_entries} picks
- **Confiança Média:** {avg_confidence:.0%}
- **Mercados:** {market_summary}
- **Times:** {team_summary if team_summary else 'Diversificado'}

💡 **Estratégia:** Diversificação entre {len(teams)} times e {len(markets)} mercados diferentes.
"""
    
    def create_detailed_report(self, formatted_recommendations: Dict[str, List[Dict]], 
                             game_ctx: Dict) -> str:
        """Cria relatório detalhado com todas as recomendações"""
        report_parts = []
        
        # Cabeçalho do relatório
        report_parts.append("# 📈 RELATÓRIO DE TRIXIES ESTRATÉGICAS")
        report_parts.append(f"*Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}*")
        report_parts.append("")
        
        # Contexto do jogo
        home_team = game_ctx.get('home_team', '')
        away_team = game_ctx.get('away_team', '')
        spread = game_ctx.get('spread', 0)
        total = game_ctx.get('total', 0)
        pace = game_ctx.get('pace', 0)
        
        report_parts.append(f"**Confronto:** {away_team} @ {home_team}")
        report_parts.append(f"**Spread:** {spread} | **Total:** {total} | **Pace Estimado:** {pace}")
        report_parts.append("---")
        report_parts.append("")
        
        # Recomendações por categoria
        for category, recs in formatted_recommendations.items():
            if not recs:
                continue
            
            category_config = self.narrative_templates[category]
            report_parts.append(f"## {category_config['title']}")
            report_parts.append(f"*{category_config['intro']}*")
            report_parts.append("")
            
            for rec in recs:
                report_parts.append(rec['formatted_text'])
                report_parts.append("")
        
        return "\n".join(report_parts)
    
    def create_quick_summary_table(self, recommendations: Dict[str, List[Dict]]) -> pd.DataFrame:
        """Cria tabela resumo rápida das recomendações"""
        rows = []
        
        for category, recs in recommendations.items():
            for rec in recs:
                raw_data = rec.get('raw_data', {})
                metadata = rec.get('metadata', {})
                
                rows.append({
                    'Categoria': category.capitalize(),
                    'Jogador': metadata.get('player', ''),
                    'Mercado': metadata.get('market', ''),
                    'Confiança': f"{metadata.get('confidence', 0):.0%}",
                    'Tese': metadata.get('thesis', ''),
                    'Estratégia': metadata.get('strategy', ''),
                    'Time': raw_data.get('player_team', ''),
                    'Role': raw_data.get('player_role', '').capitalize()
                })
        
        return pd.DataFrame(rows)


# Função de exemplo para teste
def test_narrative_formatter():
    """Testa o formatador de narrativas com dados de exemplo"""
    from thesis_engine import ThesisEngine
    from strategy_engine import StrategyEngine
    
    # Dados de exemplo
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
        }
    ]
    
    game_ctx = {
        'home_team': 'MIA',
        'away_team': 'BOS',
        'pace': 102.5,
        'spread': -3.5,
        'total': 225.5,
        'opponent_team': 'Celtics'
    }
    
    # Gera teses
    thesis_engine = ThesisEngine()
    all_theses = {}
    
    for player_ctx in players_data:
        player_name = player_ctx['name']
        theses = thesis_engine.generate_all_theses(player_ctx, game_ctx)
        if theses:
            for thesis in theses:
                thesis['player_ctx'] = player_ctx
            all_theses[player_name] = theses
    
    # Gera recomendações
    strategy_engine = StrategyEngine()
    recommendations = strategy_engine.compose_recommendations(all_theses, game_ctx)
    
    # Formata narrativas
    formatter = NarrativeFormatter()
    formatted = formatter.format_all_recommendations(recommendations, game_ctx)
    
    print("="*80)
    print("TESTE DO NARRATIVE FORMATTER")
    print("="*80)
    
    for category, recs in formatted.items():
        if recs:
            print(f"\n{recs[0]['title']}")
            print("-" * 40)
            
            for rec in recs:
                print("\n" + rec['formatted_text'])
    
    # Testa múltipla do dia
    print("\n" + "="*80)
    print("MÚLTIPLA DO DIA FORMATADA")
    print("="*80)
    
    multipla = strategy_engine.generate_multipla_dia(all_theses, game_ctx)
    formatted_multipla = formatter.format_multipla_dia(multipla, game_ctx)
    
    for multipla_type, content in formatted_multipla.items():
        print(content['header'])
        
        for rec in content['recommendations']:
            print("\n" + rec['formatted_text'])
        
        print(content['summary'])
    
    # Testa relatório detalhado
    print("\n" + "="*80)
    print("RELATÓRIO DETALHADO (PRIMEIRAS LINHAS)")
    print("="*80)
    
    report = formatter.create_detailed_report(formatted, game_ctx)
    print(report[:500] + "...")
    
    # Testa tabela resumo
    print("\n" + "="*80)
    print("TABELA RESUMO")
    print("="*80)
    
    summary_table = formatter.create_quick_summary_table(formatted)
    print(summary_table.to_string())
    
    return formatted


if __name__ == "__main__":
    # Teste do módulo
    test_narrative_formatter()