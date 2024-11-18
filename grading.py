import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime

# Initialize Firebase Firestore
if not firebase_admin._apps:  # Ensure Firebase is initialized only once
    cred = credentials.Certificate("dbkey2.json")  # Path to your Firebase service account key
    firebase_admin.initialize_app(cred)
db = firestore.client()

# Load players participating in the current match for a specific week
def load_match_players(week_number):
    matches_ref = db.collection("matches").where("week", "==", week_number)
    match_docs = matches_ref.stream()
    match_players = [doc.to_dict()["player_name"] for doc in match_docs]

    players_ref = db.collection("players")
    players = players_ref.stream()
    player_data = []
    for player in players:
        player_dict = player.to_dict()
        if player_dict["name"] in match_players:
            player_data.append({
                "id": player.id,
                "name": player_dict["name"],
                "stamina": player_dict.get("stamina", 0),
                "teamwork": player_dict.get("teamwork", 0),
                "attacking": player_dict.get("attacking", 0),
                "defending": player_dict.get("defending", 0),
            })
    return player_data

# Save grades submitted by users
def save_grades(week_number, grading_data):
    for grade in grading_data:
        db.collection("grades").add({
            "week": week_number,
            "player_name": grade["name"],
            "stamina": grade["stamina"],
            "teamwork": grade["teamwork"],
            "attacking": grade["attacking"],
            "defending": grade["defending"]
        })

# Grading session logic
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

    # Create a single form for all players
    with st.form("Grading Form"):
        for player in players:
            st.subheader(player["name"])

            # Display grading inputs
            stamina = st.number_input(
                f"Stamina ({player['name']})",
                min_value=0.0,
                max_value=10.0,
                value=min(max(player["stamina"] * 2, 0), 10),
                step=0.1,
                key=f"{player['id']}_stamina"
            )
            teamwork = st.number_input(
                f"Teamwork ({player['name']})",
                min_value=0.0,
                max_value=10.0,
                value=min(max(player["teamwork"] * 2, 0), 10),
                step=0.1,
                key=f"{player['id']}_teamwork"
            )
            attacking = st.number_input(
                f"Attacking ({player['name']})",
                min_value=0.0,
                max_value=10.0,
                value=min(max(player["attacking"] * 2, 0), 10),
                step=0.1,
                key=f"{player['id']}_attacking"
            )
            defending = st.number_input(
                f"Defending ({player['name']})",
                min_value=0.0,
                max_value=10.0,
                value=min(max(player["defending"] * 2, 0), 10),
                step=0.1,
                key=f"{player['id']}_defending"
            )

            # Collect grading data for this player
            grading_data.append({
                "id": player["id"],
                "name": player["name"],
                "stamina": stamina,
                "teamwork": teamwork,
                "attacking": attacking,
                "defending": defending
            })

        # Single submission for all grades
        submitted = st.form_submit_button("Submit Grades")
        if submitted:
            save_grades(week_number, grading_data)
            st.success("Grades submitted successfully!")

# Main application logic
def main():
    st.title("Player Grading App")
    post_match_grading()

if __name__ == "__main__":
    main()
