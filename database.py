import streamlit as st
import pandas as pd
from typing import List, Tuple
from datetime import datetime, timezone
from pymongo import AsyncMongoClient

from time_tracker import TimeTracker


def get_mongo_connection():
    """Get MongoDB connection"""
    connection_string = st.secrets["MONGO_CONNECTION_STRING"]
    client = AsyncMongoClient(connection_string,
                          tlsAllowInvalidCertificates=True)
    return client


async def save_to_mongodb(user_name: str, user_surname: str, metrics_df: pd.DataFrame):
    """Save metrics and full text to MongoDB"""
    client = get_mongo_connection()
    db = client['mtpe_database']
    collection = db['user_progress']

    # Convert DataFrame to dict and add user info
    progress_data = {
        'user_name': user_name,
        'user_surname': user_surname,
        'last_updated': datetime.now(),
        'metrics': metrics_df.to_dict('records'),
        'full_text': st.session_state.segments,
        'time_tracker': st.session_state.time_tracker.to_dict(),
        'timer_mode': st.session_state.timer_mode  # Add timer mode to saved data
    }

    # Update or insert document
    await collection.update_one(
        {'user_name': user_name, 'user_surname': user_surname},
        {'$set': progress_data},
        upsert=True
    )


async def load_from_mongodb(user_name: str, user_surname: str) -> Tuple[pd.DataFrame, List[str]]:
    """Load metrics and full text from MongoDB"""
    client = get_mongo_connection()
    db = client['mtpe_database']
    collection = db['user_progress']

    # Find user's progress
    user_data = await collection.find_one({
        'user_name': user_name,
        'user_surname': user_surname
    })

    if user_data:
        # Load timer mode first if available
        if 'timer_mode' in user_data:
            st.session_state.timer_mode = user_data['timer_mode']
            # Create TimeTracker with the correct timer mode
            st.session_state.time_tracker = TimeTracker()
            st.session_state.time_tracker.set_timer_mode(user_data['timer_mode'])

        # Then load time tracker data
        if 'time_tracker' in user_data:
            st.session_state.time_tracker = TimeTracker.from_dict(
                user_data['time_tracker'],
                timer_mode=user_data.get('timer_mode')  # Pass timer mode to from_dict
            )

        # Return metrics and full text if they exist
        metrics = user_data.get('metrics', [])
        full_text = user_data.get('full_text', [])

        if metrics and full_text:
            return pd.DataFrame(metrics), full_text

    return pd.DataFrame(), []


async def validate_mongo_connection(connection_string: str) -> bool:
    """Validate MongoDB connection string by attempting to connect"""
    try:
        test_client = AsyncMongoClient(connection_string, serverSelectionTimeoutMS=5000)
        await test_client.server_info()
        return True
    except Exception as e:
        return str(e)