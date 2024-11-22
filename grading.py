import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
import cloudinary
import cloudinary.api


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

def get_all_photo_urls():
    """
    Fetch all photo URLs from Cloudinary and adjust `public_id` to match `player_id`.
    
    Returns:
        dict: A dictionary with adjusted `public_id` (matching `player_id`) as keys and `secure_url` as values.
    """
    # Access Cloudinary credentials from Streamlit secrets
    cloudinary_key = st.secrets["cloudinary"]

    # Configure Cloudinary
    cloudinary.config(
        cloud_name=cloudinary_key["cloud_name"],
        api_key=cloudinary_key["api_key"],
        api_secret=cloudinary_key["api_secret"]
    )
    
    try:
        # Fetch all uploaded resources
        response = cloudinary.api.resources(
            type="upload",  # Fetch resources uploaded directly
            max_results=500  # Adjust as needed
        )
        # Adjust `public_id` to match `player_id` by stripping everything after '_'
        photo_map = {resource["public_id"].split('_')[0]: resource["secure_url"] for resource in response["resources"]}
        return photo_map
    except Exception as e:
        print(f"Error fetching photo URLs: {e}")
        return {}
        
def resize_photo_url(photo_url, width, height):
    """
    Resize a Cloudinary photo URL to the specified dimensions.
    
    Args:
        photo_url (str): The original Cloudinary photo URL.
        width (int): Desired width in pixels.
        height (int): Desired height in pixels.
    
    Returns:
        str: The resized Cloudinary photo URL.
    """
    # Insert transformation parameters into the Cloudinary URL
    parts = photo_url.split('/upload/')
    if len(parts) == 2:
        return f"{parts[0]}/upload/w_{width},h_{height},c_fill/{parts[1]}"
    return photo_url  # Return original URL if transformation fails

# Function to handle week selection with password
def password_protected_week_selection():
    if "selected_week" not in st.session_state:
        st.session_state["selected_week"] = datetime.now().isocalendar()[1]  # Default to the current week

    if "week_change_allowed" not in st.session_state:
        st.session_state["week_change_allowed"] = False  # Default to no week change without password

    # Display the currently selected week
    st.subheader(f"Currently Selected Week: {st.session_state['selected_week']}")

    # Check for password to allow week change
    with st.expander("Admin: Update Selected Week"):
        if not st.session_state["week_change_allowed"]:
            password = st.text_input("Enter Password:", type="password")
            if password == "almighty":  # Change the password to your desired value
                st.session_state["week_change_allowed"] = True
                st.success("Access granted. You can now update the week.")
            else:
                st.warning("Enter the correct password to unlock week selection.")

        # Allow week selection if the password is correct
        if st.session_state["week_change_allowed"]:
            available_weeks = list(range(1, 53))  # Allow selection of weeks 1-52
            selected_week = st.selectbox("Select Week to Grade:", available_weeks, index=st.session_state["selected_week"] - 1)
            if st.button("Update Week"):
                st.session_state["selected_week"] = selected_week
                st.session_state["week_change_allowed"] = False  # Lock week change after update
                st.success(f"Week updated to {selected_week}. To change again, enter the password.")


def load_match_players(week_number):
    try:
        # Fetch match data for the given week
        matches_ref = db.collection("matches").where("week", "==", week_number)
        match_docs = matches_ref.stream()
        
        # Fetch adjusted photo URLs from Cloudinary
        photo_map = get_all_photo_urls()

        player_data = []
        for match in match_docs:
            match_dict = match.to_dict()
            player_id = match_dict.get("player_id", "")
            
            # Match `player_id` directly to the adjusted `public_id`
            photo_url = photo_map.get(player_id, "https://via.placeholder.com/150?text=No+Photo")
            
            # Calculate starting values from matches (times 2)
            stamina = match_dict.get("stamina", 0) * 2
            teamwork = match_dict.get("teamwork", 0) * 2
            attacking = match_dict.get("attacking", 0) * 2
            defending = match_dict.get("defending", 0) * 2

            player_data.append({
                "id": player_id,
                "name": match_dict["player_name"],
                "photo": photo_url,
                "stamina": min(stamina, 10),  # Cap at 10
                "teamwork": min(teamwork, 10),  # Cap at 10
                "attacking": min(attacking, 10),  # Cap at 10
                "defending": min(defending, 10),  # Cap at 10
                "qualitative": "",  # Default qualitative feedback as empty
            })
        return player_data
    except Exception as e:
        st.error(f"Error loading match players: {e}")
        return []



def save_grades(week_number, grading_data):
    """
    Save player grades along with qualitative feedback and match balance to the grades collection.
    
    Args:
        week_number (int): The week number of the match.
        grading_data (list): List of dictionaries containing player grades and qualitative feedback.
        match_balance (str): The match balance feedback for the week.
    """
    try:
        for grade in grading_data:
            # Save each player's grades along with match balance
            db.collection("grades").add({
                "week": week_number,
                "player_id": grade["id"],  # Ensure player_id is saved
                "player_name": grade["name"],
                "stamina": grade["stamina"],
                "teamwork": grade["teamwork"],
                "attacking": grade["attacking"],
                "defending": grade["defending"],
                "qualitative": grade["qualitative"],  # Add qualitative feedback
            })
        st.success("Grades and match feedback saved successfully!")
    except Exception as e:
        st.error(f"Error saving grades: {e}")
def save_match_balance(week_number, match_balance):
    """
    Save the match balance feedback to a new Firestore collection called 'match_balance'.

    Args:
        week_number (int): The week number of the match.
        match_balance (str): The answer to the match balance question.
    """
    try:
        # Save or update the match balance feedback for the given week in the new collection
        db.collection("match_balance").document(f"week_{week_number}").set({
            "week": week_number,
            "match_balance": match_balance
        })
        st.success("Match balance feedback saved successfully in 'match_balance' collection!")
    except Exception as e:
        st.error(f"Error saving match balance feedback: {e}")

def update_grades_with_player_id():
    """
    Update existing records in the 'grades' collection to include player ID from the 'matches' collection.
    """
    try:
        # Fetch all grades from the 'grades' collection
        grades_ref = db.collection("matches").stream()
        grades_to_update = []

        for grade in grades_ref:
            grade_data = grade.to_dict()
            if "player_id" not in grade_data or not grade_data["player_id"]:
                # If player_id is missing, get the player_id from the matches collection
                player_name = grade_data.get("player_name", "")
                week = grade_data.get("week", "")

                # Find the matching player in the 'matches' collection
                matches_ref = db.collection("matches").where("week", "==", week).where("player_name", "==", player_name).stream()
                for match in matches_ref:
                    match_data = match.to_dict()
                    if "player_id" in match_data:
                        # Add player_id to the grade data
                        grade_data["player_id"] = match_data["player_id"]
                        grades_to_update.append((grade.id, grade_data))
                        break

        # Update grades with missing player_id
        for grade_id, updated_data in grades_to_update:
            db.collection("grades").document(grade_id).set(updated_data, merge=True)

        

    except Exception as e:
        st.error(f"Error updating grades with player IDs: {e}")

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

            # Display the photo with a fixed size, centralized
            photo_url = player.get("photo", "")
            if photo_url:
                try:
                    col_image, _, _ = st.columns([2, 1, 1])  # First column wider
                    with col_image:
                        st.image(photo_url, caption=player["name"], width=225)
                except Exception as e:
                    st.warning(f"Cannot load photo for {player['name']}: {e}")
            else:
                st.warning(f"No photo available for {player['name']}")

            # Unique keys for input fields
            unique_key_prefix = f"{player['id']}_{player['name']}"

            col1, col2 = st.columns(2)
            with col1:
                stamina = st.number_input(
                    f"Stamina (from 1 to 10)", 
                    min_value=1.0, max_value=10.0, 
                    value=float(5),  # Ensure float type
                    step=0.1,
                    key=f"{unique_key_prefix}_stamina"
                )
            with col2:
                teamwork = st.number_input(
                    f"Teamwork", 
                    min_value=1.0, max_value=10.0, 
                    value=float(5),  # Ensure float type
                    step=0.1,
                    key=f"{unique_key_prefix}_teamwork"
                )

            # Add attacking and defending fields side by side
            col3, col4 = st.columns(2)
            with col3:
                attacking = st.number_input(
                    f"Attacking", 
                    min_value=1.0, max_value=10.0, 
                    value=float(5),  # Ensure float type
                    step=0.1,
                    key=f"{unique_key_prefix}_attacking"
                )
            with col4:
                defending = st.number_input(
                    f"Defending", 
                    min_value=1.0, max_value=10.0, 
                    value=float(5),  # Ensure float type
                    step=0.1,
                    key=f"{unique_key_prefix}_defending"
                )

            # Add a text area for qualitative feedback
            qualitative = st.text_area(
                f"Qualitative Feedback ({player['name']})",
                value="",
                key=f"{unique_key_prefix}_qualitative"
            )

            # Append the grading data
            grading_data.append({
                "id": player["id"],
                "name": player["name"],
                "stamina": stamina,
                "teamwork": teamwork,
                "attacking": attacking,
                "defending": defending,
                "qualitative": qualitative,
            })

        # Add match balance question
        match_balance = st.radio(
            "Do you think the match was balanced?",
            options=["Yes 👍", "No 👎"],
            key="match_balance",
            horizontal=True
        )

        # Submit the form
        submitted = st.form_submit_button("Submit Grades")
        if submitted:
            # Save grading data
            save_grades(week_number, grading_data)

            # Save match balance feedback in a new collection
            save_match_balance(week_number, match_balance)

def save_match_balance(week_number, match_balance):
    """
    Save the match balance feedback to a new Firestore collection called 'match_balance'.

    Args:
        week_number (int): The week number of the match.
        match_balance (str): The answer to the match balance question.
    """
    try:
        # Add a new entry for the match balance feedback
        db.collection("match_balance").add({
            "week": week_number,
            "match_balance": match_balance,
            "submitted_at": datetime.now()  # Add a timestamp for each submission
        })
        st.success("Match balance feedback saved successfully in 'match_balance' collection!")
    except Exception as e:
        st.error(f"Error saving match balance feedback: {e}")

def main():
    st.title("P&W(🐷📣) Grading app")

    # Post-match grading
    post_match_grading()

    # Automatically update grades collection with player IDs from matches
    update_grades_with_player_id()
    # Password-protected week selection
    password_protected_week_selection()

if __name__ == "__main__":
    main()
