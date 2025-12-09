"""
Dashboard principal do NBA Analytics Suite
"""

import streamlit as st
from modules.config import *
from modules.utils import *
from modules.data_fetchers import *
from modules.dvp_module import DvPAnalyzer

def show_dashboard():
    st.header("📊 Dashboard")
    
    # Métricas
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        saved_l5 = load_pickle(L5_CACHE_FILE)
        df_cached = saved_l5.get("df") if saved_l5 and isinstance(saved_l5, dict) else pd.DataFrame()
        st.metric("Jogadores L5", len(df_cached))
    
    with col2:
        games = st.session_state.scoreboard or []
        st.metric("Jogos Hoje", len(games))
    
    with col3:
        odds = st.session_state.odds or {}
        st.metric("Confrontos com Odds", len(odds))
    
    with col4:
        injuries_count = 0
        if st.session_state.injuries_data:
            for team_injuries in st.session_state.injuries_data.values():
                injuries_count += len(team_injuries)
        st.metric("Lesionados", injuries_count)
    
    with col5:
        dvp_analyzer = st.session_state.get("dvp_analyzer")
        if dvp_analyzer and dvp_analyzer.defense_data:
            st.metric("Times DvP", len(dvp_analyzer.defense_data))
        else:
            st.metric("Times DvP", 0)
    
    st.markdown("---")
    
    # NOVA SEÇÃO: Status do Sistema
    st.subheader("🛠️ Status do Sistema")
    
    # Validar componentes críticos
    critical_ok, checks = validate_pipeline_integrity(['l5', 'scoreboard', 'odds', 'dvp', 'injuries'])
    
    # Mostrar em colunas
    cols_status = st.columns(5)
    check_keys = ['l5', 'scoreboard', 'odds', 'dvp', 'injuries']
    for idx, key in enumerate(check_keys):
        with cols_status[idx]:
            check = checks[key]
            if check['status']:
                st.success(f"✅ {check['name']}")
            else:
                if check['critical']:
                    st.error(f"❌ {check['name']}")
                else:
                    st.warning(f"⚠️ {check['name']}")
            st.caption(check['message'])
    
    # Se houver problemas críticos, mostrar alerta
    if not critical_ok:
        st.error("⚠️ Sistema com dados incompletos. Algumas funcionalidades podem não estar disponíveis.")
    
    st.markdown("---")
    
    # Jogos do dia
    st.subheader("🎯 Confrontos de Hoje")
    games = st.session_state.scoreboard or []
    odds = st.session_state.odds or {}
    
    if games:
        for i, game in enumerate(games):
            away = game.get("away")
            home = game.get("home")
            status = game.get("status", "Não iniciado")
            
            away_full = TEAM_ABBR_TO_ODDS.get(away, away)
            home_full = TEAM_ABBR_TO_ODDS.get(home, home)
            
            spread = None
            total = None
            if away_full and home_full:
                key_full = f"{away_full}@{home_full}"
                game_odds = odds.get(key_full, {})
                spread = game_odds.get("spread")
                total = game_odds.get("total")
            
            blowout_risk = False
            if spread:
                try:
                    if abs(float(spread)) >= 10:
                        blowout_risk = True
                except:
                    pass
            
            if blowout_risk:
                st.markdown(f'<div class="blowout-card">', unsafe_allow_html=True)
                st.markdown(f"### ⚠️ {away} @ {home} (RISCO DE BLOWOUT)")
            else:
                st.markdown(f'<div class="game-card">', unsafe_allow_html=True)
                st.markdown(f"### {away} @ {home}")
            
            st.write(f"**Status:** {status}")
            
            if spread or total:
                odds_text = []
                if spread:
                    odds_text.append(f"Spread: {spread}")
                if total:
                    odds_text.append(f"Total: {total}")
                st.write(f"**Odds:** {', '.join(odds_text)}")
            
            dvp_analyzer = st.session_state.get("dvp_analyzer")
            if dvp_analyzer and dvp_analyzer.defense_data:
                if away in dvp_analyzer.defense_data or home in dvp_analyzer.defense_data:
                    st.write("**📊 DvP Disponível:** Sim")
            
            st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("Nenhum jogo encontrado para hoje.")
    
    # Estatísticas Rápidas
    st.subheader("📈 Estatísticas Rápidas")
    if not df_cached.empty:
        col_s1, col_s2, col_s3 = st.columns(3)
        
        with col_s1:
            top_scorers = df_cached.nlargest(5, 'PTS_AVG')[['PLAYER', 'PTS_AVG']]
            st.write("**Top Scorers (L5):**")
            st.dataframe(top_scorers.style.format({'PTS_AVG': '{:.1f}'}), use_container_width=True)
        
        with col_s2:
            top_rebounders = df_cached.nlargest(5, 'REB_AVG')[['PLAYER', 'REB_AVG']]
            st.write("**Top Rebounders (L5):**")
            st.dataframe(top_rebounders.style.format({'REB_AVG': '{:.1f}'}), use_container_width=True)
        
        with col_s3:
            top_assisters = df_cached.nlargest(5, 'AST_AVG')[['PLAYER', 'AST_AVG']]
            st.write("**Top Assisters (L5):**")
            st.dataframe(top_assisters.style.format({'AST_AVG': '{:.1f}'}), use_container_width=True)
    
    st.markdown(
        '<div class="footer">NBA Analytics Suite v1.2 • Criado por <span class="highlight">Egner</span> • Assistência IA <span class="highlight">DeepSeek</span></div>',
        unsafe_allow_html=True
    )