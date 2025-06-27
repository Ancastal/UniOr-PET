import streamlit as st
import hashlib
import asyncio
from typing import Tuple
from datetime import datetime, timezone

from database import get_mongo_connection, validate_mongo_connection


def hash_password(password: str) -> str:
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()


async def create_user(name: str, surname: str, password: str, role: str = "translator", mongo_connection: str = None) -> bool:
    """Create a new user in MongoDB"""
    client = get_mongo_connection()
    db = client['mtpe_database']
    users = db['users']

    # Check if user already exists
    existing_user = await users.find_one({
        'name': name,
        'surname': surname
    })

    if existing_user:
        return False

    # Create new user
    user_doc = {
        'name': name,
        'surname': surname,
        'password': hash_password(password),
        'role': role,
        'created_at': datetime.now(timezone.utc),
        'mongo_connection': mongo_connection
    }

    await users.insert_one(user_doc)
    return True


async def verify_user(name: str, surname: str, password: str) -> Tuple[bool, str]:
    """Verify user credentials against MongoDB and return auth status and role"""
    client = get_mongo_connection()
    db = client['mtpe_database']
    users = db['users']

    user = await users.find_one({
        'name': name,
        'surname': surname,
        'password': hash_password(password)
    })

    if user is None:
        return False, ""

    return True, user.get('role', 'translator')


def display_login_form():
    """Display login form"""
    with st.form("login_form"):
        st.subheader("Welcome Back!")
        name = st.text_input("Name", key="login_name", placeholder="Enter your name")
        surname = st.text_input("Surname", key="login_surname", placeholder="Enter your surname")
        password = st.text_input("Password", type="password", key="login_password",
                              placeholder="Enter your password")

        submit_button = st.form_submit_button("Sign In", use_container_width=True)

        if submit_button:
            if name and surname and password:
                with st.spinner("Verifying credentials..."):
                    authenticated, role = asyncio.run(verify_user(name, surname, password))
                    if authenticated:
                        st.session_state.authenticated = True
                        st.session_state.user_name = name
                        st.session_state.user_surname = surname
                        st.session_state.role = role
                        st.success("Login successful!")
                        st.rerun()
                    else:
                        st.error("Invalid credentials. Please try again.")
            else:
                st.error("Please fill in all fields")


def display_register_form():
    """Display registration form"""
    with st.form("register_form"):
        st.subheader("Create Account")
        new_name = st.text_input("Name", key="reg_name", placeholder="Enter your name")
        new_surname = st.text_input("Surname", key="reg_surname", placeholder="Enter your surname")

        # Password fields in columns for better layout
        pass_col1, pass_col2 = st.columns(2)
        with pass_col1:
            new_password = st.text_input("Password", type="password",
                                       key="reg_password",
                                       placeholder="Choose password")
        with pass_col2:
            confirm_password = st.text_input("Confirm Password",
                                           type="password",
                                           placeholder="Repeat password")
        col1, col2 = st.columns(2)
        with col1:
            placeholder_select = st.empty()
        with col2:
            placeholder_mongo = st.empty()

        # Password requirements hint
        st.caption("""
            Password requirements:
            - At least 8 characters
            - Mix of letters and numbers
            """)

        register_button = st.form_submit_button("Create Account", use_container_width=True)

        if register_button:
            if new_name and new_surname and new_password:
                if len(new_password) < 8:
                    st.error("Password must be at least 8 characters long")
                    return

                if new_password != confirm_password:
                    st.error("Passwords do not match")
                    return

                # Validate MongoDB connection string for Project Managers
                if role == "Project Manager":
                    if not mongo_connection:
                        st.error("MongoDB connection string is required for Project Managers")
                        return

                    # Validate the connection string
                    validation_result = asyncio.run(validate_mongo_connection(mongo_connection))
                    if validation_result is not True:
                        st.error(f"Invalid MongoDB connection string: {validation_result}")
                        return

                with st.spinner("Creating your account..."):
                    # Convert role selection to database value
                    db_role = "project_manager" if role == "Project Manager" else "translator"
                    # Include MongoDB connection string for project managers
                    if asyncio.run(create_user(new_name, new_surname, new_password, db_role, mongo_connection if db_role == "project_manager" else None)):
                        st.success("✅ Registration successful!")
                        st.info("Please proceed to login with your credentials")
                        # Clear registration fields
                        st.session_state.pop('reg_name', None)
                        st.session_state.pop('reg_surname', None)
                        st.session_state.pop('reg_password', None)
                    else:
                        st.error("An account with these details already exists")
            else:
                st.error("Please fill in all fields")

        with placeholder_select:
                role = st.selectbox(
                    "I am a...",
                    ["Translator", "Project Manager"],
                )

        with placeholder_mongo:
                if role == "Project Manager":
                    # Show MongoDB connection string input for Project Managers
                    mongo_connection = st.text_input(
                                    "MongoDB Connection String",
                                    type="password",
                                    help="Enter your MongoDB connection string in the format: mongodb+srv://username:password@cluster.domain",
                                    label_visibility="visible"
                    )


def display_auth_page():
    """Display authentication page with login and register tabs"""
    # Welcome message with improved styling
    st.markdown("""
        <div class="welcome-card">
            <p>Access your personalized post-editing workspace by logging in or creating a new account.</p>
        </div>
        """, unsafe_allow_html=True)

    # Login/Register tabs with improved styling
    tabs = st.tabs(["🔑 Login", "✨ Register"])

    with tabs[0]:
        display_login_form()
        
        st.markdown("""
                    </form>
                </div>
                <div class="info-sidebar">
                    <h4>Why Sign In?</h4>
                    <ul>
                        <li>Save your progress automatically</li>
                        <li>Resume your work anytime</li>
                        <li>Track your editing statistics</li>
                        <li>Access advanced features</li>
                    </ul>
                </div>
            </div>
        """, unsafe_allow_html=True)

    with tabs[1]:
        display_register_form()
        
        st.markdown("""
            <div class="info-sidebar">
                <h4>Benefits of Registration</h4>
                <ul>
                    <li>Free access to all features</li>
                    <li>Secure data storage</li>
                    <li>Progress tracking</li>
                    <li>Cloud backup of your work</li>
                </ul>
            </div>
        """, unsafe_allow_html=True)

    # Footer with additional information
    st.markdown("""
        <div class="login-footer">
            <p>By using this tool, you agree to our Terms of Service and Privacy Policy</p>
            <p>Need help? Contact <a href="mailto:antonio.castaldo@phd.unipi.it">antonio.castaldo@phd.unipi.it</a></p>
        </div>
        """, unsafe_allow_html=True)


def display_user_info():
    """Display user info and logout button in sidebar"""
    st.write(f"Logged in as: **{st.session_state.user_name} {st.session_state.user_surname}**")
    if st.button("🚪 Logout", use_container_width=True):
        # Clear session state
        st.session_state.authenticated = False
        st.session_state.user_name = ""
        st.session_state.user_surname = ""
        st.rerun()