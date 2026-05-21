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

    def generate_response(self, user_input: str, history: list = None):
        if not self.api_key:
            return "Error: API Key no configurada."

        url = f"{self.base_url}/{self.model_id}:generateContent?key={self.api_key}"
        payload = {
            "contents": [{"role": "user", "parts": [{"text": f"{SYSTEM_PROMPT}\n\nUsuario: {user_input}"}]}],
            "generationConfig": {"temperature": 0.8, "maxOutputTokens": 1000}
        }

        try:
            with httpx.Client() as client:
                response = client.post(url, json=payload, timeout=30.0)
                if response.status_code == 200:
                    texto = response.json()['candidates'][0]['content']['parts'][0]['text']
                    print(f"\n📖 DM DIJO:\n{texto[:100]}...")
                    return texto
                return f"Error de narración (Status {response.status_code})"
        except Exception as e:
            return f"Error de conexión: {str(e)}"

gemini_service = GeminiService()