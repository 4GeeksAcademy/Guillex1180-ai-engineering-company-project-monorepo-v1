# Propuesta de Arquitectura de Backend

Documento técnico para el CTO. Define la arquitectura objetivo del backend en FastAPI para TrackFlow, una vez finalizados los cuatro hitos del sitio corporativo y con foco en la siguiente fase: capacidades transaccionales y analíticas para operación logística.

## 1. Contexto y Objetivos del Sistema

TrackFlow opera logística de última milla y almacén para clientes B2B (marcas e-commerce) y atiende también casos B2C (destinatarios finales). En los hitos previos se completó el sitio corporativo y la capa de presentación; ahora la necesidad estratégica es habilitar un backend robusto que soporte flujos operativos reales, no solo contenido estático.

Actores y flujos críticos del negocio que condicionan la arquitectura:

1. Equipo CX (Valentina Cruz y agentes de soporte): requiere trazabilidad de incidentes, tiempos de respuesta consistentes y datos confiables para priorizar casos.
2. Operación logística (US y ES): necesita reglas por país y carrier, consistencia en estados y visibilidad para decisiones diarias.
3. Stakeholders internos (CEO, Tech Lead, analítica): demandan métricas estables y auditables para productividad, satisfacción y calidad operativa.
4. Frontend corporativo y futuros clientes internos: necesitan contratos API versionados para evolución sin ruptura.

Objetivos del backend:

1. Exponer una API REST versionada para gestionar incidentes, autenticación, usuarios y análisis.
2. Garantizar separación entre reglas de negocio, transporte HTTP y persistencia.
3. Proteger datos sensibles y estandarizar configuración por entorno.
4. Permitir escalado progresivo del producto sin reescritura temprana.

## 2. Patrón Arquitectónico y Justificación Contextual

Patrón propuesto: Monolito Modular con Arquitectura en Capas por Dominio.

Justificación contextual (negocio, usuarios y flujos):

1. El flujo principal de TrackFlow (captura de incidentes, validación, priorización y análisis) comparte transacciones y reglas comunes; dividir desde el inicio en microservicios encarecería coordinación operativa y observabilidad distribuida sin valor inmediato.
2. El equipo CX necesita cambios frecuentes en reglas de clasificación y reporting. Un monolito modular permite iterar rápido en un solo despliegue, manteniendo límites de dominio para evitar contaminación entre módulos.
3. Existen variaciones de negocio por país (US/ES), carrier y tipo de cliente (B2B/B2C). Encapsular estas reglas por dominio y servicio reduce regresiones cuando cambien políticas comerciales.
4. La organización todavía está consolidando procesos internos tras los hitos del frontend. Mantener una unidad desplegable simplifica operación, soporte y onboarding, pero con modularidad suficiente para extraer servicios en el futuro si aparece presión real de escala.

Decisiones descartadas con criterio:

1. Microservicios desde día 1: descartado por costo operativo alto (tracing, contratos distribuidos, despliegues coordinados) para el nivel actual de madurez.
2. Monolito en capas sin dominios: descartado porque tiende a concentrar lógica en archivos transversales y aumenta acoplamiento entre equipos.

## 3. Estructura de Carpetas y Módulos del Backend

Se propone mantener FastAPI bajo app y separar por dominios funcionales en modules. Estructura recomendada:

```text
services/
  api/
    app/
      main.py
      api/
        router.py
        deps.py
      core/
        config.py
        security.py
        logging.py
        exceptions.py
      db/
        base.py
        session.py
        migrations/
      modules/
        auth/
          routers/
            auth_router.py
          schemas/
            auth_schemas.py
          models/
            user_model.py
            role_model.py
          services/
            auth_service.py
            token_service.py
          repositories/
            user_repository.py
        users/
          routers/
            users_router.py
          schemas/
            users_schemas.py
          models/
            profile_model.py
          services/
            users_service.py
          repositories/
            users_repository.py
        incidents/
          routers/
            incidents_router.py
            incidents_analysis_router.py
          schemas/
            incidents_schemas.py
            incidents_analysis_schemas.py
          models/
            incident_model.py
            analysis_model.py
          services/
            incidents_service.py
            incidents_analysis_service.py
          repositories/
            incidents_repository.py
            analysis_repository.py
      shared/
        dto/
        utils/
      tests/
        unit/
        integration/
        contract/
```

Criterio de separación y responsabilidades:

1. routers: capa HTTP. Solo recibe requests, invoca servicios y devuelve responses.
2. schemas: contratos de entrada/salida y validaciones con Pydantic.
3. models: mapeo ORM a tablas; sin lógica de aplicación.
4. services: reglas de negocio y casos de uso.
5. repositories: acceso a datos y consultas persistentes.
6. core: configuración, seguridad y concerns transversales.
7. shared: componentes reutilizables no acoplados a un dominio concreto.

Regla arquitectónica clave: dependencias unidireccionales api -> services -> repositories -> db.

## 4. Organización de Endpoints y Routers en FastAPI

Estrategia de modularización con APIRouter:

1. Cada dominio mantiene sus routers en archivos independientes bajo modules/<dominio>/routers.
2. app/api/router.py agrega todos los routers por versión.
3. main.py monta el router raíz y middlewares.

Jerarquía de rutas propuesta (v1):

1. /api/v1/auth
2. /api/v1/users
3. /api/v1/incidents
4. /api/v1/incidents/analysis
5. /api/v1/health

Ejemplo de agrupación OpenAPI por tags:

1. tags=["Auth"] en auth_router.py
2. tags=["Users"] en users_router.py
3. tags=["Incidents"] en incidents_router.py
4. tags=["Incident Analysis"] en incidents_analysis_router.py

Lineamientos obligatorios:

1. No existe un archivo único de endpoints.
2. El versionado va en URL (/api/v1, /api/v2) para cambios incompatibles.
3. Cambios aditivos dentro de v1 no rompen clientes.

## 5. Convenciones Estándar de la Comunidad FastAPI

Convenciones tomadas de la documentación oficial y práctica idiomática de la comunidad FastAPI:

1. FastAPI docs: APIRouter por módulo, dependency injection con Depends y generación OpenAPI automática.
2. Pydantic docs: validación declarativa y contratos tipados para request/response.
3. SQLAlchemy/SQLModel docs: separación de persistencia, sesión por request y mapeo ORM consistente.
4. pydantic-settings docs: configuración tipada centralizada desde entorno y archivos .env.

Cómo influyen estas convenciones en la propuesta:

1. Separation of concerns estricta:
   - routers gestionan HTTP,
   - schemas validan,
   - models persisten,
   - services aplican negocio.
2. Configuración centralizada en core/config.py mediante Settings:
   - lectura de ENV, DATABASE_URL, JWT_SECRET, CORS_ORIGINS y API_PREFIX,
   - validación de variables al arranque (fail fast).
3. Inyección de dependencias con Depends:
   - get_db para sesión,
   - get_current_user para seguridad,
   - inyección de servicios para pruebas unitarias más limpias.
4. Consistencia de contratos API:
   - respuestas tipadas,
   - manejo uniforme de errores,
   - menor acoplamiento entre frontend y backend.

## 6. Integración Frontend / Backend (Sistemas Separados)

Coexistencia propuesta:

1. El sitio corporativo (frontend) permanece desacoplado del backend por contrato API.
2. La evolución de UI no depende de detalles internos de persistencia o negocio.

Modelo de repositorios:

1. Estado actual: monorepo transversal para coordinación y activos compartidos.
2. Modelo operativo recomendado: polyrepo lógico dentro del monorepo.
   - Equipos FE y BE con pipelines independientes.
   - Versionado y despliegue desacoplados.
   - Contratos OpenAPI como frontera formal.

Comunicación API REST JSON:

1. Payloads JSON UTF-8 para todas las operaciones.
2. Respuesta de error estándar: code, message, details, trace_id.
3. Versionado de endpoints para compatibilidad evolutiva.

Gestión de variables de entorno:

1. Archivos .env por ambiente: development, staging, production.
2. .env.example versionado; secretos reales fuera del repositorio.
3. Variables mínimas obligatorias: APP_ENV, API_PREFIX, DATABASE_URL, JWT_SECRET, CORS_ORIGINS.

Seguridad CORS con CORSMiddleware:

1. allow_origins explícitos por ambiente.
2. Sin wildcard en producción.
3. Métodos y headers mínimos necesarios.
4. allow_credentials habilitado solo cuando sea imprescindible.

## 7. Riesgos y Puntos de Atención

Riesgo 1: lógica de negocio dentro de routers.

1. Impacto: endpoints difíciles de probar, duplicación de reglas y regresiones frecuentes.
2. Señal temprana: routers con validaciones complejas o consultas ORM directas.
3. Mitigación: revisiones de arquitectura y cobertura de pruebas en services.

Riesgo 2: importaciones circulares entre módulos de dominio.

1. Impacto: fallos de inicialización, acoplamiento accidental y bloqueo de escalado.
2. Señal temprana: dependencia mutua entre services o models de distintos dominios.
3. Mitigación: contratos explícitos entre módulos y dependencias unidireccionales.

Riesgo 3: fuga de variables de entorno o credenciales.

1. Impacto: exposición de datos sensibles y riesgo operacional/legal.
2. Señal temprana: secretos hardcodeados o archivos .env comprometidos.
3. Mitigación: secret manager, escaneo de secretos en CI y rotación periódica.

Riesgo 4: ruptura de contrato FE/BE por cambios no versionados.

1. Impacto: degradación del sitio corporativo y bloqueos en releases.
2. Señal temprana: cambios de schema sin actualización de OpenAPI ni pruebas contractuales.
3. Mitigación: policy de versionado, contract testing y checklist de release.

---

Esta propuesta está lista para ejecución en producción incremental: mantiene velocidad de entrega para TrackFlow, protege la mantenibilidad del código y crea una base sólida para evolucionar hacia mayor escala cuando el volumen operativo lo exija.