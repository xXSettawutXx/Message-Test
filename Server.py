import asyncio
import websockets
import json
from datetime import datetime

# เก็บข้อมูลห้องเกมและผู้เล่น
games = {}
waiting_players = []

class Game:
    def __init__(self, room_id):
        self.room_id = room_id
        self.players = []
        self.board = [["", "", ""], ["", "", ""], ["", "", ""]]
        self.current_turn = "X"
        self.game_started = False
        self.game_over = False
        self.winner = None
        
    def add_player(self, websocket, player_id):
        symbol = "X" if len(self.players) == 0 else "O"
        self.players.append({
            "websocket": websocket,
            "id": player_id,
            "symbol": symbol
        })
        if len(self.players) == 2:
            self.game_started = True
        return symbol
    
    def remove_player(self, websocket):
        self.players = [p for p in self.players if p["websocket"] != websocket]
        if len(self.players) == 0:
            return True  # ห้องว่าง ลบได้
        return False
    
    def make_move(self, x, y, symbol):
        if self.board[x][y] == "" and self.current_turn == symbol and not self.game_over:
            self.board[x][y] = symbol
            
            # ตรวจสอบชนะ
            if self.check_win():
                self.game_over = True
                self.winner = symbol
                return True
            
            # ตรวจสอบเสมอ
            if self.check_draw():
                self.game_over = True
                self.winner = "DRAW"
                return True
            
            # สลับตา
            self.current_turn = "O" if self.current_turn == "X" else "X"
            return True
        return False
    
    def check_win(self):
        # ตรวจแนวนอน
        for i in range(3):
            if self.board[i][0] == self.board[i][1] == self.board[i][2] != "":
                return True
        
        # ตรวจแนวตั้ง
        for i in range(3):
            if self.board[0][i] == self.board[1][i] == self.board[2][i] != "":
                return True
        
        # ตรวจแนวทแยง
        if self.board[0][0] == self.board[1][1] == self.board[2][2] != "":
            return True
        if self.board[2][0] == self.board[1][1] == self.board[0][2] != "":
            return True
        
        return False
    
    def check_draw(self):
        for row in self.board:
            for cell in row:
                if cell == "":
                    return False
        return True
    
    def reset(self):
        self.board = [["", "", ""], ["", "", ""], ["", "", ""]]
        self.current_turn = "X"
        self.game_over = False
        self.winner = None

async def handle_client(websocket, path):
    player_id = id(websocket)
    current_game = None
    player_symbol = None
    
    try:
        async for message in websocket:
            data = json.loads(message)
            action = data.get("action")
            
            # JOIN GAME - เข้าร่วมเกม
            if action == "join":
                room_id = data.get("room_id", "default")
                
                # สร้างห้องใหม่ถ้ายังไม่มี
                if room_id not in games:
                    games[room_id] = Game(room_id)
                
                current_game = games[room_id]
                
                # ตรวจสอบว่าห้องเต็มหรือยัง
                if len(current_game.players) >= 2:
                    await websocket.send(json.dumps({
                        "type": "error",
                        "message": "Room is full"
                    }))
                    continue
                
                player_symbol = current_game.add_player(websocket, player_id)
                
                # ส่งข้อมูลเริ่มต้น
                await websocket.send(json.dumps({
                    "type": "joined",
                    "symbol": player_symbol,
                    "room_id": room_id,
                    "players_count": len(current_game.players)
                }))
                
                # ถ้าครบ 2 คน เริ่มเกม
                if current_game.game_started:
                    for player in current_game.players:
                        await player["websocket"].send(json.dumps({
                            "type": "game_start",
                            "current_turn": current_game.current_turn
                        }))
            
            # MOVE - ทำการเดิน
            elif action == "move":
                if current_game and player_symbol:
                    x = data.get("x")
                    y = data.get("y")
                    
                    if current_game.make_move(x, y, player_symbol):
                        # ส่งอัพเดทให้ทุกคน
                        game_state = {
                            "type": "board_update",
                            "board": current_game.board,
                            "current_turn": current_game.current_turn,
                            "game_over": current_game.game_over,
                            "winner": current_game.winner
                        }
                        
                        for player in current_game.players:
                            await player["websocket"].send(json.dumps(game_state))
                    else:
                        await websocket.send(json.dumps({
                            "type": "error",
                            "message": "Invalid move"
                        }))
            
            # RESET - เริ่มเกมใหม่
            elif action == "reset":
                if current_game:
                    current_game.reset()
                    
                    for player in current_game.players:
                        await player["websocket"].send(json.dumps({
                            "type": "game_reset",
                            "board": current_game.board,
                            "current_turn": current_game.current_turn
                        }))
            
            # PING - ตรวจสอบการเชื่อมต่อ
            elif action == "ping":
                await websocket.send(json.dumps({
                    "type": "pong"
                }))
    
    except websockets.exceptions.ConnectionClosed:
        print(f"Player {player_id} disconnected")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # ลบผู้เล่นออกจากห้อง
        if current_game:
            is_empty = current_game.remove_player(websocket)
            
            # แจ้งผู้เล่นอื่นว่ามีคนออก
            for player in current_game.players:
                try:
                    await player["websocket"].send(json.dumps({
                        "type": "player_left",
                        "players_count": len(current_game.players)
                    }))
                except:
                    pass
            
            # ลบห้องถ้าไม่มีคน
            if is_empty and current_game.room_id in games:
                del games[current_game.room_id]

async def main():
    print("WebSocket Server starting on port 10000...")
    async with websockets.serve(handle_client, "0.0.0.0", 10000):
        print("Server is running!")
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())
