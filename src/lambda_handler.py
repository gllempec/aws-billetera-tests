# Importamos la herramienta "json", que convierte texto <-> diccionario
import json
# Importamos "logging", para poder dejar mensajes en el "diario" de CloudWatch
import logging
# Importamos boto3, la libreria oficial de AWS para Python
import boto3
# Importamos ClientError: la excepcion que boto3 lanza cuando AWS RECHAZA una operacion
from botocore.exceptions import ClientError

# Creamos un "logger": el objeto que vamos a usar para escribir mensajes en el diario
logger = logging.getLogger()
# Configuramos el nivel minimo de mensajes que queremos ver (INFO y mas importantes)
logger.setLevel(logging.INFO)

# Nombre de la tabla DynamoDB que usamos solo para "marcar" transferencias ya procesadas
TABLA_IDEMPOTENCIA = "transferencias-procesadas"


# Definimos la funcion "lambda_handler": el "empleado" que AWS llama cuando llega un evento.
# Siempre recibe 2 parametros: event (los datos del mensaje) y context (info tecnica, casi no se usa)
def lambda_handler(event, context):
    # Creamos una lista vacia ("canasta") donde vamos a guardar el resultado de cada transferencia
    resultados = []

    # Creamos el recurso de DynamoDB DENTRO del handler (no a nivel de modulo).
    # Si lo creamos a nivel de modulo, se crea ANTES de que el mock de AWS (moto) este activo
    # en los tests, y boto3 queda "sin credenciales" para siempre. Creandolo aqui,
    # se crea en el momento de cada invocacion, ya con el mock activo.
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
    # Obtenemos una referencia a la tabla de idempotencia
    tabla = dynamodb.Table(TABLA_IDEMPOTENCIA)

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

        transferencia_id = transferencia["transferencia_id"]

        # IDEMPOTENCIA: intentamos "reservar" este ID escribiendolo en la tabla.
        # ConditionExpression hace que la escritura FALLE si el ID YA existe en la tabla.
        # Esto es lo que evita procesar dos veces la misma transferencia (race condition / duplicados de SQS)
        try:
            tabla.put_item(
                Item={"transferencia_id": transferencia_id},
                ConditionExpression="attribute_not_exists(transferencia_id)",
            )
        # Si DynamoDB rechaza la escritura, boto3 lanza un ClientError
        except ClientError as error:
            # Revisamos el "codigo" del error: si es justo el de la condicion, es un duplicado
            if error.response["Error"]["Code"] == "ConditionalCheckFailedException":
                # Anotamos en el diario que detectamos un duplicado
                logger.warning("Transferencia duplicada, ya procesada antes: %s", transferencia_id)
                # La marcamos como no procesada, indicando el motivo
                resultados.append({"id": transferencia_id, "procesado": False, "motivo": "duplicado"})
                # Saltamos al siguiente mensaje: NO la procesamos de nuevo
                continue
            # Si es otro tipo de error (no esperado), lo dejamos "subir" sin esconderlo
            raise

        # Si el monto es positivo Y el estado es "CONFIRMADA"...
        if transferencia["monto"] > 0 and transferencia["estado"] == "CONFIRMADA":
            # ...agregamos a la canasta un resultado marcado como procesado=True
            resultados.append({"id": transferencia_id, "procesado": True})
        else:
            # Si no cumple esas condiciones, lo marcamos como procesado=False
            resultados.append({"id": transferencia_id, "procesado": False})

    # Devolvemos un diccionario con la lista de resultados, una vez procesados todos los mensajes
    return {"resultados": resultados}
