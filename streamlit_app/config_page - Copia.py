def show_enhanced_features_config():
    """Interface para ativar/desativar features"""
    st.subheader("🧪 Sistema Avançado (FASE 1)")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        pace_adj = st.checkbox(
            "🎯 Pace Adjuster", 
            value=st.session_state.get("use_pace_adjuster", True),
            help="Ajusta estatísticas baseado no ritmo do jogo"
        )
    
    with col2:
        vacuum_matrix = st.checkbox(
            "⚡ Vacuum Matrix", 
            value=st.session_state.get("use_vacuum_matrix", True),
            help="Detecta boost quando titulares estão ausentes"
        )
    
    with col3:
        correlation_filters = st.checkbox(
            "🛡️ Correlation Filters", 
            value=st.session_state.get("use_correlation_filters", True),
            help="Filtra combinações ruins automaticamente"
        )
    
    if st.button("💾 Aplicar Configurações Avançadas"):
        st.session_state.use_pace_adjuster = pace_adj
        st.session_state.use_vacuum_matrix = vacuum_matrix
        st.session_state.use_correlation_filters = correlation_filters
        st.success("Configurações avançadas salvas!")
    
    # Estatísticas
    if st.session_state.get("enhanced_trixies_generated", 0) > 0:
        st.info(f"""
        **📊 Estatísticas do Sistema Avançado:**
        - Trixies geradas: {st.session_state.enhanced_trixies_generated}
        - Taxa de filtragem: {st.session_state.filter_rate:.1%}
        - Score médio aumento: {st.session_state.avg_score_boost:.1%}
        """)