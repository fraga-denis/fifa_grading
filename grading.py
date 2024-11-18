import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime

# Load Firebase credentials from Streamlit secrets
firebase_key = dict(st.secrets["firebase_key"])  # Ensure it's converted to a dict

# Initialize Firebase Firestore
if not firebase_admin._apps:
    cred = credentials.Certificate(firebase_key)
    firebase_admin.initialize_app(cred)

db = firestore.client()

def load_match_players(week_number):
    try:
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
    except Exception as e:
        st.error(f"Error loading players: {e}")
        return []

def save_grades(week_number, grading_data):
    try:
        for grade in grading_data:
            db.collection("grades").add({
                "week": week_number,
                "player_name": grade["name"],
                "stamina": grade["stamina"],
                "teamwork": grade["teamwork"],
                "attacking": grade["attacking"],
                "defending": grade["defending"]
            })
        st.success("Grades saved successfully!")
    except Exception as e:
        st.error(f"Error saving grades: {e}")

def post_match_grading():
    st.header("Post-Match Grading")

    week_number = datetime.now().isocalendar()[1]
    st.write(f"Grading for Week: {week_number}")

    players = load_match_players(week_number)

    if not players:
        st.warning("No players found for the current match.")
        return

    grading_data = []

    with st.form("Grading Form"):
        for player in players:
            st.subheader(player["name"])
            stamina = st.number_input(
                f"Stamina ({player['name']})", 0.0, 10.0,
                min(max(player["stamina"] * 2, 0), 10), 0.1,
                key=f"{player['id']}_stamina"
            )
            teamwork = st.number_input(
                f"Teamwork ({player['name']})", 0.0, 10.0,
                min(max(player["teamwork"] * 2, 0), 10), 0.1,
                key=f"{player['id']}_teamwork"
            )
            attacking = st.number_input(
                f"Attacking ({player['name']})", 0.0, 10.0,
                min(max(player["attacking"] * 2, 0), 10), 0.1,
                key=f"{player['id']}_attacking"
            )
            defending = st.number_input(
                f"Defending ({player['name']})", 0.0, 10.0,
                min(max(player["defending"] * 2, 0), 10), 0.1,
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

        submitted = st.form_submit_button("Submit Grades")
        if submitted:
            save_grades(week_number, grading_data)

def main():
    st.title("Player Grading App")
    post_match_grading()

if __name__ == "__main__":
    main()
