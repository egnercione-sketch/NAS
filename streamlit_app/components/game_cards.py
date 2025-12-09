"""
Componentes para cards de jogos
"""

def show_game_card(game_data):
    """Card para exibir informações de um jogo"""
    with st.container():
        st.markdown(f"### {game_data['home_team']} vs {game_data['away_team']}")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Spread", f"{game_data.get('spread', 'N/A')}")
        
        with col2:
            st.metric("Total", f"{game_data.get('total', 'N/A')}")
        
        with col3:
            pace = game_data.get('pace', 0)
            color = "🟢" if pace > 100 else "🟡" if pace > 95 else "🔴"
            st.metric("Pace", f"{color} {pace}")
        
        # Botões de ação
        if st.button("Ver Detalhes", key=f"details_{game_data['game_id']}"):
            show_game_details(game_data)