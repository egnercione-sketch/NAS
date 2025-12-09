"""
Página do Mapa de Matchups
"""

def show_matchup_map():
    st.header("🗺️ Mapa de Matchups do Dia")
    
    if 'scoreboard' not in st.session_state:
        st.warning("Carregue os dados primeiro")
        return
    
    # Grid de jogos
    games = st.session_state.scoreboard
    cols = st.columns(2)
    
    for idx, game in enumerate(games):
        with cols[idx % 2]:
            show_game_card(game)
    
    # Melhores spots
    st.subheader("🔥 Melhores Oportunidades")
    
    stats = ["PTS", "REB", "AST", "BLK", "STL", "FG3M"]
    for stat in stats:
        with st.expander(f"🎯 {stat}"):
            best_players = find_best_for_stat(stat)
            for player in best_players[:3]:
                st.write(f"**{player['name']}** vs {player['opponent']}")
                st.progress(player['edge'] / 100)