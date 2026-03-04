from typing import Callable, AsyncGenerator, List, Dict, Any, Set
import asyncio
from functools import wraps

class NotEventCreated(Exception):
    pass

class EventHandler:
    def __init__(self, AvailableEvents: List[str]):
        # Ahora solo necesitamos las colas. Cada evento tiene su propia Queue.
        self.queues: Dict[str, asyncio.Queue] = {
            name: asyncio.Queue() for name in AvailableEvents
        }


    async def emit(self, event_name: str, value: Any):
        """Envía un dato a la cola del evento correspondiente."""
        if event_name in self.queues:
            # put_nowait añade el elemento sin bloquear el flujo actual
            print(f"El game id es {value["game_id"]}")
            self.queues[event_name].put_nowait(value)
            await asyncio.sleep(0)
        else:
            raise NotEventCreated(f"El evento '{event_name}' no existe.")
            
        
    def publisher(self, event_name: str):
        """Decorador para funciones que generan datos (AsyncGenerators)."""
        def decorator(func: Callable[..., AsyncGenerator]):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                async for value in func(*args, **kwargs):
                    print(f" Emitiendo evento: {event_name}")
                    await self.emit(event_name, value)
            return wrapper
        return decorator

    def subscriber(self, event_name: str):
        def decorator(func):
            async def wrapper(*args, **kwargs):
                #Este condicional permite suscribir la función a un evento específico
                if event_name in self.queues:
                    while True:
                        #Await mientras la cola este vacía, y cuando hay un evento lo captura
                        EventInfo = await self.queues[event_name].get()
                        #Aqui va la lógica del suscriptor
                        await func(GameInfo = EventInfo, *args, **kwargs)
                        await asyncio.sleep(0)
                else:
                    raise NotEventCreated(f"El evento '{event_name}' no existe.")              
            return wrapper
        return decorator    

#Creemos una instancia del EventHandler
EventController = EventHandler(["match_found"])