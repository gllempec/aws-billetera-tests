# Importamos json para poder armar el "body" de cada mensaje en formato texto JSON
import json

# Importamos lambda_handler desde src/lambda_handler.py
# (esto funciona porque conftest.py marca la raiz del proyecto, y Python busca "src" desde ahi)
from src.lambda_handler import lambda_handler


# pytest ejecuta automaticamente cualquier funcion que empiece con "test_"
def test_lambda_handler_procesa_transferencia():

    # Armamos un evento "falso" con la misma forma que el real de AWS:
    # un diccionario con la clave "Records", que vale una lista de mensajes
    event = {
        "Records": [
            {
                # json.dumps convierte este diccionario en texto JSON,
                # simulando el "body" real que llega desde SQS
                "body": json.dumps({
                    "transferencia_id": "TXT123",
                    "monto": 1500.50,
                    "estado": "CONFIRMADA",
                })
            },
            {
                # Este segundo mensaje tiene monto negativo: deberia ser rechazado
                "body": json.dumps({
                    "transferencia_id": "TX456",
                    "monto": -100,
                    "estado": "CONFIRMADA",
                })
            },
        ]
    }

    # Llamamos a lambda_handler tal como lo haria AWS: con el evento y "context" en None
    resultado = lambda_handler(event, None)

    # El primer mensaje (monto positivo, CONFIRMADA) deberia quedar procesado=True
    assert resultado["resultados"][0] == {"id": "TXT123", "procesado": True}
    # El segundo mensaje (monto negativo) deberia quedar procesado=False
    assert resultado["resultados"][1] == {"id": "TX456", "procesado": False}
