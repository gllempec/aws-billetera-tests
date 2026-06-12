// Importamos el modulo "http" de k6: permite hacer peticiones HTTP (GET, POST, etc.)
import http from 'k6/http';
// Importamos "check" (para validar respuestas) y "sleep" (para pausar entre iteraciones)
import { check, sleep } from 'k6';

// "options" configura COMO se ejecuta la prueba de carga
export const options = {
  // "stages": como va subiendo/bajando la cantidad de usuarios virtuales (VUs) en el tiempo
  stages: [
    { duration: '5s', target: 5 },   // ramp-up: en 5 segundos, subimos de 0 a 5 usuarios virtuales
    { duration: '10s', target: 5 },  // mantenemos 5 usuarios virtuales constantes por 10 segundos
    { duration: '5s', target: 0 },   // ramp-down: bajamos de 5 a 0 usuarios virtuales
  ],
  // "thresholds": los CRITERIOS DE EXITO/FALLO de la prueba (criterios de aceptacion de performance)
  thresholds: {
    // El 95% de las peticiones debe responder en menos de 500ms
    http_req_duration: ['p(95)<500'],
    // Menos del 1% de las peticiones puede fallar (status != 2xx/3xx)
    http_req_failed: ['rate<0.01'],
  },
};

// "default function": el codigo que CADA usuario virtual repite una y otra vez
export default function () {
  // Hacemos un GET al sitio oficial de pruebas de k6
  // (en un escenario real, esta seria la URL de tu API Gateway -> Lambda)
  const respuesta = http.get('https://test.k6.io');

  // "check" valida la respuesta y cuenta cuantas veces se cumple (se ve en el reporte final)
  check(respuesta, {
    'status es 200': (r) => r.status === 200,
  });

  // Cada usuario virtual espera 1 segundo antes de repetir (simula tiempo real entre acciones)
  sleep(1);
}
