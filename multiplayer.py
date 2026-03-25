import socket
import threading
import pickle
import time

class AndolanExpressMultiplayer:
    def __init__(self, is_host=False, host_ip="localhost", port=5555):
        self.is_host = is_host
        self.host_ip = host_ip
        self.port = port
        self.socket = None
        self.connected = False
        self.player_id = None
        self.opponent = None
        
        # Game state
        self.game_state = {
            'player1': None,  # Host player
            'player2': None,  # Client player  
            'scores': {'player1': 0, 'player2': 0},
            'game_started': False,
            'game_over': False,
            'winner': None
        }

    def start_host(self):
        """Start as host/server (Player 1)"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((self.host_ip, self.port))
            self.socket.listen(1)  # Only allow 1 connection
            self.is_host = True
            self.connected = True
            self.player_id = "player1"
            
            print(f"🎮 Host started on {self.host_ip}:{self.port} - Waiting for Player 2...")
            
            # Accept one connection only
            threading.Thread(target=self._accept_connection, daemon=True).start()
            return True
        except Exception as e:
            print(f"Failed to start host: {e}")
            return False

    def connect_to_host(self):
        """Connect to a host as client (Player 2)"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host_ip, self.port))
            self.connected = True
            self.player_id = "player2"
            
            print("✅ Connected to host! You are Player 2")
            
            # Start listening for messages
            threading.Thread(target=self._listen_for_messages, daemon=True).start()
            return True
        except Exception as e:
            print(f"Failed to connect to host: {e}")
            return False

    def _accept_connection(self):
        """Accept one connection (host only)"""
        try:
            client_socket, address = self.socket.accept()
            self.opponent = client_socket
            print(f"✅ Player 2 connected from {address}")
            
            # Send initial game state to player 2
            self._send_message({
                'type': 'game_state',
                'game_state': self.game_state,
                'player_id': 'player2'
            })
            
            # Start listening for messages from player 2
            threading.Thread(target=self._handle_opponent, daemon=True).start()
            
        except Exception as e:
            print(f"Error accepting connection: {e}")

    def _handle_opponent(self):
        """Handle messages from opponent (host only)"""
        while self.connected:
            try:
                data = self.opponent.recv(4096)
                if not data:
                    break
                    
                message = pickle.loads(data)
                self._process_message(message)
                
            except Exception as e:
                print(f"Error with opponent: {e}")
                break
        
        self._handle_disconnect()

    def _listen_for_messages(self):
        """Listen for messages (client only)"""
        while self.connected:
            try:
                data = self.socket.recv(4096)
                if not data:
                    break
                    
                message = pickle.loads(data)
                self._process_message(message)
                
            except Exception as e:
                if self.connected:
                    print(f"Error receiving message: {e}")
                break
        
        self.connected = False

    def _process_message(self, message):
        """Process incoming messages"""
        msg_type = message.get('type')
        
        if msg_type == 'game_state':
            self.game_state = message['game_state']
            if 'player_id' in message:
                self.player_id = message['player_id']
            print("📊 Game state updated")
            
        elif msg_type == 'player_update':
            opponent_id = 'player1' if self.player_id == 'player2' else 'player2'
            self.game_state[opponent_id] = message['player_data']
            
        elif msg_type == 'score_update':
            opponent_id = 'player1' if self.player_id == 'player2' else 'player2'
            self.game_state['scores'][opponent_id] = message['score']
            print(f"📈 {opponent_id} score: {message['score']}")
            
        elif msg_type == 'game_start':
            self.game_state['game_started'] = True
            print("🎯 Game started!")
            
        elif msg_type == 'game_over':
            self.game_state['game_over'] = True
            self.game_state['winner'] = message.get('winner')
            print(f"🏆 Game over! Winner: {self.game_state['winner']}")

    def _send_message(self, message):
        """Send message to opponent"""
        if not self.connected:
            return
            
        try:
            data = pickle.dumps(message)
            if self.is_host and self.opponent:
                self.opponent.send(data)
            elif not self.is_host:
                self.socket.send(data)
        except Exception as e:
            print(f"Failed to send message: {e}")
            self._handle_disconnect()

    def _handle_disconnect(self):
        """Handle disconnection"""
        self.connected = False
        print("❌ Opponent disconnected")

    # Game methods
    def update_player(self, player_data):
        """Update this player's state and send to opponent"""
        self.game_state[self.player_id] = player_data
        self._send_message({
            'type': 'player_update',
            'player_data': player_data
        })

    def update_score(self, score):
        """Update this player's score and send to opponent"""
        self.game_state['scores'][self.player_id] = score
        self._send_message({
            'type': 'score_update',
            'score': score
        })

    def start_game(self):
        """Host starts the game"""
        if self.is_host:
            self.game_state['game_started'] = True
            self._send_message({
                'type': 'game_start'
            })
            print("🎯 Starting game for both players!")

    def end_game(self, winner):
        """Host ends the game"""
        if self.is_host:
            self.game_state['game_over'] = True
            self.game_state['winner'] = winner
            self._send_message({
                'type': 'game_over',
                'winner': winner
            })
            print(f"🏆 Game ended! Winner: {winner}")

    def get_opponent_data(self):
        """Get opponent's player data"""
        opponent_id = 'player1' if self.player_id == 'player2' else 'player2'
        return self.game_state.get(opponent_id)

    def get_scores(self):
        """Get both players' scores"""
        return self.game_state['scores']

    def is_game_ready(self):
        """Check if both players are connected and ready"""
        if self.is_host:
            return self.opponent is not None
        else:
            return self.connected

    def disconnect(self):
        """Clean up connection"""
        self.connected = False
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
        if self.opponent:
            try:
                self.opponent.close()
            except:
                pass

# Simple test
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "host":
        print("Starting as HOST (Player 1)...")
        game = AndolanExpressMultiplayer(is_host=True)
        if game.start_host():
            # Wait for connection
            while not game.opponent:
                time.sleep(1)
                print("Waiting for Player 2...")
            
            print("Both players connected! Starting game...")
            game.start_game()
            
            # Simulate game
            time.sleep(2)
            game.update_score(100)
            time.sleep(1)
            game.update_score(200)
            time.sleep(1)
            game.end_game("player1")
            
            input("Press Enter to exit...")
            game.disconnect()
    else:
        print("Starting as CLIENT (Player 2)...")
        game = AndolanExpressMultiplayer(is_host=False)
        if game.connect_to_host():
            # Wait for game to end
            while not game.game_state['game_over']:
                time.sleep(1)
            
            print("Game ended!")
            game.disconnect()