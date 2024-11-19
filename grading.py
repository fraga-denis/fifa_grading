def post_match_grading():
    st.header("Post-Match Grading")

    # Get the current week number
    week_number = datetime.now().isocalendar()[1]
    st.write(f"Grading for Week: {week_number}")

    # Load players for the current match
    players = load_match_players(week_number)

    if not players:
        st.warning("No players found for the current match.")
        return

    grading_data = []

    # Create a single form for grading
    with st.form("Grading Form"):
        for player in players:
            # Show player details
            st.subheader(player["name"])
            if player["photo"]:  # Display the photo if the path is provided
                st.image(player["photo"], caption=player["name"], use_column_width=True)

            # Display numeric inputs for grading
            stamina = st.number_input(
                f"Stamina ({player['name']})", 
                min_value=0.0, max_value=10.0, 
                value=float(min(max(player["stamina"] * 2, 0), 10)), step=0.1,
                key=f"{player['id']}_stamina"
            )
            teamwork = st.number_input(
                f"Teamwork ({player['name']})", 
                min_value=0.0, max_value=10.0, 
                value=float(min(max(player["teamwork"] * 2, 0), 10)), step=0.1,
                key=f"{player['id']}_teamwork"
            )
            attacking = st.number_input(
                f"Attacking ({player['name']})", 
                min_value=0.0, max_value=10.0, 
                value=float(min(max(player["attacking"] * 2, 0), 10)), step=0.1,
                key=f"{player['id']}_attacking"
            )
            defending = st.number_input(
                f"Defending ({player['name']})", 
                min_value=0.0, max_value=10.0, 
                value=float(min(max(player["defending"] * 2, 0), 10)), step=0.1,
                key=f"{player['id']}_defending"
            )

            grading_data.append({
                "id": player["id"],
                "name": player["name"],
                "stamina": stamina,
                "teamwork": teamwork,
                "attacking": attacking,
                "defending": defending,
            })

        # Add a single submit button for the form
        submitted = st.form_submit_button("Submit Grades")
        if submitted:
            save_grades(week_number, grading_data)


    # Create a single form for grading
    with st.form("Grading Form"):
        for player in players:
            # Show player details
            st.subheader(player["name"])
            if player["photo"]:  # Display the photo if the path is provided
                st.image(player["photo"], caption=player["name"], use_column_width=True)

            # Display numeric inputs for grading
            stamina = st.number_input(
                f"Stamina ({player['name']})", 0.0, 10.0,
                float(min(max(player["stamina"] * 2, 0), 10)), 0.1,
                key=f"{player['id']}_stamina"
            )
            teamwork = st.number_input(
                f"Teamwork ({player['name']})", 0.0, 10.0,
                float(min(max(player["teamwork"] * 2, 0), 10)), 0.1,
                key=f"{player['id']}_teamwork"
            )
            attacking = st.number_input(
                f"Attacking ({player['name']})", 0.0, 10.0,
                float(min(max(player["attacking"] * 2, 0), 10)), 0.1,
                key=f"{player['id']}_attacking"
            )
            defending = st.number_input(
                f"Defending ({player['name']})", 0.0, 10.0,
                float(min(max(player["defending"] * 2, 0), 10)), 0.1,
                key=f"{player['id']}_defending"
            )

            grading_data.append({
                "id": player["id"],
                "name": player["name"],
                "stamina": stamina,
                "teamwork": teamwork,
                "attacking": attacking,
                "defending": defending,
            })

        # Add a single submit button for the form
        submitted = st.form_submit_button("Submit Grades")
        if submitted:
            save_grades(week_number, grading_data)
