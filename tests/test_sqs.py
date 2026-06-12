# Importamos json para convertir el diccionario del mensaje a texto JSON
import json
# Importamos boto3, la libreria oficial de AWS para Python
import boto3


# Ya no necesitamos @mock_aws aqui: el fixture "aws_simulado" en conftest.py
# activa la simulacion de AWS automaticamente para TODOS los tests
def test_enviar_y_recibir_mensaje_de_transferencia():
    # Creamos un "cliente" de SQS: un objeto que sabe hablar con el servicio SQS (simulado)
    sqs = boto3.client("sqs", region_name="us-east-1")

    # Usamos el metodo create_queue (del objeto sqs) para crear una cola nueva
    cola = sqs.create_queue(QueueName="transferencias-confirmadas")
    # Guardamos la URL de la cola, necesaria para enviar/recibir mensajes
    queue_url = cola["QueueUrl"]

    # Armamos un diccionario con los datos de una transferencia de ejemplo
    mensaje = {
        "transferencia_id": "TX123",
        "monto": 1500.50,
        "estado": "CONFIRMADA"
    }

    # Enviamos el mensaje a la cola, convirtiendo el diccionario a texto JSON con json.dumps
    sqs.send_message(QueueUrl=queue_url, MessageBody=json.dumps(mensaje))

    # Pedimos a la cola hasta 1 mensaje disponible
    respuesta = sqs.receive_message(QueueUrl=queue_url, MaxNumberOfMessages=1)

    # Si hay mensajes, vienen en la clave "Messages"; si no hay, devolvemos una lista vacia
    mensajes = respuesta.get("Messages", [])

    # Verificamos que recibimos exactamente 1 mensaje
    assert len(mensajes) == 1
    # Convertimos el texto JSON del mensaje recibido de vuelta a un diccionario
    contenido = json.loads(mensajes[0]["Body"])
    # Verificamos que los datos sean los que enviamos
    assert contenido["transferencia_id"] == "TX123"
    assert contenido["estado"] == "CONFIRMADA"
