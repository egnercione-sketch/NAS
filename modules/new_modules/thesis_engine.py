# modules/new_modules/thesis_engine.py
"""
Motor de Teses Declarativas para NBA Betting Analytics
Gera hipóteses por jogador/mercado com confiança e motivos explícitos
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any

class ThesisEngine:
    """
    Engine que gera teses estratégicas para jogadores baseadas em:
    - Perfil do jogador (posição, role, classificação)
    - Contexto do jogo (pace, spread, DvP)
    - Dados históricos e situacionais
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """Inicializa o motor de teses com configurações"""
        self.config = config or {}
        
        # Multiplicadores de confiança por tipo de tese
        self.confidence_multipliers = {
            'BigRebound': 1.0,
            'AssistMatchup': 1.0,
            'ScorerLine': 1.0,
            'ValueHunter': 0.9,  # Mais conservador para bench
            'PaceBoost': 0.85,
            'BlowoutRisk': 0.8,
        }
        
        # Pesos para cálculo de confiança
        self.weights = {
            'DvP': 0.3,
            'Pace': 0.2,
            'Role': 0.15,
            'PlayerClass': 0.2,
            'Usage': 0.15
        }
        
        # Overrides manuais de posição (exemplo)
        self.position_overrides = {
            'LeBron James': 'SF',
            'Nikola Jokic': 'C',
            'Luka Doncic': 'PG',
            'Giannis Antetokounmpo': 'PF'
        }
        
        # Thresholds
        self.thresholds = {
            'high_pace': 100,  # Pace > 100 é considerado alto
            'big_spread': 12,  # Spread > 12 é considerado blowout risk
            'low_dvp': 0.95,   # DvP < 0.95 é favorável
            'high_dvp': 1.05,  # DvP > 1.05 é desfavorável
            'min_usage': 18,   # Uso mínimo para considerar
            'starter_min': 25  # Minutos mínimos para starter
        }
    
    def get_player_position(self, player_name: str, default_pos: str) -> str:
        """Retorna posição do jogador com overrides manuais"""
        return self.position_overrides.get(player_name, default_pos)
    
    def classify_role(self, min_avg: float, is_starter: bool) -> str:
        """Classifica o role do jogador baseado em minutos e titularidade"""
        if is_starter and min_avg >= self.thresholds['starter_min']:
            return 'starter'
        elif min_avg >= 20:
            return 'rotation'
        elif min_avg >= 12:
            return 'bench'
        else:
            return 'deep_bench'
    
    def calculate_dvp_factor(self, dvp_value: float, is_favorable: bool = True) -> float:
        """Calcula fator DvP para confiança"""
        if pd.isna(dvp_value):
            return 1.0
        
        if is_favorable:
            # DvP baixo (< 1.0) é favorável para defensor
            # Para atacante, queremos DvP alto (> 1.0)
            if dvp_value > 1.0:
                return 1.0 + (dvp_value - 1.0) * 0.3
            else:
                return 0.7 + dvp_value * 0.3
        else:
            if dvp_value < 1.0:
                return 0.7 + dvp_value * 0.3
            else:
                return 1.0 + (dvp_value - 1.0) * 0.3
    
    def generate_big_rebound_thesis(self, player_ctx: Dict, game_ctx: Dict) -> Optional[Dict]:
        """
        Gera tese BigRebound: PF/C + GLASS_BANGER + DvP favorável garrafão + pace alto
        """
        pos = self.get_player_position(player_ctx['name'], player_ctx.get('pos', ''))
        
        # Verifica elegibilidade
        if pos not in ['PF', 'C']:
            return None
        
        # Verifica player class
        player_class = player_ctx.get('player_class', '')
        if 'GLASS_BANGER' not in player_class and 'REBOUNDER' not in player_class:
            return None
        
        # Coleta evidências
        evidences = []
        confidence_factors = []
        
        # 1. DvP para rebotes
        dvp_reb = player_ctx.get('dvp_reb', 1.0)
        dvp_factor = self.calculate_dvp_factor(dvp_reb, is_favorable=True)
        if dvp_reb > 1.0:
            evidences.append(f"DvP REB favorável: {dvp_reb:.2f}")
            confidence_factors.append(('DvP', dvp_factor))
        
        # 2. Pace do jogo
        pace = game_ctx.get('pace', 100)
        if pace > self.thresholds['high_pace']:
            pace_factor = 1.0 + (pace - 100) * 0.01
            evidences.append(f"Pace alto: {pace:.1f}")
            confidence_factors.append(('Pace', min(pace_factor, 1.3)))
        
        # 3. Role do jogador
        role = player_ctx.get('role', 'bench')
        role_factor = 1.0 if role == 'starter' else 0.9
        evidences.append(f"Role: {role}")
        confidence_factors.append(('Role', role_factor))
        
        # 4. Player class
        class_factor = 1.2 if 'GLASS_BANGER' in player_class else 1.0
        confidence_factors.append(('PlayerClass', class_factor))
        
        # 5. Usage rate
        usage = player_ctx.get('usg', 0.0)
        if usage > self.thresholds['min_usage']:
            usage_factor = 1.0 + (usage - 18) * 0.01
            confidence_factors.append(('Usage', min(usage_factor, 1.2)))
            evidences.append(f"USG% adequado: {usage:.1f}%")
        
        # Calcula confiança final
        if not confidence_factors:
            return None
        
        # Média ponderada
        base_confidence = 0.5
        for factor_type, value in confidence_factors:
            if factor_type in self.weights:
                base_confidence += (value - 1.0) * self.weights[factor_type]
        
        # Aplica multiplicador da tese
        confidence = min(max(base_confidence * self.confidence_multipliers['BigRebound'], 0), 1)
        
        return {
            'player': player_ctx['name'],
            'player_id': player_ctx.get('id', ''),
            'market': 'REB',
            'confidence': round(confidence, 2),
            'reason': f"{player_ctx['name']} como {pos} com perfil {player_class} em matchup favorável para rebotes",
            'evidences': evidences,
            'weights': {k: v for k, v in confidence_factors},
            'thesis_type': 'BigRebound',
            'suggested_line': self.suggest_rebound_line(player_ctx)
        }
    
    def generate_assist_matchup_thesis(self, player_ctx: Dict, game_ctx: Dict) -> Optional[Dict]:
        """
        Gera tese AssistMatchup: PG/FLOOR_GENERAL + jogo parelho + AST% alto
        """
        pos = self.get_player_position(player_ctx['name'], player_ctx.get('pos', ''))
        
        # Verifica elegibilidade
        if pos not in ['PG', 'SG']:
            return None
        
        # Verifica player class
        player_class = player_ctx.get('player_class', '')
        if 'FLOOR_GENERAL' not in player_class and 'PLAYMAKER' not in player_class:
            return None
        
        # Coleta evidências
        evidences = []
        confidence_factors = []
        
        # 1. Spread do jogo (jogo parelho)
        spread = abs(game_ctx.get('spread', 0))
        if spread <= 5:
            spread_factor = 1.2
            evidences.append(f"Jogo parelho (spread: {spread})")
        elif spread <= 8:
            spread_factor = 1.0
            evidences.append(f"Spread moderado: {spread}")
        else:
            spread_factor = 0.8
            evidences.append(f"Spread alto: {spread}")
        confidence_factors.append(('GameContext', spread_factor))
        
        # 2. AST% do jogador
        ast_pct = player_ctx.get('ast_pct', 0.0)
        if ast_pct > 20:
            ast_factor = 1.0 + (ast_pct - 20) * 0.01
            confidence_factors.append(('PlayerClass', min(ast_factor, 1.3)))
            evidences.append(f"AST% alto: {ast_pct:.1f}%")
        
        # 3. DvP para assistências
        dvp_ast = player_ctx.get('dvp_ast', 1.0)
        dvp_factor = self.calculate_dvp_factor(dvp_ast, is_favorable=True)
        if dvp_ast > 1.0:
            evidences.append(f"DvP AST favorável: {dvp_ast:.2f}")
            confidence_factors.append(('DvP', dvp_factor))
        
        # 4. Role
        role = player_ctx.get('role', 'bench')
        role_factor = 1.1 if role == 'starter' else 0.9
        confidence_factors.append(('Role', role_factor))
        
        # Calcula confiança
        if not confidence_factors:
            return None
        
        base_confidence = 0.5
        for factor_type, value in confidence_factors:
            if factor_type in self.weights:
                base_confidence += (value - 1.0) * self.weights.get(factor_type, 0.1)
        
        confidence = min(max(base_confidence * self.confidence_multipliers['AssistMatchup'], 0), 1)
        
        return {
            'player': player_ctx['name'],
            'player_id': player_ctx.get('id', ''),
            'market': 'AST',
            'confidence': round(confidence, 2),
            'reason': f"{player_ctx['name']} como {pos} com alto AST% em jogo competitivo",
            'evidences': evidences,
            'weights': {k: v for k, v in confidence_factors},
            'thesis_type': 'AssistMatchup',
            'suggested_line': self.suggest_assist_line(player_ctx)
        }
    
    def generate_scorer_line_thesis(self, player_ctx: Dict, game_ctx: Dict) -> Optional[Dict]:
        """
        Gera tese ScorerLine: SG/SF + Volume/Sharpshooter + defesa fraca no perímetro
        """
        pos = self.get_player_position(player_ctx['name'], player_ctx.get('pos', ''))
        
        if pos not in ['SG', 'SF']:
            return None
        
        player_class = player_ctx.get('player_class', '')
        if 'SCORER' not in player_class and 'SHOOTER' not in player_class and 'VOLUME' not in player_class:
            return None
        
        evidences = []
        confidence_factors = []
        
        # 1. DvP para pontos
        dvp_pts = player_ctx.get('dvp_pts', 1.0)
        dvp_factor = self.calculate_dvp_factor(dvp_pts, is_favorable=True)
        if dvp_pts > 1.0:
            evidences.append(f"DvP PTS favorável: {dvp_pts:.2f}")
            confidence_factors.append(('DvP', dvp_factor))
        
        # 2. Usage rate
        usage = player_ctx.get('usg', 0.0)
        if usage > 22:
            usage_factor = 1.0 + (usage - 22) * 0.015
            confidence_factors.append(('Usage', min(usage_factor, 1.3)))
            evidences.append(f"USG% alto: {usage:.1f}%")
        
        # 3. Player class
        class_factor = 1.2 if 'SCORER' in player_class else 1.0
        confidence_factors.append(('PlayerClass', class_factor))
        
        # 4. Total do jogo (over/under)
        total = game_ctx.get('total', 220)
        if total > 225:
            total_factor = 1.1
            evidences.append(f"Total alto: {total}")
        else:
            total_factor = 1.0
        confidence_factors.append(('GameContext', total_factor))
        
        # 5. Eficiência recente
        recent_ppg = player_ctx.get('last_5_ppg', player_ctx.get('ppg', 0))
        season_ppg = player_ctx.get('ppg', 0)
        if recent_ppg > season_ppg * 1.1:
            form_factor = 1.15
            evidences.append(f"Momentum positivo: {recent_ppg:.1f} PPG últimos 5 jogos")
        else:
            form_factor = 1.0
        confidence_factors.append(('Form', form_factor))
        
        # Calcula confiança
        base_confidence = 0.55
        for factor_type, value in confidence_factors:
            if factor_type in self.weights:
                base_confidence += (value - 1.0) * self.weights.get(factor_type, 0.1)
        
        confidence = min(max(base_confidence * self.confidence_multipliers['ScorerLine'], 0), 1)
        
        return {
            'player': player_ctx['name'],
            'player_id': player_ctx.get('id', ''),
            'market': 'PTS',
            'confidence': round(confidence, 2),
            'reason': f"{player_ctx['name']} como {pos} com perfil de scorer contra defesa vulnerável",
            'evidences': evidences,
            'weights': {k: v for k, v in confidence_factors},
            'thesis_type': 'ScorerLine',
            'suggested_line': self.suggest_points_line(player_ctx)
        }
    
    def generate_value_hunter_thesis(self, player_ctx: Dict, game_ctx: Dict) -> Optional[Dict]:
        """
        Gera tese ValueHunter: bench/rotation + bom PRA/min + minutos previstos crescentes
        """
        role = player_ctx.get('role', 'bench')
        
        # Foca em bench/rotation
        if role not in ['bench', 'rotation']:
            return None
        
        # Verifica se tem potencial de minutos
        min_avg = player_ctx.get('min_avg', 0)
        if min_avg < 15:
            return None
        
        evidences = []
        confidence_factors = []
        
        # 1. PRA por minuto
        pra = player_ctx.get('pra', 0)
        pra_per_min = pra / min_avg if min_avg > 0 else 0
        
        if pra_per_min > 0.8:
            pra_factor = 1.0 + (pra_per_min - 0.8) * 0.5
            confidence_factors.append(('Efficiency', min(pra_factor, 1.3)))
            evidences.append(f"PRA/min alto: {pra_per_min:.2f}")
        
        # 2. Tendência de minutos
        last_5_min = player_ctx.get('last_5_min_avg', min_avg)
        if last_5_min > min_avg * 1.1:
            trend_factor = 1.2
            evidences.append(f"Minutos crescentes: {last_5_min:.1f} últimos 5 jogos")
        else:
            trend_factor = 1.0
        confidence_factors.append(('Trend', trend_factor))
        
        # 3. Spread do jogo (possível garbage time)
        spread = abs(game_ctx.get('spread', 0))
        if spread > self.thresholds['big_spread']:
            garbage_factor = 1.15
            evidences.append(f"Spread alto pode gerar garbage time: {spread}")
        else:
            garbage_factor = 1.0
        confidence_factors.append(('GameContext', garbage_factor))
        
        # 4. Player class (bench specialists)
        player_class = player_ctx.get('player_class', '')
        if 'BENCH' in player_class or 'SPARK' in player_class:
            class_factor = 1.15
            evidences.append(f"Perfil de bench specialist")
        else:
            class_factor = 1.0
        confidence_factors.append(('PlayerClass', class_factor))
        
        # Calcula confiança
        base_confidence = 0.45  # Mais baixo por ser bench
        for factor_type, value in confidence_factors:
            base_confidence += (value - 1.0) * 0.2
        
        confidence = min(max(base_confidence * self.confidence_multipliers['ValueHunter'], 0), 1)
        
        return {
            'player': player_ctx['name'],
            'player_id': player_ctx.get('id', ''),
            'market': 'PRA',
            'confidence': round(confidence, 2),
            'reason': f"{player_ctx['name']} ({role}) com bom valor PRA/min e potencial de minutos",
            'evidences': evidences,
            'weights': {k: v for k, v in confidence_factors},
            'thesis_type': 'ValueHunter',
            'suggested_line': self.suggest_pra_line(player_ctx)
        }
    
    def generate_pace_boost_thesis(self, player_ctx: Dict, game_ctx: Dict) -> Optional[Dict]:
        """
        Gera tese PaceBoost: jogadores beneficiados por ritmo acelerado
        """
        pace = game_ctx.get('pace', 100)
        
        # Só ativa se pace for realmente alto
        if pace < self.thresholds['high_pace']:
            return None
        
        player_class = player_ctx.get('player_class', '')
        
        # Tipos de jogadores beneficiados por pace alto
        pace_benefited = ['RUNNER', 'TRANSITION', 'ATHLETIC', 'YOUNG']
        if not any(benefit in player_class for benefit in pace_benefited):
            return None
        
        evidences = []
        confidence_factors = []
        
        # 1. Fator pace
        pace_factor = 1.0 + (pace - 100) * 0.01
        confidence_factors.append(('Pace', min(pace_factor, 1.3)))
        evidences.append(f"Pace muito alto: {pace:.1f}")
        
        # 2. Estatísticas em jogos de pace alto
        # (aqui poderia ter dados históricos, usando placeholder)
        pace_matchup_factor = 1.1
        confidence_factors.append(('Matchup', pace_matchup_factor))
        evidences.append("Perfil beneficiado por jogo rápido")
        
        # 3. Posição (guards e wings se beneficiam mais)
        pos = self.get_player_position(player_ctx['name'], player_ctx.get('pos', ''))
        if pos in ['PG', 'SG']:
            pos_factor = 1.1
        elif pos in ['SF']:
            pos_factor = 1.05
        else:
            pos_factor = 1.0
        confidence_factors.append(('Position', pos_factor))
        
        # Determina mercado mais beneficiado
        if 'PASS' in player_class or 'PLAYMAKER' in player_class:
            market = 'AST'
            suggested_line = self.suggest_assist_line(player_ctx)
        elif 'SCORER' in player_class:
            market = 'PTS'
            suggested_line = self.suggest_points_line(player_ctx)
        else:
            market = 'PRA'
            suggested_line = self.suggest_pra_line(player_ctx)
        
        # Calcula confiança
        base_confidence = 0.5
        for factor_type, value in confidence_factors:
            base_confidence += (value - 1.0) * 0.25
        
        confidence = min(max(base_confidence * self.confidence_multipliers['PaceBoost'], 0), 1)
        
        return {
            'player': player_ctx['name'],
            'player_id': player_ctx.get('id', ''),
            'market': market,
            'confidence': round(confidence, 2),
            'reason': f"{player_ctx['name']} beneficiado pelo pace alto do jogo ({pace})",
            'evidences': evidences,
            'weights': {k: v for k, v in confidence_factors},
            'thesis_type': 'PaceBoost',
            'suggested_line': suggested_line
        }
    
    def generate_blowout_risk_thesis(self, player_ctx: Dict, game_ctx: Dict) -> Optional[Dict]:
        """
        Gera tese BlowoutRisk: penaliza linhas em grande spread
        """
        spread = abs(game_ctx.get('spread', 0))
        
        # Só ativa para spread muito alto
        if spread < self.thresholds['big_spread']:
            return None
        
        # Identifica qual time está perdendo por muito
        player_team = player_ctx.get('team', '')
        home_team = game_ctx.get('home_team', '')
        away_team = game_ctx.get('away_team', '')
        
        # Determina se o jogador está no time underdog
        is_underdog = False
        if player_team == home_team and game_ctx.get('spread', 0) > 0:
            is_underdog = True
        elif player_team == away_team and game_ctx.get('spread', 0) < 0:
            is_underdog = True
        
        evidences = []
        confidence_factors = []
        
        # Penaliza starters em blowout esperado
        role = player_ctx.get('role', 'bench')
        if role == 'starter' and is_underdog:
            risk_factor = 0.7  # Penalidade forte
            evidences.append(f"Starter em time underdog com spread alto")
        elif role == 'starter':
            risk_factor = 0.85
            evidences.append(f"Starter em jogo com blowout esperado")
        elif role in ['bench', 'rotation'] and not is_underdog:
            risk_factor = 1.1  # Bench no time favorito pode se beneficiar
            evidences.append(f"Bench em time favorito pode ter garbage time")
        else:
            risk_factor = 1.0
        
        confidence_factors.append(('BlowoutRisk', risk_factor))
        evidences.append(f"Spread muito alto: {spread}")
        
        # Calcula confiança (esta tese gera penalidades, não recomendações)
        confidence = 0.3  # Baixa confiança para apostar
        
        return {
            'player': player_ctx['name'],
            'player_id': player_ctx.get('id', ''),
            'market': 'RISK',
            'confidence': round(confidence, 2),
            'reason': f"Alerta de blowout risk para {player_ctx['name']} (spread: {spread})",
            'evidences': evidences,
            'weights': {k: v for k, v in confidence_factors},
            'thesis_type': 'BlowoutRisk',
            'suggested_line': None,
            'is_risk': True
        }
    
    # Métodos auxiliares para sugerir linhas
    def suggest_points_line(self, player_ctx: Dict) -> float:
        """Sugere linha de pontos baseado na média e momentum"""
        season_ppg = player_ctx.get('ppg', 0)
        last_5_ppg = player_ctx.get('last_5_ppg', season_ppg)
        recent_form = max(season_ppg, last_5_ppg)
        
        # Ajusta baseado no role
        role = player_ctx.get('role', 'bench')
        if role == 'starter':
            multiplier = 1.0
        elif role == 'rotation':
            multiplier = 0.9
        else:
            multiplier = 0.8
        
        return round(recent_form * multiplier, 1)
    
    def suggest_rebound_line(self, player_ctx: Dict) -> float:
        """Sugere linha de rebotes"""
        season_rpg = player_ctx.get('rpg', 0)
        last_5_rpg = player_ctx.get('last_5_rpg', season_rpg)
        recent_form = max(season_rpg, last_5_rpg)
        
        role = player_ctx.get('role', 'bench')
        if role == 'starter':
            multiplier = 1.0
        elif role == 'rotation':
            multiplier = 0.9
        else:
            multiplier = 0.8
        
        return round(recent_form * multiplier, 1)
    
    def suggest_assist_line(self, player_ctx: Dict) -> float:
        """Sugere linha de assistências"""
        season_apg = player_ctx.get('apg', 0)
        last_5_apg = player_ctx.get('last_5_apg', season_apg)
        recent_form = max(season_apg, last_5_apg)
        
        role = player_ctx.get('role', 'bench')
        if role == 'starter':
            multiplier = 1.0
        elif role == 'rotation':
            multiplier = 0.9
        else:
            multiplier = 0.8
        
        return round(recent_form * multiplier, 1)
    
    def suggest_pra_line(self, player_ctx: Dict) -> float:
        """Sugere linha de PRA"""
        season_pra = player_ctx.get('pra', 0)
        last_5_pra = player_ctx.get('last_5_pra', season_pra)
        recent_form = max(season_pra, last_5_pra)
        
        role = player_ctx.get('role', 'bench')
        if role == 'starter':
            multiplier = 1.0
        elif role == 'rotation':
            multiplier = 0.9
        else:
            multiplier = 0.8
        
        return round(recent_form * multiplier, 1)
    
    def generate_all_theses(self, player_ctx: Dict, game_ctx: Dict) -> List[Dict]:
        """
        Gera todas as teses possíveis para um jogador
        Retorna lista ordenada por confiança
        """
        theses = []
        
        # Gera cada tipo de tese
        thesis_generators = [
            self.generate_big_rebound_thesis,
            self.generate_assist_matchup_thesis,
            self.generate_scorer_line_thesis,
            self.generate_value_hunter_thesis,
            self.generate_pace_boost_thesis,
            self.generate_blowout_risk_thesis
        ]
        
        for generator in thesis_generators:
            thesis = generator(player_ctx, game_ctx)
            if thesis:
                # Filtra teses com confiança muito baixa
                if thesis.get('confidence', 0) > 0.4 or thesis.get('thesis_type') == 'BlowoutRisk':
                    theses.append(thesis)
        
        # Ordena por confiança (decrescente)
        theses.sort(key=lambda x: x['confidence'], reverse=True)
        
        # Limita a 3 teses por jogador
        return theses[:3]
    
    def process_game(self, players_data: List[Dict], game_ctx: Dict) -> Dict[str, List[Dict]]:
        """
        Processa todos os jogadores de um jogo e retorna teses organizadas
        """
        all_theses = {}
        
        for player_ctx in players_data:
            player_name = player_ctx.get('name', 'Unknown')
            player_theses = self.generate_all_theses(player_ctx, game_ctx)
            
            if player_theses:
                all_theses[player_name] = player_theses
        
        return all_theses
    
    def get_thesis_summary(self, theses_data: Dict[str, List[Dict]]) -> pd.DataFrame:
        """
        Retorna resumo das teses em DataFrame para análise
        """
        rows = []
        for player, player_theses in theses_data.items():
            for thesis in player_theses:
                rows.append({
                    'Player': player,
                    'Thesis': thesis['thesis_type'],
                    'Market': thesis['market'],
                    'Confidence': thesis['confidence'],
                    'Reason': thesis['reason'],
                    'Evidences': '; '.join(thesis['evidences']),
                    'Suggested Line': thesis.get('suggested_line', 'N/A')
                })
        
        return pd.DataFrame(rows)


# Função de exemplo para teste
def test_thesis_engine():
    """Testa o motor de teses com dados de exemplo"""
    engine = ThesisEngine()
    
    # Dados de exemplo
    player_ctx = {
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
    }
    
    game_ctx = {
        'home_team': 'MIA',
        'away_team': 'BOS',
        'pace': 102.5,
        'spread': -3.5,
        'total': 225.5
    }
    
    theses = engine.generate_all_theses(player_ctx, game_ctx)
    
    print(f"Teses para {player_ctx['name']}:")
    for thesis in theses:
        print(f"\n{thesis['thesis_type']}:")
        print(f"  Market: {thesis['market']}")
        print(f"  Confidence: {thesis['confidence']}")
        print(f"  Reason: {thesis['reason']}")
        print(f"  Evidences: {', '.join(thesis['evidences'])}")
        print(f"  Suggested Line: {thesis.get('suggested_line', 'N/A')}")
    
    return theses


if __name__ == "__main__":
    # Teste do módulo
    test_thesis_engine()