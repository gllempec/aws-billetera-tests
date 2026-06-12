# Importamos la herramienta "json", que convierte texto <-> diccionario
import json
# Importamos "logging", para poder dejar mensajes en el "diario" de CloudWatch
import logging

# Creamos un "logger": el objeto que vamos a usar para escribir mensajes en el diario
logger = logging.getLogger()
# Configuramos el nivel minimo de mensajes que queremos ver (INFO y mas importantes)
logger.setLevel(logging.INFO)


# Definimos la funcion "lambda_handler": el "empleado" que AWS llama cuando llega un evento.
# Siempre recibe 2 parametros: event (los datos del mensaje) y context (info tecnica, casi no se usa)
def lambda_handler(event, context):
    # Creamos una lista vacia ("canasta") donde vamos a guardar el resultado de cada transferencia
    resultados = []

    # Recorremos cada mensaje (registro) dentro de la lista event["Records"]
    for registro in event["Records"]:
        # Intentamos convertir el texto JSON de registro["body"] en un diccionario de Python
        try:
            transferencia = json.loads(registro["body"])
        # Si el texto NO es JSON valido, Python lanza json.JSONDecodeError: lo "atrapamos" aca
        except json.JSONDecodeError:
            # Anotamos en el diario que este mensaje vino mal, con su contenido
            logger.error("Mensaje invalido, no es JSON: %s", registro["body"])
            # "continue" salta al siguiente mensaje del for, sin frenar todo
            continue

        # Si el monto es positivo Y el estado es "CONFIRMADA"...
        if transferencia["monto"] > 0 and transferencia["estado"] == "CONFIRMADA":
            # ...agregamos a la canasta un resultado marcado como procesado=True
            resultados.append({"id": transferencia["transferencia_id"], "procesado": True})
        else:
            # Si no cumple esas condiciones, lo marcamos como procesado=False
            resultados.append({"id": transferencia["transferencia_id"], "procesado": False})

    # Devolvemos un diccionario con la lista de resultados, una vez procesados todos los mensajes
    return {"resultados": resultados}
