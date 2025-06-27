import streamlit as st
import hashlib
import asyncio
from typing import Tuple
from datetime import datetime, timezone

from database import get_mongo_connection, validate_mongo_connection, create_project, get_project_by_id, assign_translator_to_project


def hash_password(password: str) -> str:
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()


async def create_user(name: str, surname: str, password: str, role: str = "translator", mongo_connection: str = None, project_id: str = None) -> bool:
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
        'mongo_connection': mongo_connection,
        'project_id': project_id
    }

    await users.insert_one(user_doc)
    return True


async def verify_user(name: str, surname: str, password: str) -> Tuple[bool, str, dict]:
    """Verify user credentials against MongoDB and return auth status, role, and user data"""
    client = get_mongo_connection()
    db = client['mtpe_database']
    users = db['users']

    user = await users.find_one({
        'name': name,
        'surname': surname,
        'password': hash_password(password)
    })

    if user is None:
        return False, "", {}

    return True, user.get('role', 'translator'), user


def convert_project_to_segments(source_text: str, mt_output: str) -> list:
    """Convert project source text and MT output to segments format"""
    # Split texts into lines and create segments
    source_lines = [line.strip() for line in source_text.split('\n') if line.strip()]
    mt_lines = [line.strip() for line in mt_output.split('\n') if line.strip()]
    
    # Ensure both have same length by padding shorter one
    max_len = max(len(source_lines), len(mt_lines))
    source_lines.extend([''] * (max_len - len(source_lines)))
    mt_lines.extend([''] * (max_len - len(mt_lines)))
    
    return list(zip(source_lines, mt_lines))


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
                    authenticated, role, user_data = asyncio.run(verify_user(name, surname, password))
                    if authenticated:
                        st.session_state.authenticated = True
                        st.session_state.user_name = name
                        st.session_state.user_surname = surname
                        st.session_state.role = role
                        
                        # Load project data for translators
                        if role == "translator" and user_data.get('project_id'):
                            with st.spinner("Loading project data..."):
                                project = asyncio.run(get_project_by_id(user_data['project_id']))
                                if project:
                                    segments = convert_project_to_segments(
                                        project['source_text'], 
                                        project['mt_output']
                                    )
                                    st.session_state.segments = segments
                                    st.session_state.has_loaded_segments = True
                                    
                                    # Set timer mode from project settings
                                    project_timer_mode = project.get('timer_mode', 'current')
                                    st.session_state.timer_mode = project_timer_mode
                                    
                                    timer_desc = "Current Timer (Automatic)" if project_timer_mode == "current" else "PET Timer (Manual Control)"
                                    st.success(f"Login successful! Project loaded with {timer_desc}.")
                                else:
                                    st.warning("Login successful but project data could not be loaded.")
                        else:
                            st.success("Login successful!")
                        
                        st.rerun()
                    else:
                        st.error("Invalid credentials. Please try again.")
            else:
                st.error("Please fill in all fields")


def display_register_form():
    """Display registration form"""
    st.subheader("Create Account")
    
    # Role selection outside the form so it can update dynamically
    role = st.selectbox(
        "I am a...",
        ["Translator", "Project Manager"],
        key="role_selection"
    )
    
    # Now create the form with role-specific fields
    with st.form("register_form"):
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

        # Initialize variables for conditional fields
        mongo_connection = None
        source_file = None
        mt_file = None
        project_id = None
        timer_mode = "current"

        # Role-specific fields
        if role == "Project Manager":
            st.write("#### Project Manager Setup")
            
            # MongoDB connection string
            mongo_connection = st.text_input(
                "MongoDB Connection String",
                type="password",
                help="Enter your MongoDB connection string in the format: mongodb+srv://username:password@cluster.domain",
                label_visibility="visible"
            )
            
            # File uploads for Project Managers
            st.write("Upload your project files:")
            source_file = st.file_uploader(
                "Source Text File",
                type=['txt', 'docx', 'pdf'],
                help="Upload the source text file for translation"
            )
            
            mt_file = st.file_uploader(
                "Machine Translation Output File", 
                type=['txt', 'docx', 'pdf'],
                help="Upload the machine translation output file"
            )
            
            # Timer mode selection for Project Managers
            st.write("**Timer Settings for Translators**")
            timer_mode = st.radio(
                "Select timer mode for your translators:",
                options=["current", "pet"],
                format_func=lambda x: "Current Timer (Automatic)" if x == "current" else "PET Timer (Manual Control)",
                help="Current Timer: Automatic time tracking with idle detection. PET Timer: Manual start/pause control for research.",
                horizontal=True
            )
            
        elif role == "Translator":
            st.write("#### Translator Setup")
            
            # Project ID input for Translators
            project_id = st.text_input(
                "Project ID",
                placeholder="Enter the project ID provided by your Project Manager",
                help="This ID links you to the project files uploaded by your Project Manager"
            )

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

                # Role-specific validation
                if role == "Project Manager":
                    if not mongo_connection:
                        st.error("MongoDB connection string is required for Project Managers")
                        return
                    
                    if not source_file or not mt_file:
                        st.error("Both source text and MT output files are required for Project Managers")
                        return

                    # Validate the connection string
                    validation_result = asyncio.run(validate_mongo_connection(mongo_connection))
                    if validation_result is not True:
                        st.error(f"Invalid MongoDB connection string: {validation_result}")
                        return

                elif role == "Translator":
                    if not project_id:
                        st.error("Project ID is required for Translators")
                        return
                    
                    # Validate project ID exists
                    project = asyncio.run(get_project_by_id(project_id))
                    if not project:
                        st.error("Invalid Project ID. Please check with your Project Manager.")
                        return

                with st.spinner("Creating your account..."):
                    try:
                        # Convert role selection to database value
                        db_role = "project_manager" if role == "Project Manager" else "translator"
                        
                        # Handle Project Manager registration
                        if db_role == "project_manager":
                            # Read file contents
                            source_text = source_file.read().decode('utf-8')
                            mt_output = mt_file.read().decode('utf-8')
                            
                            # Create user first
                            user_created = asyncio.run(create_user(new_name, new_surname, new_password, db_role, mongo_connection))
                            
                            if user_created:
                                # Create project and get project ID
                                new_project_id = asyncio.run(create_project(new_name, new_surname, source_text, mt_output, timer_mode))
                                timer_desc = "Current Timer (Automatic)" if timer_mode == "current" else "PET Timer (Manual Control)"
                                st.success(f"✅ Registration successful! Your Project ID is: **{new_project_id}**")
                                st.info(f"Timer mode set to: **{timer_desc}**")
                                st.info("Share this Project ID with your translators so they can join your project.")
                                st.info("Please proceed to login with your credentials")
                            else:
                                st.error("An account with these details already exists")
                                
                        # Handle Translator registration  
                        else:
                            user_created = asyncio.run(create_user(new_name, new_surname, new_password, db_role, None, project_id))
                            
                            if user_created:
                                # Assign translator to project
                                asyncio.run(assign_translator_to_project(project_id, new_name, new_surname))
                                st.success("✅ Registration successful! You have been assigned to the project.")
                                st.info("Please proceed to login with your credentials")
                            else:
                                st.error("An account with these details already exists")
                                
                        # Clear registration fields
                        st.session_state.pop('reg_name', None)
                        st.session_state.pop('reg_surname', None)
                        st.session_state.pop('reg_password', None)
                        
                    except Exception as e:
                        st.error(f"Registration failed: {str(e)}")
            else:
                st.error("Please fill in all fields")


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
    
    # Display role information
    role_display = "Project Manager" if st.session_state.role == "project_manager" else "Translator"
    st.write(f"Role: **{role_display}**")
    
    # Show project info if segments are loaded
    if hasattr(st.session_state, 'segments') and len(st.session_state.segments) > 0:
        st.write(f"📄 Segments loaded: **{len(st.session_state.segments)}**")
    
    if st.button("🚪 Logout", use_container_width=True):
        # Clear session state
        st.session_state.authenticated = False
        st.session_state.user_name = ""
        st.session_state.user_surname = ""
        st.session_state.role = ""
        st.rerun()