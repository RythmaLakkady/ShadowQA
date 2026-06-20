import asyncio
import httpx
import time
import json
from datetime import datetime
from database.db import save_test_session

async def fetch(client, method, url, payload):
    """Asynchronous worker that fires a single payload and captures the text body."""
    start_time = time.time()
    try:
        # httpx handles JSON bodies securely across all methods using .request()
        response = await client.request(method.upper(), url, json=payload, timeout=10.0)
        res_time = (time.time() - start_time) * 1000
        return response.status_code, response.text, res_time
    except Exception as e:
        res_time = (time.time() - start_time) * 1000
        return 0, str(e), res_time

async def execute_concurrent_tests(tests, target_url, http_method):
    """Fires all test vectors at the exact same time."""
    async with httpx.AsyncClient() as client:
        tasks = [fetch(client, http_method, target_url, test.get('payload', {})) for test in tests]
        return await asyncio.gather(*tasks)

def run_tests(test_cases, target_url, http_method, user_id):
    """Main execution loop bridging async performance with Streamlit's sync generator."""
    total_vectors = len(test_cases)
    if total_vectors == 0:
        return

    # Yield an initial loading state
    yield {"done": False, "index": 0, "total": total_vectors, "test": test_cases[0]}

    # 🚀 Execute all network requests simultaneously
    results = asyncio.run(execute_concurrent_tests(test_cases, target_url, http_method))
    
    executed_results = []
    failures_count = 0
    
    for index, (test, (status_code, response_body, res_time)) in enumerate(zip(test_cases, results)):
        result_status = "UNKNOWN"
        
        # Your custom audit vulnerability logic
        if test['test_type'] == "Happy Path" and status_code in [200, 201]:
            result_status = "PASS"
        elif test['test_type'] == "Edge Case" and status_code in [400, 422]:
            result_status = "PASS"
        elif status_code == 500:
            result_status = "VULNERABILITY_CRASH (500)"
            failures_count += 1
        elif test['test_type'] in ["Edge Case", "Chaos Path"] and status_code in [200, 201]:
            result_status = "VULNERABILITY_LEAK (Accepted Unsanitized Data)"
            failures_count += 1
        elif status_code == 0:
            result_status = "CONNECTION_REFUSED_CRASH"
            failures_count += 1
        else:
            result_status = "PASS (Handled Gracefully)"
            
        # Determine strict PASS/FAIL for UI compatibility
        ui_status = "FAIL" if "VULNERABILITY" in result_status or "CRASH" in result_status else "PASS"
            
        executed_results.append({
            "test_type": test['test_type'],
            "payload": json.dumps(test['payload']),
            "status_code": status_code,
            "response_time_ms": round(res_time, 2),
            "response_body": response_body,  # Crucial for the AI Debugger Bridge
            "result_status": result_status,
            "status": ui_status,             # Used by the UI to trigger the RAG handoff
            "description": test.get('description', '')
        })
        
        # Yield progress back to Streamlit
        yield {
            "done": False,
            "index": index,
            "total": total_vectors,
            "test": test,
            "result": executed_results[-1]
        }
        
    vulnerability_rate = round((failures_count / total_vectors) * 100, 2) if total_vectors > 0 else 0
    timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Commit to SQLite
    save_test_session(user_id, target_url, timestamp_str, vulnerability_rate, executed_results)
    
    # Yield final metrics dashboard
    yield {
        "done": True,
        "vulnerability_rate": vulnerability_rate,
        "failures_count": failures_count,
        "avg_latency": round(sum(r['response_time_ms'] for r in executed_results) / total_vectors, 2) if total_vectors > 0 else 0,
        "executed_results": executed_results
    }