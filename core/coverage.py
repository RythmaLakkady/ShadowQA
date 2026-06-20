# core/coverage.py
import json
import re

def parse_postman_collection(file_content: str):
    """Extracts HTTP methods and endpoints from a Postman v2.1+ JSON collection."""
    endpoints = []
    try:
        data = json.loads(file_content)
        
        def extract_items(items):
            for item in items:
                if "item" in item:
                    extract_items(item["item"])
                elif "request" in item:
                    req = item["request"]
                    method = req.get("method", "GET").upper()
                    # Extract URL string whether it's a dict or a string
                    url_data = req.get("url", "")
                    url_raw = url_data.get("raw", "") if isinstance(url_data, dict) else str(url_data)
                    
                    # Clean up URL (remove Postman {{variables}} and query params for cleaner matching)
                    url_path = re.sub(r'\{\{[^}]+\}\}', '', url_raw).split('?')[0]
                    if url_path:
                        endpoints.append(f"{method} {url_path}")
        
        if "item" in data:
            extract_items(data["item"])
            
    except Exception as e:
        return [f"Error parsing Postman file: {str(e)}"]
    
    return list(set(endpoints))

def parse_pytest_script(file_content: str):
    """Extracts requests and client calls from Python testing scripts."""
    endpoints = []
    # Matches patterns like: requests.get('/api/users') or client.post('/login')
    pattern = r"(?:requests|client|httpx|session)\.(get|post|put|delete|patch)\(\s*['\"]([^'\"]+)['\"]"
    matches = re.findall(pattern, file_content, re.IGNORECASE)
    
    for method, url in matches:
        endpoints.append(f"{method.upper()} {url.split('?')[0]}")
        
    return list(set(endpoints))

def evaluate_shadow_zones(schema_text: str, extracted_tests: list, groq_client, model_name="llama-3.3-70b-versatile"):
    """
    Passes the API schema and the found test endpoints to the LLM to identify coverage gaps.
    """
    system_prompt = (
        "You are an expert SDET performing an Automated Test Coverage & Gap Analysis.\n"
        "You will receive an OpenAPI/API Schema and a list of endpoints currently targeted by the user's test suite.\n"
        "Identify the 'Shadow Zones': endpoints, HTTP methods, or critical parameter edge cases defined in the schema that are MISSING from the test suite.\n"
        "Format your output cleanly using Markdown with these exact headings:\n\n"
        "### 📊 Coverage Score Estimate\n"
        "[Provide a percentage and brief justification]\n\n"
        "### ✅ Verified Test Coverage\n"
        "[List what they are doing right based on the extracted tests]\n\n"
        "### 🕵️‍♂️ Critical Shadow Zones (Missing Tests)\n"
        "[List the explicit gaps, missing endpoints, and unhandled status codes]"
    )
    
    test_list_str = "\n".join(extracted_tests) if extracted_tests else "No recognizable network requests found in uploaded files."
    user_prompt = f"API Schema Reference:\n{schema_text}\n\nExisting Tests Extracted from User Files:\n{test_list_str}"
    
    response = groq_client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.1
    )
    
    return response.choices[0].message.content