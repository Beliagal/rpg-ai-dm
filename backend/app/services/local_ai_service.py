import os
import json
from typing import List, Dict, Any
from openai import AsyncOpenAI
from app.core.prompts import SYSTEM_PROMPT
from app.schemas.ai_responses import StateMutationResponseSchema

class LocalAiService:
    def __init__(self):
        # Conexión asíncrona al demonio local de Ollama
        self.client = AsyncOpenAI(
            base_url="http://localhost:11434/v1",
            api_key="ollama"  # Requisito estructural de la librería, ignorado por Ollama
        )
        self.model_name = "qwen2.5:7b"

    async def generate_structured_response(self, context_instruction: str, history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Envía el historial y el contexto al modelo local exigiendo un formato JSON.
        Valida la respuesta final contra el esquema nativo de la aplicación.
        """
        full_system_instruction = f"{SYSTEM_PROMPT}\n\n[CONTEXTO ACTUAL DEL JUEGO]\n{context_instruction}"

        # Construir el set de mensajes para la API de chat
        messages = [{"role": "system", "content": full_system_instruction}]
        
        for message in history:
            role = message.get("role")
            content = ""
            if "parts" in message and isinstance(message["parts"], list) and len(message["parts"]) > 0:
                content = message["parts"][0].get("text", "")
            else:
                content = message.get("content", "")
                
            messages.append({"role": role, "content": content})

        try:
            # Invocación asíncrona forzando JSON nativo
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            
            raw_content = response.choices[0].message.content
            if not raw_content:
                raise ValueError("El modelo local devolvió un contenido vacío.")

            # Parsear el JSON crudo y validar estructuralmente contra Pydantic
            parsed_json = json.loads(raw_content)
            validated_data = StateMutationResponseSchema.model_validate(parsed_json)
            return validated_data.model_dump()

        except Exception as e:
            print(f"❌ Error crítico en el motor de IA local (Ollama): {str(e)}")
            return {
                "narrative": "El motor narrativo local ha sufrido un problema al procesar la acción. Por favor, intenta reformular tu comando.",
                "hp_change": None
            }

local_ai_service = LocalAiService()