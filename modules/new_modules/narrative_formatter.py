# modules/new_modules/narrative_formatter.py
"""
NarrativeFormatter - Módulo para formatar recomendações em narrativas textuais explicativas
com templates específicos para cada estratégia.
"""
import pandas as pd
from typing import Dict, List, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class NarrativeFormatter:
    def __init__(self):
        self.templates = self._load_templates()
        self.color_codes = {
            "conservadora": "#2E7D32",  # Verde
            "ousada": "#D84315",         # Laranja
            "banco": "#1565C0",          # Azul
            "explosao": "#6A1B9A"        # Roxo
        }
        
    def _load_templates(self) -> Dict:
        """Carrega templates de narrativa para cada estratégia."""
        return {
            "conservadora": {
                "title": "🎯 JOGO CONSERVADOR",
                "subtitle": "Titulares com baixa volatilidade e alta confiança",
                "introduction": "Esta estratégia foca em **titulares estabelecidos** com histórico consistente e matchups favoráveis. Ideal para construir uma base sólida de apostas.",
                "player_template": "**{name}** ({position}) - Confiança: **{confidence}%**\n\n📊 *{primary_thesis}*: {motives}\n\n📈 Estatísticas Projetadas: {stats_summary}\n\n🔍 {additional_evidence}",
                "closing": "Esta seleção oferece a melhor relação risco-retorno para apostadores que preferem segurança e consistência."
            },
            "ousada": {
                "title": "⚡ APOSTA OUSADA",
                "subtitle": "Alto teto estatístico e potencial explosivo",
                "introduction": "Estratégia focada em jogadores com **potencial de superação**, seja por matchup extremamente favorável, aumento de minutos ou contexto de jogo.",
                "player_template": "**{name}** ({position}) - Potencial: **{upside_score}/10**\n\n⚡ *{primary_thesis}*: {motives}\n\n🚀 Fatores de Explosão: {explosion_factors}\n\n🎯 Projeção Otimista: {optimistic_projection}\n\n⚠️ Riscos: {risks}",
                "closing": "Recomendado para apostadores dispostos a assumir mais risco em troca de retornos potencialmente maiores."
            },
            "banco": {
                "title": "💰 CAÇA VALOR",
                "subtitle": "Reservas com boa relação custo-benefício",
                "introduction": "Foco em jogadores de **banco ou rotation** que podem superar expectativas devido a matchups favoráveis, garbage time ou aumento de oportunidades.",
                "player_template": "**{name}** ({position}) - Valor: **{value_score}/10**\n\n💰 *{primary_thesis}*: {motives}\n\n📊 Estatísticas por Minuto: {per_minute_stats}\n\n🎪 Contexto de Oportunidade: {opportunity_context}\n\n📈 Razão Custo-Benefício: {value_ratio}",
                "closing": "Ideal para apostas de valor onde o mercado pode estar subestimando o potencial do jogador."
            },
            "explosao": {
                "title": "🚀 FATOR EXPLOSIVO",
                "subtitle": "Contextos situacionais e fatores inesperados",
                "introduction": "Estratégia que capitaliza em **eventos imprevisíveis** como lesões, mudanças de escalação, ritmo extremo ou condições específicas do jogo.",
                "player_template": "**{name}** ({position}) - Impacto: **{impact_score}/10**\n\n🚀 *{primary_thesis}*: {motives}\n\n💥 Fatores Situacionais: {situational_factors}\n\n🎭 Elemento Surpresa: {surprise_element}\n\n⚡ Projeção no Cenário Ideal: {best_case}",
                "closing": "Para apostadores que buscam capitalizar em situações únicas e potencialmente mal precificadas pelo mercado."
            }
        }
    
    def format_recommendations(self, strategy_recommendations: Dict, matchup_context: Dict) -> Dict:
        """
        Formata todas as recomendações em narrativas textuais.
        
        Args:
            strategy_recommendations: Dict com recomendações por categoria do StrategyEngine
            matchup_context: Contexto do confronto
            
        Returns:
            Dict com narrativas formatadas por categoria
        """
        formatted_narratives = {}
        
        for category, recommendations in strategy_recommendations.items():
            if not recommendations:
                formatted_narratives[category] = self._format_empty_narrative(category)
                continue
            
            # Formatar narrativa principal da categoria
            narrative = self._format_category_narrative(
                category=category,
                recommendations=recommendations,
                matchup_context=matchup_context
            )
            
            # Formar narrativas individuais dos jogadores
            player_narratives = []
            for rec in recommendations:
                player_narrative = self._format_player_narrative(rec, category, matchup_context)
                player_narratives.append(player_narrative)
            
            # Combinar tudo
            formatted_narratives[category] = {
                "overview": narrative,
                "players": player_narratives,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "recommendation_count": len(recommendations),
                "color": self.color_codes.get(category, "#000000")
            }
        
        return formatted_narratives
    
    def _format_category_narrative(self, category: str, recommendations: List, 
                                  matchup_context: Dict) -> Dict:
        """Formata a narrativa geral de uma categoria."""
        template = self.templates[category]
        
        # Calcular métricas agregadas
        avg_confidence = sum(r.get('confidence', 0) for r in recommendations) / len(recommendations)
        teams = set(r.get('team', '') for r in recommendations)
        positions = [r.get('position', '') for r in recommendations]
        
        # Estatísticas resumidas
        total_pra = sum(r.get('stats', {}).get('pra_avg', 0) for r in recommendations)
        avg_pra = total_pra / len(recommendations)
        
        # Contexto do matchup para inserir na narrativa
        matchup_summary = self._format_matchup_summary(matchup_context)
        
        narrative_text = f"""
# {template['title']}
*{template['subtitle']}*

---

## 📋 Visão Geral
{template['introduction']}

**Matchup Atual:** {matchup_summary}

**Composição da Estratégia:**
- 🔢 **{len(recommendations)} jogadores** selecionados
- 🎯 **Confiança média:** {avg_confidence:.1%}
- 🏀 **PRA médio projetado:** {avg_pra:.1f}
- 🏆 **Times representados:** {', '.join(sorted(teams))}
- 🎮 **Posições:** {', '.join(sorted(set(positions)))}

## 🎯 Recomendações
"""
        
        return {
            "text": narrative_text,
            "metrics": {
                "avg_confidence": avg_confidence,
                "team_diversity": len(teams),
                "avg_pra": avg_pra,
                "player_count": len(recommendations)
            },
            "matchup_context": matchup_summary
        }
    
    def _format_player_narrative(self, player_data: Dict, category: str, 
                                matchup_context: Dict) -> Dict:
        """Formata narrativa individual para um jogador."""
        template = self.templates[category]
        
        # Extrair dados do jogador
        name = player_data.get('name', 'N/A')
        position = player_data.get('position', 'N/A')
        team = player_data.get('team', 'N/A')
        confidence = player_data.get('confidence', 0) * 100
        
        # Processar tese primária
        primary_thesis = player_data.get('primary_thesis', 'Sem tese identificada')
        motives = self._extract_motives(player_data.get('theses', []))
        
        # Preparar dados específicos por categoria
        formatted_data = {
            "name": name,
            "position": position,
            "team": team,
            "confidence": f"{confidence:.0f}",
            "primary_thesis": primary_thesis,
            "motives": motives
        }
        
        # Adicionar campos específicos por categoria
        if category == "conservadora":
            formatted_data.update(self._format_conservadora_fields(player_data, matchup_context))
        elif category == "ousada":
            formatted_data.update(self._format_ousada_fields(player_data, matchup_context))
        elif category == "banco":
            formatted_data.update(self._format_banco_fields(player_data, matchup_context))
        elif category == "explosao":
            formatted_data.update(self._format_explosao_fields(player_data, matchup_context))
        
        # Gerar texto da narrativa
        narrative_text = template["player_template"].format(**formatted_data)
        
        # Adicionar identificadores únicos
        player_id = player_data.get('player_id', '')
        
        return {
            "id": player_id,
            "name": name,
            "position": position,
            "team": team,
            "narrative": narrative_text,
            "confidence": confidence,
            "stats": player_data.get('stats', {}),
            "raw_data": player_data  # Manter dados originais para referência
        }
    
    def _format_conservadora_fields(self, player_data: Dict, context: Dict) -> Dict:
        """Campos específicos para estratégia conservadora."""
        stats = player_data.get('stats', {})
        
        # Resumo estatístico
        stats_summary = f"{stats.get('pts_avg', 0):.1f} PTS, {stats.get('reb_avg', 0):.1f} REB, {stats.get('ast_avg', 0):.1f} AST"
        
        # Evidências adicionais
        evidence = player_data.get('evidence', {})
        matchup_info = evidence.get('matchup', {})
        dvp_rank = matchup_info.get('dvp_rank', 'N/A')
        
        additional = []
        if dvp_rank != 'N/A':
            additional.append(f"DvP Rank: {dvp_rank}")
        
        role_factors = evidence.get('role_factors', {})
        minutes_proj = role_factors.get('minutes_proj', 0)
        if minutes_proj > 30:
            additional.append(f"Minutos projetados: {minutes_proj:.0f}+")
        
        return {
            "stats_summary": stats_summary,
            "additional_evidence": "; ".join(additional) if additional else "Matchup favorável confirmado"
        }
    
    def _format_ousada_fields(self, player_data: Dict, context: Dict) -> Dict:
        """Campos específicos para estratégia ousada."""
        # Calcular score de potencial
        upside_factors = []
        
        stats = player_data.get('stats', {})
        pra_avg = stats.get('pts_avg', 0) + stats.get('reb_avg', 0) + stats.get('ast_avg', 0)
        
        if pra_avg > 35:
            upside_factors.append("PRA histórico alto")
        
        evidence = player_data.get('evidence', {})
        situational = evidence.get('situational', {})
        
        if situational.get('pace_boost', False):
            upside_factors.append("Ritmo acelerado")
        
        if situational.get('injury_boost', False):
            upside_factors.append("Oportunidade por lesão")
        
        # Projeção otimista (20% acima da média)
        optimistic_pts = stats.get('pts_avg', 0) * 1.2
        optimistic_reb = stats.get('reb_avg', 0) * 1.2
        optimistic_ast = stats.get('ast_avg', 0) * 1.2
        
        # Riscos
        risks = []
        if player_data.get('role') != 'starter':
            risks.append("Variação de minutos")
        
        blowout_risk = situational.get('blowout_risk', False)
        if blowout_risk:
            risks.append("Risco de blowout")
        
        return {
            "upside_score": min(len(upside_factors) * 2, 10),
            "explosion_factors": ", ".join(upside_factors) if upside_factors else "Consistência acima da média",
            "optimistic_projection": f"{optimistic_pts:.1f} PTS, {optimistic_reb:.1f} REB, {optimistic_ast:.1f} AST",
            "risks": ", ".join(risks) if risks else "Risco moderado"
        }
    
    def _format_banco_fields(self, player_data: Dict, context: Dict) -> Dict:
        """Campos específicos para estratégia banco."""
        stats = player_data.get('stats', {})
        pra_avg = stats.get('pts_avg', 0) + stats.get('reb_avg', 0) + stats.get('ast_avg', 0)
        
        # Estatísticas por minuto
        minutes_avg = player_data.get('minutes_avg', 30)
        if minutes_avg > 0:
            pts_per_min = stats.get('pts_avg', 0) / minutes_avg
            reb_per_min = stats.get('reb_avg', 0) / minutes_avg
            ast_per_min = stats.get('ast_avg', 0) / minutes_avg
        else:
            pts_per_min = reb_per_min = ast_per_min = 0
        
        # Contexto de oportunidade
        opportunity = []
        role = player_data.get('role', '')
        
        if role in ['bench', 'rotation']:
            opportunity.append("Papel de reserva com minutos garantidos")
        
        evidence = player_data.get('evidence', {})
        situational = evidence.get('situational', {})
        
        if situational.get('blowout_risk', False):
            opportunity.append("Potencial garbage time")
        
        # Razão custo-benefício (simplificada)
        value_ratio = "Alta" if pra_avg > 20 and role in ['bench', 'rotation'] else "Média"
        
        return {
            "value_score": min(int(pra_avg / 3), 10),  # Score baseado no PRA
            "per_minute_stats": f"{pts_per_min:.2f} PTS/min, {reb_per_min:.2f} REB/min, {ast_per_min:.2f} AST/min",
            "opportunity_context": "; ".join(opportunity) if opportunity else "Papel definido na rotação",
            "value_ratio": value_ratio
        }
    
    def _format_explosao_fields(self, player_data: Dict, context: Dict) -> Dict:
        """Campos específicos para estratégia explosão."""
        # Fatores situacionais
        situational_factors = []
        
        evidence = player_data.get('evidence', {})
        situational = evidence.get('situational', {})
        
        if situational.get('injury_boost', False):
            situational_factors.append("Lesões no mesmo posição")
        
        if situational.get('pace_boost', False):
            situational_factors.append("Ritmo extremamente alto")
        
        # Elemento surpresa
        surprise_elements = []
        role = player_data.get('role', '')
        
        if role not in ['starter', 'rotation']:
            surprise_elements.append("Minutos inesperados")
        
        # Projeção no cenário ideal
        stats = player_data.get('stats', {})
        best_case_pts = stats.get('pts_avg', 0) * 1.4
        best_case_reb = stats.get('reb_avg', 0) * 1.4
        best_case_ast = stats.get('ast_avg', 0) * 1.4
        
        # Score de impacto
        impact_score = min(len(situational_factors) * 3 + len(surprise_elements) * 2, 10)
        
        return {
            "impact_score": impact_score,
            "situational_factors": ", ".join(situational_factors) if situational_factors else "Contexto favorável",
            "surprise_element": ", ".join(surprise_elements) if surprise_elements else "Potencial de minuto aumentado",
            "best_case": f"{best_case_pts:.1f}+ PTS, {best_case_reb:.1f}+ REB, {best_case_ast:.1f}+ AST"
        }
    
    def _extract_motives(self, theses: List) -> str:
        """Extrai motivos das teses aplicadas."""
        if not theses:
            return "Matchup favorável identificado"
        
        motives = []
        for thesis in theses:
            thesis_motives = thesis.get('motives', [])
            if isinstance(thesis_motives, list):
                motives.extend(thesis_motives)
            elif isinstance(thesis_motives, str):
                motives.append(thesis_motives)
        
        # Remover duplicados e limitar
        unique_motives = list(dict.fromkeys(motives))[:3]
        return "; ".join(unique_motives)
    
    def _format_matchup_summary(self, matchup_context: Dict) -> str:
        """Formata resumo do matchup para narrativas."""
        if not matchup_context:
            return "Dados do matchup não disponíveis"
        
        parts = []
        
        home = matchup_context.get('home_team', '')
        away = matchup_context.get('away_team', '')
        if home and away:
            parts.append(f"{home} vs {away}")
        
        pace = matchup_context.get('pace', 0)
        if pace:
            pace_label = "⚡ RÁPIDO" if pace >= 110 else "🐢 LENTO" if pace <= 95 else "⚖️ MÉDIO"
            parts.append(f"Ritmo: {pace} ({pace_label})")
        
        spread = matchup_context.get('spread', 0)
        if spread:
            favorite = home if spread < 0 else away
            parts.append(f"Favorito: {favorite} ({abs(spread):.1f})")
        
        total = matchup_context.get('total', 0)
        if total:
            total_label = "ALTO" if total >= 230 else "BAIXO" if total <= 210 else "MÉDIO"
            parts.append(f"Total: {total} ({total_label})")
        
        return " | ".join(parts)
    
    def _format_empty_narrative(self, category: str) -> Dict:
        """Formata narrativa para categoria sem recomendações."""
        template = self.templates[category]
        
        return {
            "overview": {
                "text": f"# {template['title']}\n\n*Nenhuma recomendação disponível para esta estratégia no momento.*\n\n🔍 **Motivo possível:** Os critérios para '{template['subtitle']}' não foram atendidos pelos jogadores disponíveis.",
                "metrics": {
                    "avg_confidence": 0,
                    "team_diversity": 0,
                    "avg_pra": 0,
                    "player_count": 0
                },
                "matchup_context": "N/A"
            },
            "players": [],
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "recommendation_count": 0,
            "color": self.color_codes.get(category, "#000000")
        }
    
    def generate_compact_table(self, category: str, recommendations: List) -> pd.DataFrame:
        """
        Gera tabela compacta para exibição nas abas.
        
        Args:
            category: Categoria da estratégia
            recommendations: Lista de recomendações formatadas
            
        Returns:
            DataFrame com colunas otimizadas para exibição
        """
        if not recommendations:
            return pd.DataFrame()
        
        table_data = []
        for rec in recommendations:
            player_narrative = rec.get('narrative', {})
            
            table_data.append({
                'Jogador': rec.get('name', ''),
                'Pos': rec.get('position', ''),
                'Time': rec.get('team', ''),
                'Conf': f"{rec.get('confidence', 0):.0f}%",
                'Tese': rec.get('raw_data', {}).get('primary_thesis', ''),
                'PRA': rec.get('stats', {}).get('pra_avg', 0),
                'Narrativa': self._summarize_narrative(rec.get('narrative', ''))
            })
        
        df = pd.DataFrame(table_data)
        
        # Ordenar por confiança
        if 'Conf' in df.columns:
            df['Conf_Num'] = df['Conf'].str.replace('%', '').astype(float)
            df = df.sort_values('Conf_Num', ascending=False)
            df = df.drop('Conf_Num', axis=1)
        
        return df
    
    def _summarize_narrative(self, narrative: str, max_length: int = 80) -> str:
        """Resume a narrativa para caber em tabelas."""
        if not narrative:
            return ""
        
        # Extrair primeira sentença ou truncar
        lines = narrative.split('\n')
        for line in lines:
            if line.strip() and not line.startswith('**'):
                summary = line.strip()
                if len(summary) > max_length:
                    summary = summary[:max_length] + "..."
                return summary
        
        return narrative[:max_length] + "..." if len(narrative) > max_length else narrative
    
    def export_to_markdown(self, formatted_narratives: Dict, filename: str = None) -> str:
        """
        Exporta narrativas formatadas para Markdown.
        
        Args:
            formatted_narratives: Narrativas formatadas
            filename: Nome do arquivo (opcional)
            
        Returns:
            String em formato Markdown
        """
        markdown_parts = []
        
        # Cabeçalho
        markdown_parts.append("# 📊 RELATÓRIO DE ESTRATÉGIAS DEEP7\n")
        markdown_parts.append(f"*Gerado em: {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n")
        
        # Resumo executivo
        markdown_parts.append("## 📈 Resumo Executivo\n")
        
        total_recommendations = sum(
            cat_data.get('recommendation_count', 0) 
            for cat_data in formatted_narratives.values()
        )
        
        markdown_parts.append(f"- **Total de recomendações:** {total_recommendations}")
        markdown_parts.append("- **Estratégias ativas:** " + ", ".join([
            f"{cat.capitalize()} ({data.get('recommendation_count', 0)})" 
            for cat, data in formatted_narratives.items() 
            if data.get('recommendation_count', 0) > 0
        ]))
        markdown_parts.append("")
        
        # Narrativa de cada categoria
        for category, data in formatted_narratives.items():
            if data.get('recommendation_count', 0) == 0:
                continue
            
            # Usar a cor para embelezar no markdown (se suportado)
            color_hex = data.get('color', '#000000')
            markdown_parts.append(f"---\n\n## 🎯 {category.upper()}\n")
            
            # Adicionar visão geral
            overview = data.get('overview', {})
            markdown_parts.append(overview.get('text', ''))
            markdown_parts.append("")
            
            # Adicionar jogadores
            markdown_parts.append("### 🏀 Jogadores Recomendados\n")
            
            for i, player in enumerate(data.get('players', []), 1):
                markdown_parts.append(f"#### {i}. {player.get('name', '')} ({player.get('position', '')} - {player.get('team', '')})")
                markdown_parts.append(f"*Confiança: {player.get('confidence', 0):.0f}%*")
                markdown_parts.append("")
                markdown_parts.append(player.get('narrative', ''))
                markdown_parts.append("")
                
                # Estatísticas
                stats = player.get('stats', {})
                if stats:
                    markdown_parts.append(f"**Estatísticas:** {stats.get('pts_avg', 0):.1f} PTS, {stats.get('reb_avg', 0):.1f} REB, {stats.get('ast_avg', 0):.1f} AST")
                    markdown_parts.append("")
                
                markdown_parts.append("---")
                markdown_parts.append("")
        
        markdown_content = "\n".join(markdown_parts)
        
        # Salvar em arquivo se nome fornecido
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(markdown_content)
                logger.info(f"Relatório exportado para: {filename}")
            except Exception as e:
                logger.error(f"Erro ao exportar relatório: {e}")
        
        return markdown_content