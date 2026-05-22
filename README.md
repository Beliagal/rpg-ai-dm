# RPG AI Dungeon Master (RADM)

RPG AI Dungeon Master es un motor de juego de rol (TTRPG) basado en una arquitectura desacoplada, diseñado para integrar inteligencia artificial generativa con el rigor matemático de las reglas Dungeons & Dragons 5e (SRD 5.2.1).

El sistema actúa como un orquestador de reglas, garantizando que, aunque la narrativa sea fluida y creativa, los resultados mecánicos (tiradas, modificadores, competencias y estados) sean consistentes, transparentes y verificables.

# 🏗 Arquitectura del Sistema
El proyecto sigue una estructura orientada a servicios, optimizada para la escalabilidad y la fiabilidad en la toma de decisiones basada en reglas.

Componentes Clave:
* Engine de Reglas (DiceService): Motor de cálculo puro que aplica fórmulas de D&D 5e sobre los estados del personaje, garantizando determinismo en las mecánicas.

* Orquestador de IA (GeminiService): Capa de abstracción que gestiona la inyección de contexto (RAG narrativo) y prompts dinámicos, asegurando que el modelo mantenga el tono y las restricciones del juego.

* Persistencia (SQLAlchemy ORM): Modelo relacional altamente estructurado que gestiona desde los atributos base del personaje hasta el historial completo de la sesión.

* API Gateway (FastAPI): Interfaz asíncrona que expone los servicios bajo estándares RESTful, facilitando la integración con cualquier frontend.

# 🛠 Especificaciones Técnicas

* Lenguaje: Python 3.13+

* Framework: FastAPI (Asynchronous high-performance API)

* ORM: SQLAlchemy 2.0 (Hexagonal-ready design)

* Validación: Pydantic V2

* Testing: Suite integral basada en pytest con fixtures de sesión aisladas y mocks para servicios externos.

# 🚀 Visión Estratégica (Roadmap Técnico)
El desarrollo del proyecto está orientado a la maduración de tres pilares fundamentales:

* Continuidad Narrativa: Implementación de sistemas de memoria a largo plazo (sliding window context) para permitir sesiones de juego extensas y profundas.

* Sistema de Combate Dinámico: Motor de estados persistentes para gestionar condiciones, recursos, turnos e impacto físico sobre la salud del jugador.

* Base de Conocimiento Dinámica: Integración de documentos de reglas (SRD) mediante técnicas de recuperación de información, permitiendo que el DM sea un experto en las reglas del sistema en tiempo real.

# ⚖️ Filosofía del Proyecto
Este sistema fue concebido bajo premisas de mantenibilidad, escalabilidad y desacoplamiento. El código no busca ser una solución monolítica, sino un ecosistema donde la lógica de negocio (reglas de juego) esté estrictamente separada de la capa de presentación (narrativa de IA).

# 🛠 Desarrollo y Contribución
Para configurar el entorno de trabajo:

* Instalación de dependencias
[pip install -r requirements.txt]

* Ejecución de la suite de pruebas
[python -m pytest backend/tests/ -v]

Nota: La arquitectura de pruebas asegura que cualquier modificación en el core de reglas pase por una suite de validación rigurosa antes de cualquier despliegue.
