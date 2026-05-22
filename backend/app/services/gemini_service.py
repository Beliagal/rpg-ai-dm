import os
import httpx
from pathlib import Path
from dotenv import load_dotenv
from app.core.prompts import SYSTEM_PROMPT

BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(dotenv_path=BASE_DIR / ".env")

class GeminiService:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.base_url = "https://generativelanguage.googleapis.com/v1"
        self.model_id = None
        
        print("\n" + "="*40)
        print("🔍 BUSCANDO MODELOS DISPONIBLES...")
        
        if not self.api_key:
            print("❌ ERROR: No se encontró GEMINI_API_KEY")
            return

        try:
            with httpx.Client() as client:
                response = client.get(f"{self.base_url}/models?key={self.api_key}")
                if response.status_code == 200:
                    models_data = response.json().get('models', [])
                    for m in models_data:
                        if "generateContent" in m.get("supportedGenerationMethods", []):
                            if "1.5-flash" in m.get("name") or "2.5-flash" in m.get("name"):
                                self.model_id = m.get("name")
                                break
                            if not self.model_id:
                                self.model_id = m.get("name")
                    print(f"✅ Usando modelo: {self.model_id}")
                else:
                    print(f"❌ Error de API ({response.status_code})")
        except Exception as e:
            print(f"❌ Error al conectar con Google: {e}")

        if not self.model_id:
            self.model_id = "models/gemini-pro"
        print("="*40 + "\n")

    def generate_response(self, context_instruction: str, history: list = None) -> str:
        if not self.api_key:
            return "Error: API Key no configurada."

        url = f"{self.base_url}/{self.model_id}:generateContent?key={self.api_key}"
        
        # Normalizar historial y corregir mapeo de roles para la API de Google
        processed_contents = []
        if history:
            for item in history:
                # Mapear rol 'assistant' a 'model' requerido por Gemini
                raw_role = item.get("role", "user")
                role = "model" if raw_role == "assistant" else raw_role
                
                if "parts" in item and isinstance(item["parts"], list):
                    processed_contents.append({
                        "role": role,
                        "parts": item["parts"]
                    })
                elif "message" in item:  # Soporte para formato plano del frontend antiguo
                    processed_contents.append({
                        "role": role,
                        "parts": [{"text": item["message"]}]
                    })
        else:
            # Fallback defensivo si no hay historial
            processed_contents = [{"role": "user", "parts": [{"text": "Comenzar narración."}]}]

        # Combinar el prompt estático del DM con el contexto dinámico del personaje
        full_system_instruction = f"{SYSTEM_PROMPT}\n\n[CONTEXTO ACTUAL DEL JUEGO]\n{context_instruction}"

        payload = {
            "contents": processed_contents,
            "systemInstruction": {
                "parts": [{"text": full_system_instruction}]
            },
            "generationConfig": {
                "temperature": 0.8, 
                "maxOutputTokens": 1000
            }
        }

        try:
            with httpx.Client() as client:
                response = client.post(url, json=payload, timeout=30.0)
                if response.status_code == 200:
                    res_json = response.json()
                    texto = res_json['candidates'][0]['content']['parts'][0]['text']
                    print(f"\n📖 DM DIJO:\n{texto[:100]}...")
                    return texto
                return f"Error de narración (Status {response.status_code}): {response.text}"
        except Exception as e:
            return f"Error de conexión: {str(e)}"

gemini_service = GeminiService()