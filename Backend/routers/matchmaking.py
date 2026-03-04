#Esta Implementación ya fue testeada con POSTMAN, check

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import asyncio
import time
import uuid
from collections import deque
from typing import Dict, List
from .EventHandler import EventController, EventHandler

router = APIRouter(prefix = "/match")

#Esta clase es bien Funcional
class MatchMakingManager():

    #Estoy crea la clase 
    def __init__(self, time_seconds = 300):
        #Cola Asincronica
        self.queue = deque()

        #Dict de Conecciones
        self.connections = {}

        #Tiempo de Expirado de la Coneccion
        self.timeout = time_seconds

        #Lock para que sólo una corrutina pueda modificar la cola a la vez
        self.lock = asyncio.Lock()

        #condicion de asyncio, sobre el control del Lock, para que el Worker de Match duerma mientras
        self.condition = asyncio.Condition(self.lock)

    #Insertas un UserName
    async def insert_user(self, username, ws):
        joined_at = time.time()
        async with self.condition:
            #Agregamos a las conecciones
            self.connections[username] = {"joined_at": joined_at, "websocket": ws}

            #Agregramos a la cola
            self.queue.append(username)

            #Notificar de un cambio
            self.condition.notify_all()
        return
    
    #Remover un UserName
    async def remove_user(self, username: str):
        async with self.condition:
            self.connections.pop(username, None)
            self.queue.remove(username)
            self.condition.notify_all()
        return
    
    def Generate_ID(self):
        game_id = str(uuid.uuid4())
        return game_id
 
    def verify(self):
        return len(self.queue) >= 2
    
    def NotEmptyQueue(self):
        return len(self.queue) > 0

    async def TimeOutWorker(self):
        while True:
            print("TimeOut Worker Trabajando")
            #Pone a dormir el worker al menos un segundo
            async with self.condition: 
                #Le vamos a poner una condicion       
                await self.condition.wait_for(self.NotEmptyQueue)        
                #Creamos un time y un array de expirados
                now = time.time()
                expired = []
                expired_ws = []
                for username in list(self.queue):
                    if(now - self.connections[username]["joined_at"] > self.timeout):
                        expired.append(username)

                for username in expired:
                    self.queue.remove(username)
                    dataUser = self.connections.pop(username, None)
                    if dataUser:
                        expired_ws.append((username, dataUser["websocket"]))

                if(expired):
                    print("Time Out Worker extrajo Time outs")
                    self.condition.notify_all()

            for username, ws in expired_ws:
                await ws.send_json({
                    "event": "match not found",
                    "reason": "timeout"
                })

                #Cierra la coneccion del Websocket
                await ws.close()
            #Se pone afuera porque bloque el Lock y al  final para que no se haga en la siguiente iteracion
            await asyncio.sleep(1)
              
        return    
        
    #Worker que se encarga de buscar el matching
    @EventController.publisher("match_found")
    async def MatchMakingWorker(self):   
        contador = 0     
        while True:
            contador += 1
            matchFound = False
            print("Match Making Worker Trabajando")
            async with self.condition:
                await self.condition.wait_for(self.verify)

                #Extraimos dos usuarios de la cola
                u1 = self.queue.popleft()
                u2 = self.queue.popleft()

                #Extraerlos de Conexiones
                Info_u1 = self.connections.pop(u1, None)
                Info_u2 = self.connections.pop(u2, None)

                #Generamos el Game ID
                if(Info_u1 and Info_u2):
                    matchFound = True
                    game_id = self.Generate_ID()

                    WebSocket_u1 = Info_u1["websocket"]
                    WebSocket_u2 = Info_u2["websocket"]

                    session_id_u1 = str(uuid.uuid1())
                    session_id_u2 = str(uuid.uuid1())

                    #U1 siempre color negro, U2 siempre color blanco
                    Response_u1 = {"event": "match found", "game_id": game_id, "player_session_id": session_id_u1, "yo":{"username":u1, "color":"black"}, "other": {"username": u2, "color": "white"}}
                    Response_u2 = {"event": "match found", "game_id": game_id, "player_session_id": session_id_u2, "yo":{"username":u2, "color":"white"}, "other": {"username": u1, "color": "black"}}

                    ResponseEvent = {"game_id": game_id, "black": session_id_u1, "white": session_id_u2}

            if matchFound:
                try:
                    await asyncio.gather(WebSocket_u1.send_json(Response_u1),
                                        WebSocket_u2.send_json(Response_u2),
                                        return_exceptions=True)

                    await asyncio.gather(WebSocket_u1.close(),WebSocket_u2.close(),
                                         return_exceptions=True)
                    print("Match Making Worker hay realizado un Match")
                finally:
                    yield ResponseEvent
            else:
                await asyncio.sleep(0)
                print("Partida No encontrada")
        return




manager = MatchMakingManager() 

#Endpoint es el Enpoint de Match

@router.websocket("/")
async def MakeMatch(ws: WebSocket):
    await ws.accept()
    username = None
    try:
        data = await ws.receive_json()
        username = data["username"]
        print(f"el nombre de usuario es {username}")
        await manager.insert_user(username, ws)
        print("usuario insertado exitosomente")
        # Espera pasiva hasta que el cliente cierre
        while True:
            try:
                await ws.receive()
            except RuntimeError:
                #Ya se cerro la conexión
                print(f"El worker cerro la conexion de {username}")
                break

    except WebSocketDisconnect:
        if username:
            print("El cliente cerro la conexion de {username}")
            await manager.remove_user(username)
