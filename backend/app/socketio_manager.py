"""
Socket.io manager for real-time gameplay features.
Handles player presence, action list updates, ready states, and chat.
"""
import socketio
from typing import Dict, Set

# Create Socket.IO server
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins='*',
    logger=True,
    engineio_logger=True
)

# Track active sessions and connected players
# Structure: {session_id: {player_id: sid}}
active_sessions: Dict[str, Dict[str, str]] = {}


@sio.event
async def connect(sid, environ):
    """Handle client connection."""
    print(f"Client connected: {sid}")
    await sio.emit('connected', {'sid': sid}, to=sid)


@sio.event
async def disconnect(sid):
    """Handle client disconnection."""
    print(f"Client disconnected: {sid}")

    # Remove from active sessions
    for session_id, players in active_sessions.items():
        for player_id, player_data in list(players.items()):
            if isinstance(player_data, dict) and player_data.get('sid') == sid:
                del players[player_id]
                # Notify other players in session
                await sio.emit('player_disconnected', {
                    'player_id': player_id,
                    'session_id': session_id
                }, room=f"session:{session_id}")
                break
            elif player_data == sid:  # Legacy support
                del players[player_id]
                await sio.emit('player_disconnected', {
                    'player_id': player_id,
                    'session_id': session_id
                }, room=f"session:{session_id}")
                break


@sio.event
async def join_session(sid, data):
    """Player joins a game session."""
    session_id = data.get('session_id')
    player_id = data.get('player_id')
    player_name = data.get('player_name')

    if not session_id or not player_id:
        await sio.emit('error', {'message': 'Missing session_id or player_id'}, to=sid)
        return

    # Join session room
    await sio.enter_room(sid, f"session:{session_id}")

    # Track player in session with their info
    if session_id not in active_sessions:
        active_sessions[session_id] = {}
    active_sessions[session_id][player_id] = {
        'sid': sid,
        'player_name': player_name,
        'player_id': player_id
    }

    # Build full player list for broadcast
    players_list = [
        {
            'player_id': pid,
            'player_name': pdata['player_name'],
            'online': True
        }
        for pid, pdata in active_sessions[session_id].items()
    ]

    # Notify other players
    await sio.emit('player_joined', {
        'player_id': player_id,
        'player_name': player_name,
        'session_id': session_id
    }, room=f"session:{session_id}", skip_sid=sid)

    # Send current session state to joining player
    await sio.emit('session_joined', {
        'session_id': session_id,
        'players_online': players_list
    }, to=sid)


@sio.event
async def leave_session(sid, data):
    """Player leaves a game session."""
    session_id = data.get('session_id')
    player_id = data.get('player_id')

    if session_id and player_id:
        # Leave session room
        await sio.leave_room(sid, f"session:{session_id}")

        # Remove from tracking
        if session_id in active_sessions and player_id in active_sessions[session_id]:
            del active_sessions[session_id][player_id]

        # Notify other players
        await sio.emit('player_left', {
            'player_id': player_id,
            'session_id': session_id
        }, room=f"session:{session_id}")


# ============== ACTION LIST EVENTS ==============

@sio.event
async def action_draft_created(sid, data):
    """Broadcast new action draft to session."""
    session_id = data.get('session_id')
    if session_id:
        await sio.emit('action_draft_created', data, room=f"session:{session_id}", skip_sid=sid)


@sio.event
async def action_draft_updated(sid, data):
    """Broadcast action draft update to session."""
    session_id = data.get('session_id')
    if session_id:
        await sio.emit('action_draft_updated', data, room=f"session:{session_id}", skip_sid=sid)


@sio.event
async def action_draft_deleted(sid, data):
    """Broadcast action draft deletion to session."""
    session_id = data.get('session_id')
    draft_id = data.get('draft_id')
    if session_id and draft_id:
        await sio.emit('action_draft_deleted', {'draft_id': draft_id}, room=f"session:{session_id}", skip_sid=sid)


@sio.event
async def action_draft_reordered(sid, data):
    """Broadcast action list reorder to session."""
    session_id = data.get('session_id')
    order = data.get('order')  # Array of draft IDs in new order
    if session_id and order:
        await sio.emit('action_draft_reordered', {'order': order}, room=f"session:{session_id}", skip_sid=sid)


# ============== READY STATE EVENTS ==============

@sio.event
async def ready_state_changed(sid, data):
    """Broadcast ready state change to session."""
    session_id = data.get('session_id')
    player_id = data.get('player_id')
    character_id = data.get('character_id')
    ready = data.get('ready')

    if session_id:
        await sio.emit('ready_state_changed', {
            'player_id': player_id,
            'character_id': character_id,
            'ready': ready
        }, room=f"session:{session_id}", skip_sid=sid)


# ============== TURN SUBMISSION EVENTS ==============

@sio.event
async def turn_submitted(sid, data):
    """Broadcast turn submission to session."""
    session_id = data.get('session_id')
    turn_id = data.get('turn_id')

    if session_id and turn_id:
        await sio.emit('turn_submitted', {
            'turn_id': turn_id,
            'status': 'ready_for_agents'
        }, room=f"session:{session_id}")


@sio.event
async def turn_completed(sid, data):
    """Broadcast turn completion (Keeper response) to session."""
    session_id = data.get('session_id')
    turn_id = data.get('turn_id')
    reaction = data.get('reaction')

    if session_id and turn_id:
        await sio.emit('turn_completed', {
            'turn_id': turn_id,
            'reaction': reaction
        }, room=f"session:{session_id}")


# ============== MASTER TRANSFER EVENTS ==============

@sio.event
async def master_transferred(sid, data):
    """Broadcast master transfer to session."""
    session_id = data.get('session_id')
    new_master_id = data.get('new_master_id')
    new_master_name = data.get('new_master_name')

    if session_id and new_master_id:
        await sio.emit('master_transferred', {
            'new_master_id': new_master_id,
            'new_master_name': new_master_name
        }, room=f"session:{session_id}")


# ============== CHAT EVENTS ==============

@sio.event
async def realm_chat_message(sid, data):
    """Broadcast realm chat message to session."""
    session_id = data.get('session_id')
    player_id = data.get('player_id')
    player_name = data.get('player_name')
    message = data.get('message')
    timestamp = data.get('timestamp')

    if session_id and message:
        await sio.emit('realm_chat_message', {
            'player_id': player_id,
            'player_name': player_name,
            'message': message,
            'timestamp': timestamp
        }, room=f"session:{session_id}", skip_sid=sid)


@sio.event
async def prophet_chat_message(sid, data):
    """Handle private Prophet chat messages (to AI, then back to player)."""
    player_id = data.get('player_id')
    message = data.get('message')

    # TODO: Forward to Prophet AI agent / n8n workflow
    # For now, echo back with a mock Prophet response
    if message:
        await sio.emit('prophet_chat_response', {
            'message': f"Prophet (mock): You asked about '{message[:50]}...'",
            'timestamp': data.get('timestamp')
        }, to=sid)


# ============== LATE JOINER EVENTS ==============

@sio.event
async def request_join_active_session(sid, data):
    """Player requests to join active session (needs master approval)."""
    session_id = data.get('session_id')
    player_id = data.get('player_id')
    player_name = data.get('player_name')
    master_player_id = data.get('master_player_id')

    if session_id and master_player_id:
        # Send approval request to master
        if session_id in active_sessions and master_player_id in active_sessions[session_id]:
            master_sid = active_sessions[session_id][master_player_id]
            await sio.emit('join_request', {
                'player_id': player_id,
                'player_name': player_name,
                'requesting_sid': sid
            }, to=master_sid)


@sio.event
async def approve_join_request(sid, data):
    """Master approves late joiner."""
    session_id = data.get('session_id')
    player_id = data.get('player_id')
    player_name = data.get('player_name')
    requesting_sid = data.get('requesting_sid')

    if session_id and requesting_sid:
        # Notify approved player
        await sio.emit('join_approved', {
            'session_id': session_id
        }, to=requesting_sid)

        # Broadcast to all players in session
        await sio.emit('player_joined', {
            'player_id': player_id,
            'player_name': player_name,
            'session_id': session_id,
            'late_joiner': True
        }, room=f"session:{session_id}")


@sio.event
async def reject_join_request(sid, data):
    """Master rejects late joiner."""
    requesting_sid = data.get('requesting_sid')
    reason = data.get('reason', 'Master declined your request')

    if requesting_sid:
        await sio.emit('join_rejected', {'reason': reason}, to=requesting_sid)


# Function to get Socket.IO ASGI app
def get_socketio_app(fastapi_app):
    """Wrap FastAPI app with Socket.IO."""
    return socketio.ASGIApp(
        socketio_server=sio,
        other_asgi_app=fastapi_app,
        socketio_path='/socket.io'
    )
