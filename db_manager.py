"""
Database abstraction layer for MongoDB and Supabase
"""
from abc import ABC, abstractmethod
from typing import Optional, Tuple, Dict, Any, List
from datetime import datetime, timezone
import pandas as pd
from pymongo import AsyncMongoClient
from supabase import create_client, Client
import hashlib
import streamlit as st
import os


def hash_password(password: str) -> str:
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()


class DatabaseManager(ABC):
    """Abstract base class for database operations"""

    @abstractmethod
    async def create_user(self, name: str, surname: str, password: str, role: str = "translator",
                         db_type: str = None, db_connection: str = None, project_key: str = None) -> bool:
        """Create a new user"""
        pass

    @abstractmethod
    async def verify_user(self, name: str, surname: str, password: str) -> Tuple[bool, str, Optional[str], Optional[str]]:
        """Verify user credentials and return (authenticated, role, db_type, db_connection)"""
        pass

    @abstractmethod
    async def save_progress(self, user_name: str, user_surname: str, metrics_df: pd.DataFrame,
                           segments: List, time_tracker_dict: Dict, timer_mode: str):
        """Save user progress"""
        pass

    @abstractmethod
    async def load_progress(self, user_name: str, user_surname: str) -> Tuple[pd.DataFrame, List, Dict, str]:
        """Load user progress and return (metrics_df, segments, time_tracker_dict, timer_mode)"""
        pass

    @abstractmethod
    async def create_project(self, project_key: str, pm_name: str, pm_surname: str,
                            db_type: str, db_connection: str) -> bool:
        """Create a new project record"""
        pass

    @abstractmethod
    async def get_project(self, project_key: str) -> Optional[Dict[str, Any]]:
        """Retrieve project by key"""
        pass

    @abstractmethod
    async def save_project_files(self, project_key: str, source_filename: str,
                                translation_filename: str, source_content: str,
                                translation_content: str, line_count: int) -> bool:
        """Store project files"""
        pass

    @abstractmethod
    async def load_project_files(self, project_key: str) -> Optional[Tuple[str, str, str, str]]:
        """Load project files and return (source_filename, translation_filename, source_content, translation_content)"""
        pass

    @abstractmethod
    async def get_user_project_key(self, user_name: str, user_surname: str) -> Optional[str]:
        """Get project key for a user (mainly for translators)"""
        pass

    @abstractmethod
    async def get_project_translators(self, project_key: str) -> List[Dict[str, Any]]:
        """Get all translators assigned to a project"""
        pass


class MongoDBManager(DatabaseManager):
    """MongoDB implementation of database operations"""

    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self._client = None

    @property
    def client(self):
        """Get or create MongoDB client"""
        if self._client is None:
            self._client = AsyncMongoClient(
                self.connection_string,
                tlsAllowInvalidCertificates=True
            )
        return self._client

    @property
    def db(self):
        """Get database instance"""
        return self.client['mtpe_database']

    async def create_user(self, name: str, surname: str, password: str, role: str = "translator",
                         db_type: str = None, db_connection: str = None, project_key: str = None) -> bool:
        """Create a new user in MongoDB"""
        users = self.db['users']

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
            'db_type': db_type,
            'db_connection': db_connection,
            'project_key': project_key
        }

        await users.insert_one(user_doc)
        return True

    async def verify_user(self, name: str, surname: str, password: str) -> Tuple[bool, str, Optional[str], Optional[str]]:
        """Verify user credentials against MongoDB"""
        users = self.db['users']

        user = await users.find_one({
            'name': name,
            'surname': surname,
            'password': hash_password(password)
        })

        if user is None:
            return False, "", None, None

        return True, user.get('role', 'translator'), user.get('db_type'), user.get('db_connection')

    async def save_progress(self, user_name: str, user_surname: str, metrics_df: pd.DataFrame,
                           segments: List, time_tracker_dict: Dict, timer_mode: str):
        """Save user progress to MongoDB"""
        collection = self.db['user_progress']

        progress_data = {
            'user_name': user_name,
            'user_surname': user_surname,
            'last_updated': datetime.now(),
            'metrics': metrics_df.to_dict('records') if not metrics_df.empty else [],
            'full_text': segments,
            'time_tracker': time_tracker_dict,
            'timer_mode': timer_mode
        }

        await collection.update_one(
            {'user_name': user_name, 'user_surname': user_surname},
            {'$set': progress_data},
            upsert=True
        )

    async def load_progress(self, user_name: str, user_surname: str) -> Tuple[pd.DataFrame, List, Dict, str]:
        """Load user progress from MongoDB"""
        collection = self.db['user_progress']

        user_data = await collection.find_one({
            'user_name': user_name,
            'user_surname': user_surname
        })

        if user_data:
            metrics = user_data.get('metrics', [])
            full_text = user_data.get('full_text', [])
            time_tracker = user_data.get('time_tracker', {})
            timer_mode = user_data.get('timer_mode', 'current')

            metrics_df = pd.DataFrame(metrics) if metrics else pd.DataFrame()
            return metrics_df, full_text, time_tracker, timer_mode

        return pd.DataFrame(), [], {}, 'current'

    async def create_project(self, project_key: str, pm_name: str, pm_surname: str,
                            db_type: str, db_connection: str) -> bool:
        """Create a new project record in MongoDB"""
        projects = self.db['projects']

        # Check if project already exists
        existing = await projects.find_one({'project_key': project_key})
        if existing:
            return False

        project_doc = {
            'project_key': project_key,
            'pm_name': pm_name,
            'pm_surname': pm_surname,
            'created_at': datetime.now(timezone.utc),
            'last_updated': datetime.now(timezone.utc),
            'db_type': db_type,
            'db_connection': db_connection
        }

        await projects.insert_one(project_doc)
        return True

    async def get_project(self, project_key: str) -> Optional[Dict[str, Any]]:
        """Retrieve project by key from MongoDB"""
        projects = self.db['projects']
        return await projects.find_one({'project_key': project_key})

    async def save_project_files(self, project_key: str, source_filename: str,
                                translation_filename: str, source_content: str,
                                translation_content: str, line_count: int) -> bool:
        """Store project files in MongoDB"""
        collection = self.db['project_files']

        file_doc = {
            'project_key': project_key,
            'source_filename': source_filename,
            'translation_filename': translation_filename,
            'source_content': source_content,
            'translation_content': translation_content,
            'line_count': line_count,
            'uploaded_at': datetime.now(timezone.utc)
        }

        # Upsert to handle re-uploads
        await collection.update_one(
            {'project_key': project_key},
            {'$set': file_doc},
            upsert=True
        )
        return True

    async def load_project_files(self, project_key: str) -> Optional[Tuple[str, str, str, str]]:
        """Load project files from MongoDB"""
        collection = self.db['project_files']

        file_data = await collection.find_one({'project_key': project_key})

        if file_data:
            return (
                file_data['source_filename'],
                file_data['translation_filename'],
                file_data['source_content'],
                file_data['translation_content']
            )
        return None

    async def get_user_project_key(self, user_name: str, user_surname: str) -> Optional[str]:
        """Get project key for a user from MongoDB"""
        users = self.db['users']
        user = await users.find_one({'name': user_name, 'surname': user_surname})
        return user.get('project_key') if user else None

    async def get_project_translators(self, project_key: str) -> List[Dict[str, Any]]:
        """Get all translators assigned to a project from MongoDB"""
        users = self.db['users']
        cursor = users.find({
            'project_key': project_key,
            'role': 'translator'
        })
        translators = await cursor.to_list(length=None)
        # Convert ObjectId to string for JSON serialization
        for translator in translators:
            if '_id' in translator:
                translator['_id'] = str(translator['_id'])
        return translators


class SupabaseManager(DatabaseManager):
    """Supabase implementation of database operations"""

    def __init__(self, url: str, api_key: str):
        self.url = url
        self.api_key = api_key
        self._client = None

    @property
    def client(self) -> Client:
        """Get or create Supabase client"""
        if self._client is None:
            self._client = create_client(self.url, self.api_key)
        return self._client

    async def create_user(self, name: str, surname: str, password: str, role: str = "translator",
                         db_type: str = None, db_connection: str = None, project_key: str = None) -> bool:
        """Create a new user in Supabase"""
        # Check if user already exists
        response = self.client.table('users').select('*').eq('name', name).eq('surname', surname).execute()

        if response.data:
            return False

        # Create new user
        user_doc = {
            'name': name,
            'surname': surname,
            'password': hash_password(password),
            'role': role,
            'created_at': datetime.now(timezone.utc).isoformat(),
            'db_type': db_type,
            'db_connection': db_connection,
            'project_key': project_key
        }

        self.client.table('users').insert(user_doc).execute()
        return True

    async def verify_user(self, name: str, surname: str, password: str) -> Tuple[bool, str, Optional[str], Optional[str]]:
        """Verify user credentials against Supabase"""
        response = self.client.table('users').select('*').eq('name', name).eq('surname', surname).eq('password', hash_password(password)).execute()

        if not response.data:
            return False, "", None, None

        user = response.data[0]
        return True, user.get('role', 'translator'), user.get('db_type'), user.get('db_connection')

    async def save_progress(self, user_name: str, user_surname: str, metrics_df: pd.DataFrame,
                           segments: List, time_tracker_dict: Dict, timer_mode: str):
        """Save user progress to Supabase"""
        progress_data = {
            'user_name': user_name,
            'user_surname': user_surname,
            'last_updated': datetime.now().isoformat(),
            'metrics': metrics_df.to_dict('records') if not metrics_df.empty else [],
            'full_text': segments,
            'time_tracker': time_tracker_dict,
            'timer_mode': timer_mode
        }

        # Check if progress already exists
        response = self.client.table('user_progress').select('*').eq('user_name', user_name).eq('user_surname', user_surname).execute()

        if response.data:
            # Update existing progress
            self.client.table('user_progress').update(progress_data).eq('user_name', user_name).eq('user_surname', user_surname).execute()
        else:
            # Insert new progress
            self.client.table('user_progress').insert(progress_data).execute()

    async def load_progress(self, user_name: str, user_surname: str) -> Tuple[pd.DataFrame, List, Dict, str]:
        """Load user progress from Supabase"""
        response = self.client.table('user_progress').select('*').eq('user_name', user_name).eq('user_surname', user_surname).execute()

        if response.data:
            user_data = response.data[0]
            metrics = user_data.get('metrics', [])
            full_text = user_data.get('full_text', [])
            time_tracker = user_data.get('time_tracker', {})
            timer_mode = user_data.get('timer_mode', 'current')

            metrics_df = pd.DataFrame(metrics) if metrics else pd.DataFrame()
            return metrics_df, full_text, time_tracker, timer_mode

        return pd.DataFrame(), [], {}, 'current'

    async def create_project(self, project_key: str, pm_name: str, pm_surname: str,
                            db_type: str, db_connection: str) -> bool:
        """Create a new project record in Supabase"""
        # Check if project already exists
        response = self.client.table('projects').select('*').eq('project_key', project_key).execute()
        if response.data:
            return False

        project_doc = {
            'project_key': project_key,
            'pm_name': pm_name,
            'pm_surname': pm_surname,
            'created_at': datetime.now(timezone.utc).isoformat(),
            'last_updated': datetime.now(timezone.utc).isoformat(),
            'db_type': db_type,
            'db_connection': db_connection
        }

        self.client.table('projects').insert(project_doc).execute()
        return True

    async def get_project(self, project_key: str) -> Optional[Dict[str, Any]]:
        """Retrieve project by key from Supabase"""
        response = self.client.table('projects').select('*').eq('project_key', project_key).execute()
        return response.data[0] if response.data else None

    async def save_project_files(self, project_key: str, source_filename: str,
                                translation_filename: str, source_content: str,
                                translation_content: str, line_count: int) -> bool:
        """Store project files in Supabase"""
        file_doc = {
            'project_key': project_key,
            'source_filename': source_filename,
            'translation_filename': translation_filename,
            'source_content': source_content,
            'translation_content': translation_content,
            'line_count': line_count,
            'uploaded_at': datetime.now(timezone.utc).isoformat()
        }

        # Check if exists
        response = self.client.table('project_files').select('*').eq('project_key', project_key).execute()

        if response.data:
            # Update
            self.client.table('project_files').update(file_doc).eq('project_key', project_key).execute()
        else:
            # Insert
            self.client.table('project_files').insert(file_doc).execute()

        return True

    async def load_project_files(self, project_key: str) -> Optional[Tuple[str, str, str, str]]:
        """Load project files from Supabase"""
        response = self.client.table('project_files').select('*').eq('project_key', project_key).execute()

        if response.data:
            file_data = response.data[0]
            return (
                file_data['source_filename'],
                file_data['translation_filename'],
                file_data['source_content'],
                file_data['translation_content']
            )
        return None

    async def get_user_project_key(self, user_name: str, user_surname: str) -> Optional[str]:
        """Get project key for a user from Supabase"""
        response = self.client.table('users').select('project_key').eq('name', user_name).eq('surname', user_surname).execute()
        return response.data[0]['project_key'] if response.data else None

    async def get_project_translators(self, project_key: str) -> List[Dict[str, Any]]:
        """Get all translators assigned to a project from Supabase"""
        response = self.client.table('users').select('*').eq('project_key', project_key).eq('role', 'translator').execute()
        return response.data if response.data else []


@st.cache_resource
def get_default_supabase_manager():
    """Get the default Supabase manager using environment variables"""
    url = os.getenv('PROJECT_URL') or st.secrets.get('PROJECT_URL')
    api_key = os.getenv('PROJECT_API_KEY') or st.secrets.get('PROJECT_API_KEY')

    if not url or not api_key:
        raise ValueError("Supabase credentials not found in environment or secrets")

    return SupabaseManager(url, api_key)


@st.cache_resource
def get_default_mongodb_manager():
    """Get the default MongoDB manager using secrets"""
    connection_string = st.secrets.get("MONGO_CONNECTION_STRING")

    if not connection_string:
        raise ValueError("MongoDB connection string not found in secrets")

    return MongoDBManager(connection_string)


def get_database_manager(db_type: str = None, db_connection: str = None) -> DatabaseManager:
    """
    Factory function to get the appropriate database manager

    Args:
        db_type: Type of database ('supabase', 'mongodb', or None for default)
        db_connection: Connection string for the database (required for custom MongoDB)

    Returns:
        DatabaseManager instance
    """
    if db_type is None or db_type == 'free_supabase':
        # Use default free Supabase
        return get_default_supabase_manager()
    elif db_type == 'mongodb':
        # Use custom MongoDB
        if not db_connection:
            raise ValueError("MongoDB connection string is required")
        return MongoDBManager(db_connection)
    elif db_type == 'supabase':
        # Use custom Supabase
        if not db_connection:
            raise ValueError("Supabase connection string is required")
        # Parse Supabase connection string (format: "url|api_key")
        try:
            url, api_key = db_connection.split('|')
            return SupabaseManager(url, api_key)
        except ValueError:
            raise ValueError("Invalid Supabase connection string format. Expected: 'url|api_key'")
    else:
        raise ValueError(f"Unknown database type: {db_type}")


async def validate_project_key_and_get_pm_settings(project_key: str) -> Tuple[bool, Optional[str], Optional[str], str]:
    """
    Validate a project key and retrieve the Project Manager's database settings

    Args:
        project_key: Project key in format "surname_name" (e.g., "Smith_John")

    Returns:
        Tuple of (is_valid, db_type, db_connection, error_message)
    """
    try:
        # Parse project key (format: surname_name)
        parts = project_key.split('_')
        if len(parts) < 2:
            return False, None, None, "Invalid project key format. Expected format: 'Surname_Name'"

        pm_surname = parts[0]
        pm_name = '_'.join(parts[1:])  # Handle names with underscores

        # Get default database manager to look up PM
        db_manager = get_default_supabase_manager()

        # Look up the project manager
        if isinstance(db_manager, SupabaseManager):
            response = db_manager.client.table('users').select('*').eq('name', pm_name).eq('surname', pm_surname).eq('role', 'project_manager').execute()

            if not response.data:
                return False, None, None, f"No Project Manager found with key: {project_key}"

            pm_user = response.data[0]
            db_type = pm_user.get('db_type')
            db_connection = pm_user.get('db_connection')

            return True, db_type, db_connection, ""
        else:
            # MongoDB lookup
            users = db_manager.db['users']
            pm_user = await users.find_one({
                'name': pm_name,
                'surname': pm_surname,
                'role': 'project_manager'
            })

            if not pm_user:
                return False, None, None, f"No Project Manager found with key: {project_key}"

            db_type = pm_user.get('db_type')
            db_connection = pm_user.get('db_connection')

            return True, db_type, db_connection, ""

    except Exception as e:
        return False, None, None, f"Error validating project key: {str(e)}"


def validate_database_connection(db_type: str, db_connection: str) -> Tuple[bool, str]:
    """
    Validate a database connection

    Args:
        db_type: Type of database ('mongodb' or 'supabase')
        db_connection: Connection string

    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        if db_type == 'mongodb':
            # Try to create a MongoDB client and connect
            import asyncio
            from pymongo import AsyncMongoClient

            async def test_mongo():
                client = AsyncMongoClient(db_connection, serverSelectionTimeoutMS=5000)
                await client.server_info()
                client.close()

            asyncio.run(test_mongo())
            return True, ""
        elif db_type == 'supabase':
            # Try to create a Supabase client
            try:
                url, api_key = db_connection.split('|')
                client = create_client(url, api_key)
                # Test connection by trying to access a table
                # This will fail if credentials are invalid
                client.table('users').select('count').limit(1).execute()
                return True, ""
            except ValueError:
                return False, "Invalid format. Expected: 'url|api_key'"
        else:
            return False, f"Unknown database type: {db_type}"
    except Exception as e:
        return False, str(e)
