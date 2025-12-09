"""
Página de Projeções Avançadas
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

# Importar módulos existentes
from modules.cache_manager import load_cache, save_cache
from modules.utils import safe_get

def show_projections_page():
    """
    Exibe página de projeções de jogadores com dados avançados
    """
    st.title("📊 Projeções Avançadas")
    
    # Verificar se dados estão carregados
    if 'df_l5' not in st.session_state or st.session_state.df_l5.empty:
        st.warning("⚠️ Carregue os dados na página Dashboard primeiro!")
        return
    
    # Sidebar para configurações
    with st.sidebar:
        st.header("⚙️ Configurações")
        
        # Filtros
        st.subheader("Filtros")
        
        teams = sorted(st.session_state.df_l5['TEAM'].unique())
        selected_teams = st.multiselect(
            "Times",
            teams,
            default=teams[:3] if len(teams) > 3 else teams
        )
        
        positions = sorted(st.session_state.df_l5['POSITION'].unique())
        selected_positions = st.multiselect(
            "Posições",
            positions,
            default=positions
        )
        
        # Configurações de projeção
        st.subheader("Parâmetros")
        
        season_weight = st.slider(
            "Peso da temporada",
            min_value=0.0,
            max_value=1.0,
            value=0.7,
            help="Quanto peso dar para estatísticas da temporada inteira"
        )
        
        recent_weight = 1 - season_weight
        
        # Botão para recalcular
        recalc = st.button("🔄 Recalcular Projeções")
    
    # Container principal
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.subheader("📈 Projeções do Dia")
    
    with col2:
        # Indicador de qualidade
        if 'projection_quality' in st.session_state:
            quality = st.session_state.projection_quality
            color = "🟢" if quality > 80 else "🟡" if quality > 60 else "🔴"
            st.metric("Qualidade", f"{color} {quality}%")
    
    # Filtrar dados
    df_filtered = st.session_state.df_l5.copy()
    
    if selected_teams:
        df_filtered = df_filtered[df_filtered['TEAM'].isin(selected_teams)]
    
    if selected_positions:
        df_filtered = df_filtered[df_filtered['POSITION'].isin(selected_positions)]
    
    # Calcular projeções (simplificado por enquanto)
    projections = calculate_simple_projections(df_filtered, season_weight)
    
    # Exibir tabela de projeções
    show_projections_table(projections)
    
    # Gráficos de comparação
    show_projection_charts(projections)

def calculate_simple_projections(df, season_weight=0.7):
    """
    Calcula projeções simples baseadas nos dados L5
    """
    projections = []
    
    for _, row in df.iterrows():
        player_data = row.to_dict()
        
        # Dados dos últimos 5 jogos (já temos)
        pts_L5 = safe_get(player_data, 'PTS', 0.0)
        reb_L5 = safe_get(player_data, 'REB', 0.0)
        ast_L5 = safe_get(player_data, 'AST', 0.0)
        min_L5 = safe_get(player_data, 'MIN', 0.0)
        
        # Para esta versão inicial, usamos apenas L5
        # Em versões futuras, buscaríamos dados da temporada
        
        # Projeção simples (L5 * fator de ajuste)
        projection_factor = 1.0  # Fator neutro inicialmente
        
        proj = {
            'PLAYER': safe_get(player_data, 'PLAYER', ''),
            'TEAM': safe_get(player_data, 'TEAM', ''),
            'POSITION': safe_get(player_data, 'POSITION', ''),
            'MIN_L5': min_L5,
            'PTS_L5': pts_L5,
            'REB_L5': reb_L5,
            'AST_L5': ast_L5,
            'PRA_L5': pts_L5 + reb_L5 + ast_L5,
            
            # Projeções (inicialmente iguais ao L5)
            'MIN_PROJ': min_L5 * projection_factor,
            'PTS_PROJ': pts_L5 * projection_factor,
            'REB_PROJ': reb_L5 * projection_factor,
            'AST_PROJ': ast_L5 * projection_factor,
            'PRA_PROJ': (pts_L5 + reb_L5 + ast_L5) * projection_factor,
            
            # Volatilidade (simplificada)
            'VOLATILITY': calculate_volatility(player_data),
            'CONFIDENCE': calculate_confidence(player_data)
        }
        
        projections.append(proj)
    
    return pd.DataFrame(projections)

def calculate_volatility(player_data):
    """
    Calcula volatilidade baseada na consistência
    """
    # Simplificado: menor volatilidade para mais jogos
    games_played = safe_get(player_data, 'GP', 5)
    if games_played >= 5:
        return 0.3  # Baixa volatilidade
    elif games_played >= 3:
        return 0.6  # Média volatilidade
    else:
        return 0.8  # Alta volatilidade

def calculate_confidence(player_data):
    """
    Calcula confiança na projeção
    """
    min_L5 = safe_get(player_data, 'MIN', 0.0)
    
    if min_L5 >= 30:
        return 0.9  # Alta confiança
    elif min_L5 >= 20:
        return 0.7  # Média confiança
    elif min_L5 >= 10:
        return 0.5  # Baixa confiança
    else:
        return 0.3  # Muito baixa confiança

def show_projections_table(df_projections):
    """
    Exibe tabela de projeções com formatação
    """
    # Selecionar colunas para exibir
    display_cols = [
        'PLAYER', 'TEAM', 'POSITION',
        'MIN_PROJ', 'PTS_PROJ', 'REB_PROJ', 'AST_PROJ', 'PRA_PROJ',
        'VOLATILITY', 'CONFIDENCE'
    ]
    
    # Verificar quais colunas existem
    available_cols = [col for col in display_cols if col in df_projections.columns]
    
    if not available_cols:
        st.warning("Nenhuma coluna de projeção disponível")
        return
    
    df_display = df_projections[available_cols].copy()
    
    # Renomear colunas para português
    rename_map = {
        'PLAYER': 'Jogador',
        'TEAM': 'Time',
        'POSITION': 'Posição',
        'MIN_PROJ': 'Min Proj',
        'PTS_PROJ': 'PTS Proj',
        'REB_PROJ': 'REB Proj',
        'AST_PROJ': 'AST Proj',
        'PRA_PROJ': 'PRA Proj',
        'VOLATILITY': 'Volatilidade',
        'CONFIDENCE': 'Confiança'
    }
    
    df_display.rename(columns=rename_map, inplace=True)
    
    # Formatar números
    for col in ['Min Proj', 'PTS Proj', 'REB Proj', 'AST Proj', 'PRA Proj']:
        if col in df_display.columns:
            df_display[col] = df_display[col].round(1)
    
    for col in ['Volatilidade', 'Confiança']:
        if col in df_display.columns:
            df_display[col] = df_display[col].round(2)
    
    # Exibir tabela
    st.dataframe(
        df_display,
        use_container_width=True,
        height=600
    )
    
    # Opção de download
    csv = df_display.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download CSV",
        data=csv,
        file_name=f"projecoes_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )

def show_projection_charts(df_projections):
    """
    Exibe gráficos comparativos
    """
    st.subheader("📊 Análise Comparativa")
    
    # Gráfico 1: Top 10 PTS Proj
    if 'PTS_PROJ' in df_projections.columns:
        top_scorers = df_projections.nlargest(10, 'PTS_PROJ')
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Top 10 Projeção de Pontos**")
            for _, row in top_scorers.iterrows():
                player_name = safe_get(row, 'PLAYER', '')
                pts_proj = safe_get(row, 'PTS_PROJ', 0)
                pts_l5 = safe_get(row, 'PTS_L5', 0)
                
                delta = pts_proj - pts_l5
                st.metric(
                    player_name,
                    f"{pts_proj:.1f}",
                    delta=f"{delta:+.1f}"
                )
    
    # Gráfico 2: Top 10 PRA Proj
    if 'PRA_PROJ' in df_projections.columns:
        top_pra = df_projections.nlargest(10, 'PRA_PROJ')
        
        with col2:
            st.markdown("**Top 10 Projeção PRA**")
            for _, row in top_pra.iterrows():
                player_name = safe_get(row, 'PLAYER', '')
                pra_proj = safe_get(row, 'PRA_PROJ', 0)
                pra_l5 = safe_get(row, 'PRA_L5', 0)
                
                delta = pra_proj - pra_l5
                st.metric(
                    player_name,
                    f"{pra_proj:.1f}",
                    delta=f"{delta:+.1f}"
                )

if __name__ == "__main__":
    show_projections_page()