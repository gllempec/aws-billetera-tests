# Importamos boto3 para crear el cliente de DynamoDB (simulado) y poder crear la tabla
import boto3
# Importamos pytest para poder definir "fixtures" (preparativos automaticos para los tests)
import pytest
# Importamos mock_aws para simular TODOS los servicios de AWS dentro del bloque "with"
from moto import mock_aws


# @pytest.fixture(autouse=True) hace que ESTA preparacion se ejecute SOLA, antes de CADA test,
# sin que cada test tenga que pedirla explicitamente (asi todos los tests tienen AWS simulado + tabla lista)
@pytest.fixture(autouse=True)
def aws_simulado():
    # "with mock_aws():" activa la simulacion de AWS solo dentro de este bloque
    with mock_aws():
        # Creamos un cliente de DynamoDB (simulado) para poder crear la tabla
        dynamodb = boto3.client("dynamodb", region_name="us-east-1")

        # Creamos la tabla que lambda_handler usa para idempotencia
        dynamodb.create_table(
            TableName="transferencias-procesadas",
            KeySchema=[{"AttributeName": "transferencia_id", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "transferencia_id", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )

        # "yield" entrega el control al test; todo lo de arriba es "preparacion" (setup)
        yield
