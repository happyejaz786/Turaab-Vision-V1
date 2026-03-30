import os
import json
import mimetypes
from datetime import datetime
import streamlit as st
from google import genai
from google.genai import types

class PromptLibraryManager:
    def __init__(self, db_path="prompt_bank.json"):
        self.db_path = db_path
        self._ensure_db_exists()

    def _ensure_db_exists(self):
        """Creates the JSON database if it doesn't exist."""
        if not os.path.exists(self.db_path):
            with open(self.db_path, "w", encoding="utf-8") as f:
                json.dump({}, f, indent=4)

    def _get_file_profile(self, has_image, file_name):
        """Smart detection of the uploaded file type."""
        if has_image:
            return "Visual/Image File (PNG, JPG, WEBP)"
        if file_name:
            mime_type, _ = mimetypes.guess_type(file_name)
            if mime_type:
                return f"Document/Data File ({mime_type})"
            ext = os.path.splitext(file_name)[1]
            return f"File with extension: {ext}"
        return "No file attached. Pure text query."

    def generate_and_save_prompt(self, raw_prompt, has_image=False, file_name=None):
        """
        Core Engine: Enhances prompt with Intent Detection, Time Awareness, and Failsafes.
        """
        file_profile = self._get_file_profile(has_image, file_name)
        
        # 🕒 Fetching accurate system time to inject into the AI's brain
        current_time = datetime.now().strftime("%I:%M %p, %A, %B %d, %Y")
        
        system_instruction = f"""
        You are a Senior AI Prompt Engineer. Your job is to take a user's raw input and context, 
        and transform it into a highly professional, detailed, and optimized master prompt for an AI assistant.
        
        Context:
        - Uploaded file type: {file_profile}
        - Current System Time: {current_time}
        - Raw Input: {raw_prompt}
        
        CRITICAL PIPELINE & CONSTRAINTS:
        1. Intent Check (The Greeting Rule): If the Raw Input is a simple greeting (e.g., "Hi", "Hello", "Assalaam", "Kaise ho"), casual conversation, or asking the time:
           - DO NOT generate a complex, structured analysis prompt. 
           - INSTEAD, instruct the AI to respond warmly, naturally, and concisely. Explicitly tell the AI to use the provided 'Current System Time' to wish the user appropriately (e.g., Good Morning/Afternoon/Evening) and answer naturally.
        2. Auto-Detection Protocol: (If not a greeting) FIRST detect the file type, THEN detect the language of the uploaded document/image.
        3. Language Rule: The AI MUST respond in the EXACT same language as the uploaded document or user input by default. Only change if explicitly asked to translate.
        4. Depth & Detail: For technical or analytical queries, the AI MUST provide a highly detailed, comprehensive, and structured response.
        5. Execution: Create a master prompt that gives these clear instructions to the AI engine.
        
        Respond EXACTLY in this JSON structure:
        {{
            "category": "Category_Name",
            "enhanced_prompt": "The detailed master prompt here..."
        }}
        """

        try:
            api_keys = st.secrets["gemini"]["api_keys"]
        except Exception:
            print("⚠️ API Keys missing from Streamlit secrets.")
            return raw_prompt, "Uncategorized"

        models_to_try = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-flash-latest"]

        # 🔄 API Key & Model Rotation Logic
        for key in api_keys:
            try:
                client = genai.Client(api_key=key)
                for model_name in models_to_try:
                    try:
                        response = client.models.generate_content(
                            model=model_name,
                            contents=system_instruction,
                            config=types.GenerateContentConfig(
                                response_mime_type="application/json",
                                temperature=0.2
                            )
                        )
                        
                        if response and response.text:
                            result = json.loads(response.text)
                            category = result.get("category", "General").replace(" ", "_")
                            enhanced_prompt = result.get("enhanced_prompt", raw_prompt)

                            # Silently save to backend
                            self._save_to_bank(raw_prompt, enhanced_prompt, category)
                            return enhanced_prompt, category
                    except Exception as e:
                        continue
            except Exception as e:
                continue

        # Failsafe mechanism
        self._save_to_bank(raw_prompt, raw_prompt, "General_Fallback")
        return raw_prompt, "General_Fallback"

    def _save_to_bank(self, raw_prompt, enhanced_prompt, category):
        """Dynamically updates the JSON database without deleting existing data."""
        try:
            with open(self.db_path, "r", encoding="utf-8") as f:
                db = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            db = {}

        if category not in db:
            db[category] = {}

        key_name = raw_prompt.replace("\n", " ").strip()
        if len(key_name) > 60:
            key_name = key_name[:57] + "..."

        db[category][key_name] = enhanced_prompt

        with open(self.db_path, "w", encoding="utf-8") as f:
            json.dump(db, f, indent=4, ensure_ascii=False)