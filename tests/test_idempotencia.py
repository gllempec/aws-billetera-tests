# Importamos json para armar el "body" del mensaje, igual que llegaria desde SQS
import json

# Importamos allure: permite agregar "metadata" al test (titulo, severidad, descripcion)
# que despues se ve en el reporte HTML, no solo PASSED/FAILED
import allure

# Importamos lambda_handler, la funcion que vamos a probar
from src.lambda_handler import lambda_handler


# @allure.title: el nombre "legible" que aparece en el reporte (en vez del nombre de la funcion)
@allure.title("Una transferencia duplicada (re-entrega de SQS) no se procesa dos veces")
# @allure.severity: que tan grave es si este test falla. CRITICAL porque significaria doble pago real
@allure.severity(allure.severity_level.CRITICAL)
# @allure.description: texto largo explicando el escenario, visible al hacer click en el test
@allure.description(
    "SQS garantiza 'at-least-once delivery': el mismo mensaje puede llegar mas de una vez. "
    "Esta prueba simula esa re-entrega y verifica que la Lambda detecte el duplicado via "
    "DynamoDB (conditional write) y NO reprocese la transferencia, evitando un doble pago."
)
# @allure.tag: etiquetas para filtrar/agrupar en el reporte (ej: ver solo tests de "idempotencia")
@allure.tag("idempotencia", "race-condition")
# Este test simula lo que SQS llama "at-least-once delivery": el MISMO mensaje
# puede llegarle a la Lambda mas de una vez. La idempotencia debe evitar el doble procesamiento.
def test_transferencia_duplicada_no_se_procesa_dos_veces():
    # Armamos UN mensaje de transferencia (lo vamos a "entregar" dos veces)
    mensaje = {
        "body": json.dumps({
            "transferencia_id": "TX999",
            "monto": 500,
            "estado": "CONFIRMADA",
        })
    }

    # Primera entrega: la Lambda procesa el mensaje normalmente
    primer_resultado = lambda_handler({"Records": [mensaje]}, None)

    # Segunda entrega: SQS reenvia el MISMO mensaje (duplicado)
    segundo_resultado = lambda_handler({"Records": [mensaje]}, None)

    # La primera vez se procesa con normalidad
    assert primer_resultado["resultados"][0] == {"id": "TX999", "procesado": True}

    # La segunda vez se detecta como duplicado: NO se vuelve a procesar
    assert segundo_resultado["resultados"][0] == {
        "id": "TX999",
        "procesado": False,
        "motivo": "duplicado",
    }
