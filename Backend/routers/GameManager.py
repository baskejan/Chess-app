#Este es el archivo donde se escribe el Gamemanager
import asyncio 
from typing import Dict, List, Any
import random as rd
from .EventHandler import EventController
from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from starlette.websockets import WebSocketState

#Creemos el Apirouter
router = APIRouter(prefix="/partida")

#Clase para manejar los errores de conexión
class DisconnectionPlayer(Exception):
    pass

class NotPermitedKey(Exception):
    pass

class NotPermitedUser(Exception):
    pass

class NotTurnYet(Exception):
    pass


"""
Definamos la estructura que recibe el gamestate
{
    white: session_id_u1,
    black: session_id_u2,
    turn: color( white or black ),
    board: FenString,
    enpassant: "",
    castling: {white: true, black: true}
    halfmoves:0
    fullmoves:0
}
"""
#Clase que se encarga de manejar el estado del juego
class GameState:
    __slots__ = ["white", "black", "turn", "board", "enpassant", "castling", "halfmoves","fullmoves", "state", "winner", "num_players", "lock", "condition", "moves", "reason", "desc", "first"]
    def __init__(self, **kwargs):
        PermitedAttibutes = {"white", "black", "turn", "board", "enpassant", "castling", "halfmoves","fullmoves"}
        for clave, valor in kwargs.items():
            if clave in PermitedAttibutes:
                setattr(self, clave, valor)
            else:
                raise NotPermitedKey(f"La clave {clave} no esta permitida en GameState")
        
        self.state: bool = False #Esto significa que la partida no ha iniciado todavía
        self.desc: Dict[str, bool] = {self.white: False, self.black: False} #Esto permite registrar sí hay desconexión por usuario
        self.winner = None
        self.reason = ""
        self.first = "" #Primer Usuario que se desconecta
        self.lock = asyncio.Lock()
        #Le pasamos el Lock al condition
        self.condition = asyncio.Condition(self.lock)
        self.num_players = 0
        self.moves = []

    def is_turn(self, player_id: str) -> bool:
        if self.white == player_id:
            color_player = "white"
        else:
            color_player = "black"
        

        if self.turn == color_player:
            return True
        else:
            return False
    
    def change_turn(self):
        if self.turn == "white":
            self.turn = "black"
        else:
            self.turn = "white"
    
    def handle_move(self, player_id: str, move: Dict): 
        self.moves.append(move)
        print(f"El jugador {player_id} hizo este movimiento {move}")

    def finish(self, move: str):
        if len(self.moves) < 10:
            return False
        else:
            return True
    
    def set_winner(self, player_id: str, reason: str = ""):
        if reason != "":
            self.reason = reason
        else:
            if self.white == player_id:
                self.winner = self.white
            else:
                self.winner = self.black

    def get_other_player(self, player_id):
        if player_id == self.white:
            return self.black
        else:
            return self.white
        
    def getFenString(self):
        return "Here goes the Fen String"

#Creemos las clase que se encarga de ser el GameManager

class GameManager:
    def __init__(self):
        self.connections: Dict[str, WebSocket] = {}
        self.games: Dict[str, GameState] = {}
        self.lock = asyncio.Lock()
        self.condition = asyncio.Condition(self.lock)    
    
        
    async def add_connection(self, player_id: str, ws: WebSocket):
        async with self.condition:
            self.connections[player_id] = ws
      

    async def remove_connection(self, player_id: str):
        async with self.condition:
            _ = self.connections.pop(player_id, None)


    #Este es el metodo que vamos a decorar con el EventHandler.suscriber
    @EventController.subscriber("match_found")
    async def CreateGame(self, GameInfo: Dict = None):
            print(f"Hemos recibido un nuevo evento {GameInfo}")
            game_id = GameInfo.pop("game_id")

            #Agregar elementos del tablero al GameInfo
            GameInfo["turn"] = "white"
            GameInfo["board"] = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR"
            GameInfo["enpassant"] = ""
            GameInfo["castling"] = {"white": True, "black": True}
            GameInfo["halfmoves"] = 0
            GameInfo["fullmoves"] = 0

            #Adquirimos el Lock para modificar el diccionario de conexiones y agregar la partida
            async with self.condition:
                #Agregamos el gameInfo al diccionario de juegos
                self.games[game_id] = GameState(**GameInfo)

                #Notificamos a la otra corrutina que ya esta lista la partida
                self.condition.notify_all()
        
    def game_ready(self, game_id: str):
        if game_id in self.games:
            return True
        else:
            return False

    async def wait_for_game(self, game_id: str) -> bool:  
        #Si retorna True es porque ya partida fue creada con exito,
        #En caso contrario retorna false
        async with self.condition:
            await self.condition.wait_for(lambda: self.game_ready(game_id))        
        return True

    
    async def notify_both_players(self, game_id):
        try:
            game = self.games[game_id]
            player_conn1_num = game.white
            player_conn2_num = game.black
            ws1 = self.connections.get(player_conn1_num, None)
            ws2 = self.connections.get(player_conn2_num, None)
            if ws1 and ws2:
                if ws1.client_state == WebSocketState.CONNECTED and ws2.client_state == WebSocketState.CONNECTED:
                    await asyncio.gather(
                        ws1.send_json({"event": "turn change", "board": game.board, "turn": game.turn}), 
                        ws2.send_json({"event": "turn change", "board": game.board, "turn": game.turn}),
                    return_exceptions=True)
        except Exception as e:
            print("Hubo un error {e}")    

    

        

#Creamos la instancia del GameManager

game_manager = GameManager()    
#Endpoint para manejar la entrada de los websockets al juego


@router.websocket("/{game_id}")
async def EnterGame(ws: WebSocket, game_id: str, player_id: str):
    await ws.accept()
    
    try:
        # 1. Espera de cortesía para que la partida esté creada
        if not await game_manager.wait_for_game(game_id):
            print(f"Tiempo excedido esperando partida {game_id}")
            await ws.close(code=4008)
            return

        # Agregamos la conexión al manager
        await game_manager.add_connection(player_id, ws)
        game = game_manager.games[game_id]

        # 2. Sincronización de entrada (Magic Code)
        async with game.condition:
            game.num_players += 1
            game.condition.notify_all() 

            if game.num_players < 2:
                # El primer jugador espera al segundo
                await game.condition.wait_for(lambda: game.num_players == 2)
            else:
                # El segundo jugador activa el inicio de la partida
                game.state = True
                #await game_manager.notify_start_game()
                game.condition.notify_all() 

        print(f"La partida {game_id} ya va a iniciar")
        # 3. Bucle Principal de Juego

        while True:
            # --- FASE A: Esperar Turno (Con Lock) ---
            print(f"Estoy en la fase A game_id: {player_id} ")
            async with game.condition:
                # Esperamos nuestro turno O que el juego termine (por desconexión ajena)
                opponent_id =  game.get_other_player(player_id) 
                await game.condition.wait_for(lambda: game.is_turn(player_id) or not game.state or game.desc[opponent_id])
                if not game.state or game.desc[opponent_id]:
                    break
            
            
            # --- FASE B: Recibir Movimiento (Sin Lock) ---
            # El servidor espera aquí el input del usuario sin bloquear a otros
            try:
                print(f"Estoy en la fase B game_id: {player_id} ")
                async with game.condition:
                    if not game.check_mate:
                        await ws.send_text("Ya puedes mover")
                        move: Dict = await ws.receive_json()
            except WebSocketDisconnect:
                print(f"El jugador {player_id} se desconecto movimiendo")
                async with game.condition:
                    game.desc[player_id] = True
                    game.state = False
                    if game.first == "":
                        game.first = player_id
                    game.condition.notify_all()
                break
            except Exception as e:
                print("Error Desconocido")
                async with game.condition:
                    game.desc[player_id] = True
                    game.state = False
                    if game.first == "":
                        game.first = player_id
                    game.condition.notify_all()
                break
            

            # --- FASE C: Procesar Jugada (Con Lock) ---
            print(f"Estoy en la fase C game_id: {player_id} ")
            async with game.condition:
                # Re-verificar estado por si el rival se fue mientras pensábamos el movimiento
                if not game.state or game.desc[opponent_id]:
                    break

                # Ejecutamos la lógica de fin de juego o movimiento normal
                if not game.finish(move):
                    # El juego continúa: actualizamos tablero y cambiamos turno
                    game.handle_move(player_id, move)
                    game.change_turn()

                    #Esta función sólo se ejecuta sí ambas conexiones siguen abiertas
                    #En caso contrario no envía nada
                    await game_manager.notify_both_players(game_id)

                    #Despertamos al rival
                    game.condition.notify_all() 
                else:
                    game.state = False
                    game.set_winner(player_id)
                    game.condition.notify_all() 
                    # Despertamos al rival para que salga de su wait_for
                    break
    
    except WebSocketDisconnect as e:
        print(f"El  usuario {player_id} se ha desconectado antes de que sea su turno")
        async with game.condition:
            game.desc[player_id] = True
            game.state = False
            if game.first == "":
                game.first = player_id
            game.condition.notify_all()                  

    except Exception as e:
        print("Error Desconocido")
        async with game.condition:
            game.desc[player_id] = True
            game.state = False
            if game.first == "":
                game.first = player_id
            game.condition.notify_all()                  


    finally:         
        #Hubo desconexión de alguno de los jugadores
        if game.first != "":
            print(f"Un jugador se desconecto, nombre: {game.first}")
            #Declaramos ganador al otro jugador
            other_id = game.get_other_player(game.first)
            if game.winner is None:
                game.set_winner(other_id, reason="abandon")
            
            
        print("Cerrando la conexión")
        if ws.client_state == WebSocketState.CONNECTED:
            await ws.close()

        #Printeamos la información de la partida
        print(f"Partida Info: \n {game.__dict__}")            

        #Limpieza del diccionario de conexiones
        await game_manager.remove_connection(player_id)        
        print(f"Limpieza de recursos completada para {player_id}.")

        


