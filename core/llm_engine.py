import os
import requests
import json
import streamlit as st

def load_env_key():
    """Locates the Groq API key checking system environment variables, local .env files, or Streamlit secrets."""
    if os.getenv("GROQ_API_KEY"):
        return os.getenv("GROQ_API_KEY").strip()
    if os.path.exists(".env"):
        with open(".env", "r") as f:
            for line in f:
                if line.startswith("GROQ_API_KEY"):
                    parts = line.strip().split("=", 1)
                    if len(parts) == 2:
                        return parts[1].strip("'\" ")
    try:
        return st.secrets.get("GROQ_API_KEY", "").strip()
    except Exception:
        return ""

def generate_test_vectors(target_url, http_method, api_desc, backend_api_key):
    system_prompt = """You are a highly analytical Senior SDET and Penetration Testing AI Agent.
    Your task is to analyze the user's API description and output exactly 15 diverse testing payloads.
    
    You must split the payloads equally into exactly 3 categories:
    1. 'Happy Path': Perfectly clean data matching structural layout specifications exactly. Expects 200/201.
    2. 'Edge Case': High/low boundaries, negative indices, extreme string data lengths, missing keys. Expects 400.
    3. 'Chaos Path': Malicious payloads, basic SQL injections, array breakouts, type coercion threats.
    
    CRITICAL: You must return a valid JSON object containing a single key called "test_cases" which holds the array of payloads. Do not include any markdown or explanation text.
    Format structural pattern perfectly as:
    {
      "test_cases": [
        {"test_type": "Happy Path", "description": "Short reasoning", "payload": {"key": "value"}},
        {"test_type": "Edge Case", "description": "Short reasoning", "payload": {"key": "value"}}
      ]
    }
    """
    
    user_prompt = f"Target Endpoint URL: {target_url}\nMethod: {http_method}\nSchema Rules: {api_desc}"
    
    headers = {
        "Authorization": f"Bearer {backend_api_key}",
        "Content-Type": "application/json"
    }
    payload_data = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.2,
        "response_format": {"type": "json_object"}
    }
    response = requests.post("https://api.groq.com/openai/v1/chat/completions", json=payload_data, headers=headers)
    
    if response.status_code == 200:
        raw_content = response.json()['choices'][0]['message']['content']
        parsed_json = json.loads(raw_content)
        return parsed_json.get("test_cases", [])
    else:
        raise Exception(f"Inference Failure: Groq API returned Status Code {response.status_code}. Details: {response.text}")
