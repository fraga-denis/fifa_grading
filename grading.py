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
        # Fetch match data for the given week
        matches_ref = db.collection("matches").where("week", "==", week_number)
        match_docs = matches_ref.stream()
        
        player_data = []
        for match in match_docs:
            match_dict = match.to_dict()
            player_data.append({
                "id": match_dict.get("player_id", ""),
                "name": match_dict["player_name"],
                "stamina": match_dict.get("stamina", 0),
                "teamwork": match_dict.get("teamwork", 0),
                "attacking": match_dict.get("attacking", 0),
                "defending": match_dict.get("defending", 0),
            })
        return player_data
    except Exception as e:
        st.error(f"Error loading match players: {e}")
        return []
