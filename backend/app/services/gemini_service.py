import os
import json
from typing import List, Dict, Any, Optional
from google import genai
from google.genai import types
from google.genai.errors import APIError
from app.core.prompts import SYSTEM_PROMPT
from app.schemas.ai_responses import StateMutationResponseSchema

class GeminiService:
    def __init__(self):
        # El SDK de Google GenAI inicializa automáticamente usando la variable GEMINI_API_KEY del entorno
        self.client = genai.Client()
        self.model_name = "gemini-2.5-flash"

    def generate_structured_response(self, context_instruction: str, history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Envía el historial de la conversación a Gemini exigiendo de forma nativa
        un objeto JSON que cumpla estrictamente con el esquema StateMutationResponseSchema.
        """
        # Combinar el prompt del sistema con el contexto dinámico del personaje actual
        full_system_instruction = f"{SYSTEM_PROMPT}\n\n[CONTEXTO ACTUAL DEL JUEGO]\n{context_instruction}"

        # Mapear el historial del formato interno de la DB al formato de contenidos exigido por el SDK GenAI
        contents = []
        for message in history:
            # Gemini exige que los roles del historial sean estrictamente 'user' o 'model'
            api_role = "model" if message["role"] == "assistant" else "user"
            contents.append(
                types.Content(
                    role=api_role,
                    parts=[types.Part.from_text(text=message["parts"][0]["text"])]
                )
            )

        # Configurar la generación de la IA para forzar salida estructurada en JSON
        config = types.GenerateContentConfig(
            system_instruction=full_system_instruction,
            temperature=0.7,
            response_mime_type="application/json",
            response_schema=StateMutationResponseSchema,
        )

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=contents,
                config=config
            )
            
            # Al usar response_schema, response.text es garantizado un string JSON válido con nuestra estructura
            return json.loads(response.text)

        except APIError as e:
            return {
                "narrative": f"Error de comunicación con el servicio de narración (Status {e.code}).",
                "hp_change": None
            }
        except Exception as e:
            return {
                "narrative": f"Error inesperado en el motor de IA: {str(e)}",
                "hp_change": None
            }

    def generate_response(self, context_instruction: str, history: List[Dict[str, Any]]) -> str:
        """
        Método heredado preservado exclusivamente para mantener la compatibilidad hacia atrás
        con los endpoints originales /game/chat y /game/roll del frontend.
        """
        structured = self.generate_structured_response(context_instruction, history)
        return structured.get("narrative", "")

gemini_service = GeminiService()