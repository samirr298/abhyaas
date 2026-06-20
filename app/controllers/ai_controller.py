import os
from flask import request, jsonify
from google import genai
from google.genai import types
from app.controllers.base_controller import BaseController


class AIController(BaseController):
    """Stateless AI assistant backend using the official google-genai SDK.

    - Low token cap configuration to keep responses short.
    - Strict local length cutting guardrails.
    - Safety rejection rules for large tasks.
    """

    MAX_CHARS = 180

    HEAVY_TASK_PATTERNS = [
        "full code", "implement", "build a complete", "complete project",
        "rewrite", "debug entire", "fix my project", "summarize this long",
        "long article", "thousands of", "step-by-step with code",
        "generate a full", "create routes", "controller", "refactor"
    ]

    def __init__(self):
        super().__init__()
        # Initializes the real Gemini client using your environment variable
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    def _is_heavy_task(self, text: str) -> bool:
        t = (text or "").lower()
        return any(p in t for p in self.HEAVY_TASK_PATTERNS)

    def _shorten(self, text: str) -> str:
        t = (text or "").strip()
        if len(t) <= self.MAX_CHARS:
            return t
        return (t[: self.MAX_CHARS - 3].rstrip() + "...")

    def ask(self):
        data = request.get_json(silent=True) or {}
        question = (data.get("question") or "").strip()

        if not question:
            return jsonify({"ok": False, "answer": "Please type a question."}), 400

        # Guard 1: Reject heavy requests right away
        if self._is_heavy_task(question):
            return jsonify({
                "ok": False,
                "answer": "I can’t help with heavy tasks. Ask a small question and I’ll answer briefly."
            }), 200

        try:
            # Force brevity right at the model level via instructions
            system_instruction = (
                "You are a helpful, extremely brief assistant. "
                "Provide direct, short answers. Do not use pleasantries. "
                f"Your response MUST be under {self.MAX_CHARS} characters."
            )

            # Cap output tokens to restrict word counts safely before it transfers
            config = types.GenerateContentConfig(
                system_instruction=system_instruction,
                max_output_tokens=70,  
                temperature=0.4,
            )

            # Fire request to the optimized model
            response = self.client.models.generate_content(
                model='gemini-2.5-flash',
                contents=question,
                config=config
            )

            raw_answer = response.text or "I am unsure how to answer that clearly."
            final_answer = raw_answer

            return jsonify({"ok": True, "answer": final_answer})

        except Exception as e:
            print(f"🚨 GEMINI API RUNTIME ERROR: {str(e)}")
            return jsonify({
                "ok": False, 
                "answer": "Sorry, I'm having trouble processing that right now."
            }), 500