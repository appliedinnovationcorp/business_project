import json
import asyncio
from typing import Dict, List, Set
from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from datetime import datetime
import uuid

from models import CollaborationSession, User
from database import get_db

class ConnectionManager:
    def __init__(self):
        # Store active connections by session_id
        self.active_connections: Dict[str, List[WebSocket]] = {}
        # Store user info for each connection
        self.connection_users: Dict[WebSocket, Dict] = {}
        # Store session info
        self.sessions: Dict[str, Dict] = {}

    async def connect(self, websocket: WebSocket, session_id: str, user_id: int, user_name: str):
        """Accept a new WebSocket connection"""
        await websocket.accept()
        
        # Initialize session if it doesn't exist
        if session_id not in self.active_connections:
            self.active_connections[session_id] = []
            self.sessions[session_id] = {
                'active_users': {},
                'created_at': datetime.utcnow(),
                'last_activity': datetime.utcnow()
            }
        
        # Add connection to session
        self.active_connections[session_id].append(websocket)
        
        # Store user info for this connection
        self.connection_users[websocket] = {
            'user_id': user_id,
            'user_name': user_name,
            'session_id': session_id,
            'connected_at': datetime.utcnow()
        }
        
        # Add user to session
        self.sessions[session_id]['active_users'][user_id] = {
            'user_name': user_name,
            'connected_at': datetime.utcnow(),
            'cursor_position': None,
            'current_selection': None
        }
        
        # Update last activity
        self.sessions[session_id]['last_activity'] = datetime.utcnow()
        
        # Notify other users in the session
        await self.broadcast_user_joined(session_id, user_id, user_name)
        
        # Send current session state to the new user
        await self.send_session_state(websocket, session_id)

    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection"""
        if websocket in self.connection_users:
            user_info = self.connection_users[websocket]
            session_id = user_info['session_id']
            user_id = user_info['user_id']
            user_name = user_info['user_name']
            
            # Remove connection from session
            if session_id in self.active_connections:
                self.active_connections[session_id].remove(websocket)
                
                # Remove user from session
                if user_id in self.sessions[session_id]['active_users']:
                    del self.sessions[session_id]['active_users'][user_id]
                
                # Clean up empty sessions
                if not self.active_connections[session_id]:
                    del self.active_connections[session_id]
                    del self.sessions[session_id]
                else:
                    # Notify other users that this user left
                    asyncio.create_task(
                        self.broadcast_user_left(session_id, user_id, user_name)
                    )
            
            # Remove user info
            del self.connection_users[websocket]

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send a message to a specific WebSocket connection"""
        try:
            await websocket.send_text(json.dumps(message))
        except:
            # Connection might be closed
            pass

    async def broadcast_to_session(self, session_id: str, message: dict, exclude_websocket: WebSocket = None):
        """Broadcast a message to all connections in a session"""
        if session_id in self.active_connections:
            disconnected = []
            for connection in self.active_connections[session_id]:
                if connection != exclude_websocket:
                    try:
                        await connection.send_text(json.dumps(message))
                    except:
                        # Connection is closed, mark for removal
                        disconnected.append(connection)
            
            # Clean up disconnected connections
            for connection in disconnected:
                self.disconnect(connection)

    async def broadcast_user_joined(self, session_id: str, user_id: int, user_name: str):
        """Notify session users that a new user joined"""
        message = {
            'type': 'user_joined',
            'user_id': user_id,
            'user_name': user_name,
            'timestamp': datetime.utcnow().isoformat()
        }
        await self.broadcast_to_session(session_id, message)

    async def broadcast_user_left(self, session_id: str, user_id: int, user_name: str):
        """Notify session users that a user left"""
        message = {
            'type': 'user_left',
            'user_id': user_id,
            'user_name': user_name,
            'timestamp': datetime.utcnow().isoformat()
        }
        await self.broadcast_to_session(session_id, message)

    async def send_session_state(self, websocket: WebSocket, session_id: str):
        """Send current session state to a user"""
        if session_id in self.sessions:
            session = self.sessions[session_id]
            message = {
                'type': 'session_state',
                'active_users': session['active_users'],
                'timestamp': datetime.utcnow().isoformat()
            }
            await self.send_personal_message(message, websocket)

    async def handle_cursor_update(self, session_id: str, user_id: int, cursor_data: dict, websocket: WebSocket):
        """Handle cursor position updates"""
        if session_id in self.sessions and user_id in self.sessions[session_id]['active_users']:
            self.sessions[session_id]['active_users'][user_id]['cursor_position'] = cursor_data
            
            message = {
                'type': 'cursor_update',
                'user_id': user_id,
                'cursor_data': cursor_data,
                'timestamp': datetime.utcnow().isoformat()
            }
            await self.broadcast_to_session(session_id, message, exclude_websocket=websocket)

    async def handle_selection_update(self, session_id: str, user_id: int, selection_data: dict, websocket: WebSocket):
        """Handle text/element selection updates"""
        if session_id in self.sessions and user_id in self.sessions[session_id]['active_users']:
            self.sessions[session_id]['active_users'][user_id]['current_selection'] = selection_data
            
            message = {
                'type': 'selection_update',
                'user_id': user_id,
                'selection_data': selection_data,
                'timestamp': datetime.utcnow().isoformat()
            }
            await self.broadcast_to_session(session_id, message, exclude_websocket=websocket)

    async def handle_workflow_update(self, session_id: str, user_id: int, workflow_data: dict, websocket: WebSocket):
        """Handle workflow changes"""
        message = {
            'type': 'workflow_update',
            'user_id': user_id,
            'workflow_data': workflow_data,
            'timestamp': datetime.utcnow().isoformat()
        }
        await self.broadcast_to_session(session_id, message, exclude_websocket=websocket)

    async def handle_chat_message(self, session_id: str, user_id: int, user_name: str, message_text: str, websocket: WebSocket):
        """Handle chat messages"""
        message = {
            'type': 'chat_message',
            'user_id': user_id,
            'user_name': user_name,
            'message': message_text,
            'timestamp': datetime.utcnow().isoformat()
        }
        await self.broadcast_to_session(session_id, message, exclude_websocket=websocket)

    async def handle_notification(self, session_id: str, user_id: int, notification_data: dict, websocket: WebSocket):
        """Handle notifications"""
        message = {
            'type': 'notification',
            'user_id': user_id,
            'notification_data': notification_data,
            'timestamp': datetime.utcnow().isoformat()
        }
        await self.broadcast_to_session(session_id, message, exclude_websocket=websocket)

    def get_session_stats(self, session_id: str) -> dict:
        """Get statistics for a session"""
        if session_id not in self.sessions:
            return {}
        
        session = self.sessions[session_id]
        return {
            'session_id': session_id,
            'active_users_count': len(session['active_users']),
            'active_users': list(session['active_users'].values()),
            'created_at': session['created_at'].isoformat(),
            'last_activity': session['last_activity'].isoformat()
        }

    def get_all_sessions_stats(self) -> List[dict]:
        """Get statistics for all active sessions"""
        return [self.get_session_stats(session_id) for session_id in self.sessions.keys()]

# Global connection manager instance
manager = ConnectionManager()

class CollaborationHandler:
    """Handle collaboration-related database operations"""
    
    @staticmethod
    def create_session(db: Session, project_id: int) -> str:
        """Create a new collaboration session"""
        session_id = str(uuid.uuid4())
        
        collaboration_session = CollaborationSession(
            project_id=project_id,
            session_id=session_id,
            active_users=[]
        )
        
        db.add(collaboration_session)
        db.commit()
        
        return session_id
    
    @staticmethod
    def get_session(db: Session, session_id: str) -> CollaborationSession:
        """Get collaboration session by ID"""
        return db.query(CollaborationSession).filter(
            CollaborationSession.session_id == session_id
        ).first()
    
    @staticmethod
    def update_session_activity(db: Session, session_id: str, active_users: List[int]):
        """Update session activity"""
        session = db.query(CollaborationSession).filter(
            CollaborationSession.session_id == session_id
        ).first()
        
        if session:
            session.active_users = active_users
            session.last_activity = datetime.utcnow()
            db.commit()
    
    @staticmethod
    def cleanup_inactive_sessions(db: Session, hours: int = 24):
        """Clean up sessions that have been inactive for specified hours"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        inactive_sessions = db.query(CollaborationSession).filter(
            CollaborationSession.last_activity < cutoff_time
        ).all()
        
        for session in inactive_sessions:
            db.delete(session)
        
        db.commit()
        return len(inactive_sessions)
