# RPG AI Dungeon Master (RADM)

RPG AI Dungeon Master es un motor de juego de rol (TTRPG) basado en una arquitectura desacoplada, diseñado para integrar inteligencia artificial generativa con el rigor matemático de las reglas Dungeons & Dragons 5e (SRD).

El sistema actúa como un orquestador de reglas, garantizando que, aunque la narrativa sea fluida y creativa, los resultados mecánicos (tiradas, modificadores, competencias y estados) sean consistentes, transparentes y verificables.

# 🏗 Arquitectura del Sistema
El proyecto sigue una estructura orientada a servicios, optimizada para la escalabilidad, el desacoplamiento y la fiabilidad en la toma de decisiones basada en reglas.

Componentes Clave:
* **Engine de Reglas (DiceService):** Motor de cálculo puro que aplica fórmulas de D&D 5e sobre los estados del personaje, garantizando determinismo en las mecánicas de dados.
* **Orquestador de IA (GeminiService):** Capa de abstracción que gestiona la inyección de contexto dinámico y la configuración de esquemas nativos (Structured Outputs), forzando al modelo a separar la experiencia inmersiva de las directrices mecánicas.
* **Servicio de Mutación de Estado (StateMutationService):** Componente especializado en procesar de forma transaccional los impactos físicos y lógicos (como alteraciones de HP) dictados por el motor de IA, encapsulando las reglas de negocio del SRD.
* **Persistencia (SQLAlchemy ORM):** Modelo relacional estructurado que gestiona de forma segura desde los atributos base del personaje hasta el historial completo de la sesión bajo transacciones ACID.
* **API Gateway (FastAPI):** Interfaz asíncrona que expone los servicios bajo estándares RESTful, facilitando la integración nativa y la validación de contratos de entrada/salida.

# 🛠 Especificaciones Técnicas

* **Lenguaje:** Python 3.13+
* **Framework:** FastAPI (Asynchronous high-performance API)
* **SDK de IA:** Google GenAI Core (google-genai)
* **ORM:** SQLAlchemy 2.0 (Hexagonal-ready design)
* **Validación:** Pydantic V2 (Definición estricta de contratos JSON de salida para LLMs)
* **Testing:** Suite integral basada en pytest con fixtures de sesión aisladas y mocks orientados a servicios externos.

# 🚀 Visión Estratégica & Roadmap Técnico
El desarrollo del proyecto está orientado a la maduración de tres pilares fundamentales:

* **Continuidad Narrativa (Hito Completo):** Implementación de sistemas de memoria basados en una ventana sliding (sliding window context) para persistir el hilo conductor en sesiones extensas.
* **Automatización de Estado de Juego (Hito Completo):** Tubería síncrona que lee la inferencia estructurada de la IA y aplica de forma automatizada daños o curaciones sobre la salud del jugador en base de datos.
* **Sistema de Combate e Inventario Dinámico (Próximo Incremento):** Motor de estados persistentes para gestionar de forma transaccional la adquisición de recursos, condiciones avanzadas, turnos y equipo.
* **Base de Conocimiento Dinámica (RAG):** Integración de documentos de reglas mediante técnicas de recuperación de información para dotar al DM de pericia regulatoria en tiempo real.

# ⚖️ Filosofía del Proyecto
Este sistema fue concebido bajo premisas de mantenibilidad, escalabilidad y desacoplamiento. El código no busca ser una solución monolítica, sino un ecosistema donde la lógica de negocio (reglas de juego) esté estrictamente separada de la capa de presentación (narrativa de IA). Las mutaciones del modelo jamás ocurren de forma directa en los endpoints, garantizando la estabilidad y consistencia del dominio.

# 🛠 Desarrollo y Contribución

Para configurar el entorno de trabajo:

1. **Instalación de dependencias**
   pip install -r requirements.txt

2. **Configuración de Variables de Entorno**
   Es obligatorio proveer la clave de acceso oficial al SDK en tu sesión:
   $env:GEMINI_API_KEY="tu_api_key_aquí"
   (Es una solución temporal hasta que se implemente el estado final de la aplicación)

3. **Ejecución de la suite de pruebas**
   pytest -v

Nota: La arquitectura de pruebas asegura que cualquier modificación en el core de reglas o en la estructura de los contratos de la IA pase por una suite de validación rigurosa antes de cualquier despliegue.


# 🚀 Visión Estratégica & Roadmap Técnico
El desarrollo del proyecto está orientado a la evolución progresiva de las mecánicas de juego y la persistencia del contexto narrativo:

*   **Fase 1: Motor Base y Continuidad (Completado):** Implementación de la arquitectura de servicios desacoplada, gestión del historial de sesión con ventana deslizante (*sliding window*) y simulación de dados básica.
*   **Fase 2: Automatización del Estado (Completado):** Integración de *Structured Outputs* con Gemini y desarrollo del `StateMutationService` para el procesamiento transaccional de impactos de salud (HP) en la base de datos SQLite.
*   **Fase 3: Inventario e Interacción con el Entorno (Próximo Incremento):** 
    *   Diseño de mutaciones dinámicas de inventario (recogida, descarte y uso de objetos).
    *   Persistencia de localización y transiciones de estado del entorno (bloqueo de puertas, cofres abiertos/cerrados).
*   **Fase 4: Sistema de Combate Dinámico y Condiciones:** Motor de estados avanzado para gestionar turnos, iniciativa, recursos limitados (espejos de conjuros, habilidades por descanso) y estados alterados (envenenado, asustado).
*   **Fase 5: Base de Conocimiento Experta (RAG):** Integración de las reglas oficiales del SRD mediante técnicas de recuperación de información para que el DM valide la viabilidad de las acciones del jugador en tiempo real.