# RPG AI Dungeon Master (RADM)

RPG AI Dungeon Master es un motor de juego de rol (TTRPG) basado en una arquitectura desacoplada, diseñado para integrar inteligencia artificial generativa con el rigor matemático de las reglas de Dungeons & Dragons 5e (SRD).

El sistema actúa como un orquestador de reglas, garantizando que, aunque la narrativa sea fluida y creativa, los resultados mecánicos (tiradas, modificadores, competencias y estados) sean consistentes, transparentes, deterministas y verificables.

---

# 🏗 Arquitectura del Sistema

El proyecto está estructurado como un espacio de trabajo monorepo para desacoplar por completo las reglas de negocio de la interfaz de usuario, garantizando escalabilidad, modularidad y un desarrollo independiente de cada capa.

rpg-ai-dm/
├── backend/            # Motor de reglas, máquina de estados y orquestación de IA (Python)
├── frontend/           # Aplicación web interactiva e interfaz de usuario (Next.js)
├── pnpm-workspace.yaml # Configuración del espacio de trabajo del monorepo
└── README.md           # Documentación global del ecosistema

Componentes Clave del Backend
Engine de Reglas (DiceService): Motor de cálculo puro que aplica fórmulas de D&D 5e sobre los estados del personaje, garantizando determinismo en las mecánicas de dados.

Orquestador de IA (GeminiService): Capa de abstracción que gestiona la inyección de contexto dinámico y la configuración de esquemas nativos (Structured Outputs), forzando al modelo a separar la experiencia inmersiva de las directrices mecánicas.

Servicio de Mutación de Estado (StateMutationService): Componente especializado en procesar de forma transaccional los impactos físicos y lógicos (como alteraciones de HP) dictados por el motor de IA, encapsulando las reglas de negocio del SRD.

Persistencia (SQLAlchemy ORM): Modelo relacional estructurado que gestiona de forma segura desde los atributos base del personaje hasta el historial completo de la sesión bajo transacciones ACID con SQLite.

API Gateway (FastAPI): Interfaz asíncrona que expone los servicios bajo estándares RESTful, facilitando la integración nativa y la validación de contratos de entrada/salida.

Componentes Clave del Frontend
Interfaz de Usuario: Aplicación SPA reactiva con chat inmersivo, renderizado de logs de combate en tiempo real y panel de estado dinámico del personaje.

Gestión de Estado: Abstracción basada en hooks personalizados (useGameSession) encargada de sincronizar de forma asíncrona las acciones del jugador con las respuestas estructuradas del DM.

# 🛠 Especificaciones Técnicas
Backend
Lenguaje: Python 3.13+

Framework: FastAPI (Asynchronous high-performance API)

SDK de IA: Google GenAI Core (google-genai)

ORM: SQLAlchemy 2.0 (Diseño preparado para Arquitectura Hexagonal)

Validación: Pydantic V2 (Definición estricta de contratos JSON de salida para LLMs)

Testing: Suite integral basada en pytest con fixtures de sesión aisladas y mocks orientados a servicios externos.

Frontend
Framework: Next.js 15+ (App Router) con TypeScript 5+

Gestor de Paquetes: pnpm (v11+)

Estilos: Tailwind CSS

Testing: Suite de pruebas unitarias e integración con Vitest 3+ y entorno de simulación de navegador JSDOM.

# 🚀 Visión Estratégica & Roadmap Técnico
El desarrollo del proyecto está orientado a la evolución progresiva de las mecánicas de juego, el desacoplamiento estricto y la persistencia del contexto narrativo:

Fase 1: Motor Base y Continuidad (Completado): Implementación de la arquitectura de servicios desacoplada en el backend, gestión del historial de sesión con ventana deslizante (sliding window context) para mantener el hilo argumental y simulación de dados básica.

Fase 2: Automatización del Estado e Interfaz (Completado): Integración de Structured Outputs con Gemini para separar narrativa de mecánicas. Construcción del StateMutationService para procesar impactos de salud (HP). Creación de la app base en Next.js y configuración de su entorno de testing robusto.

Fase 3: Inventario e Interacción con el Entorno (Próximo Incremento): Diseño de mutaciones dinámicas de inventario (recogida, descarte y uso de objetos). Persistencia de localización y transiciones de estado del entorno (bloqueo de puertas, cofres abiertos/cerrados).

Fase 4: Sistema de Combate Dinámico y Condiciones: Motor de estados avanzado para gestionar turnos, iniciativa, recursos limitados (espejos de conjuros, habilidades por descanso) y estados alterados (envenenado, asustado).

Fase 5: Base de Conocimiento Experta (RAG): Integración de las reglas oficiales del SRD mediante técnicas de recuperación de información para que el DM valide la viabilidad de las acciones del jugador en tiempo real.

# ⚖️ Filosofía del Proyecto
Este sistema fue concebido bajo premisas de mantenibilidad, scalabilidad, Clean Code y principios SOLID. El código evita estrictamente las soluciones monolíticas. La lógica de negocio (reglas de juego del backend y lógica de UI en hooks del frontend) está estrictamente separada de las capas de presentación y de las firmas de frameworks externos.

Las mutaciones de estado jamás ocurren de forma directa en los endpoints ni de manera descontrolada en los componentes visuales, garantizando la estabilidad, consistencia y predictibilidad del dominio.

# 🛠 Desarrollo y Configuración del Entorno
Configuración del Frontend
Debido a las políticas estrictas de seguridad de las versiones recientes de pnpm (v10/v11+), los scripts de construcción nativos (como la compilación de esbuild para entornos de Windows) deben ser aprobados explícitamente antes de realizar la instalación.

1. Aprobar scripts e instalar dependencias
cd frontend
pnpm approve-builds
pnpm install

2. Ejecutar servidor de desarrollo
pnpm run dev

3. Ejecutar la suite de pruebas (Vitest)
pnpm run test

Nota de infraestructura: vitest.config.ts utiliza un tipado por tipomapeado abstracto (unknown/never[]) sobre su array de plugins para desacoplar de forma limpia las discrepancias de firmas entre los tipos internos de Vite 7 (usados por Vitest 3) y Vite 8 (usados por Next.js), satisfaciendo los checks de TypeScript sin vulnerar las reglas estrictas de ESLint (no-explicit-any).

# Configuración del Backend
1. Instalación de dependencias y entorno virtual
cd backend
python -m venv .venv
source .venv/bin/activate  # En Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt

2. Configuración de Variables de Entorno
Es obligatorio proveer la clave de acceso al SDK de Google en tu terminal:
$env:GEMINI_API_KEY="tu_api_key_aquí"

3. Ejecución de la suite de pruebas (pytest)
pytest -v

Nota de infraestructura: La arquitectura de pruebas del backend asegura que cualquier modificación en el core de reglas o en la estructura de los contratos de la IA pase por una validación rigurosa y aislada mediante fixtures antes de cualquier despliegue.