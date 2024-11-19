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

# Set up default selected week in session state
if "selected_week" not in st.session_state:
    st.session_state["selected_week"] = datetime.now().isocalendar()[1]

# Function to handle week selection with password
def password_protected_week_selection():
    with st.expander("Admin: Update Selected Week"):
        password = st.text_input("Enter Password:", type="password")
        if password == "almighty":  # Change the password to your desired value
            available_weeks = list(range(1, 53))  # Allow selection of weeks 1-52
            selected_week = st.selectbox("Select Week to Grade:", available_weeks, index=st.session_state["selected_week"] - 1)
            if st.button("Update Week"):
                st.session_state["selected_week"] = selected_week
                st.success(f"Week updated to {selected_week}")
        else:
            st.warning("Enter the correct password to update the week.")

def load_match_players(week_number):
    try:
        # Fetch match data for the given week
        matches_ref = db.collection("matches").where("week", "==", week_number)
        match_docs = matches_ref.stream()
        
        player_data = []
        for match in match_docs:
            match_dict = match.to_dict()
            player_data.append({
                "id": match_dict.get("player_id", ""),
                "name": match_dict["player_name"],
                "photo": match_dict.get("photo", ""),
                "stamina": match_dict.get("stamina", 0),
                "teamwork": match_dict.get("teamwork", 0),
                "attacking": match_dict.get("attacking", 0),
                "defending": match_dict.get("defending", 0),
            })
        return player_data
    except Exception as e:
        st.error(f"Error loading match players: {e}")
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
                "defending": grade["defending"],
            })
        st.success("Grades saved successfully!")
    except Exception as e:
        st.error(f"Error saving grades: {e}")

def post_match_grading():
    st.header("Post-Match Grading")

    # Use the selected week from session state
    week_number = st.session_state["selected_week"]
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

            # Validate photo URL as a string
            photo_url = str(player.get("photo", ""))
            if photo_url:  # Display the photo if the path is provided
                st.image(photo_url, caption=player["name"], use_container_width=True)

            # Ensure unique keys for each player input
            unique_key_prefix = f"{player['id']}_{player['name']}"  # Combine `id` and `name` for uniqueness

            # Display numeric inputs for grading
            stamina = st.number_input(
                f"Stamina ({player['name']})", 
                min_value=0.0, max_value=10.0, 
                value=float(min(max(player["stamina"] * 2, 0), 10)), step=0.1,
                key=f"{unique_key_prefix}_stamina"
            )
            teamwork = st.number_input(
                f"Teamwork ({player['name']})", 
                min_value=0.0, max_value=10.0, 
                value=float(min(max(player["teamwork"] * 2, 0), 10)), step=0.1,
                key=f"{unique_key_prefix}_teamwork"
            )
            attacking = st.number_input(
                f"Attacking ({player['name']})", 
                min_value=0.0, max_value=10.0, 
                value=float(min(max(player["attacking"] * 2, 0), 10)), step=0.1,
                key=f"{unique_key_prefix}_attacking"
            )
            defending = st.number_input(
                f"Defending ({player['name']})", 
                min_value=0.0, max_value=10.0, 
                value=float(min(max(player["defending"] * 2, 0), 10)), step=0.1,
                key=f"{unique_key_prefix}_defending"
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


def main():
    st.title("Player Grading App")

    # Password-protected week selection
    password_protected_week_selection()

    # Post-match grading
    post_match_grading()

if __name__ == "__main__":
    main()
