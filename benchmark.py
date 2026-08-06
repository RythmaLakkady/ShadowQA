import os
import ast
import time
import json
import statistics
import asyncio
from pathlib import Path
from dotenv import load_dotenv

def calculate_code_metrics():
    metrics = {
        "python_files": 0,
        "modules": 0,
        "classes": 0,
        "functions": 0,
        "non_comment_loc": 0,
        "total_function_length": 0
    }
    
    base_dir = Path(".")
    for filepath in base_dir.rglob("*.py"):
        if any(part in str(filepath) for part in ["venv", ".git", "__pycache__", "node_modules", "chroma_db", "chromadb"]):
            continue
            
        metrics["python_files"] += 1
        metrics["modules"] += 1
        
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                source = f.read()
                lines = source.splitlines()
                # Count non-comment LOC
                loc = sum(1 for line in lines if line.strip() and not line.strip().startswith("#"))
                metrics["non_comment_loc"] += loc
                
                # Parse AST
                tree = ast.parse(source)
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        metrics["classes"] += 1
                    elif isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                        metrics["functions"] += 1
                        func_loc = node.end_lineno - node.lineno + 1
                        metrics["total_function_length"] += func_loc
        except Exception:
            pass
            
    metrics["average_function_length"] = round(metrics["total_function_length"] / metrics["functions"], 2) if metrics["functions"] > 0 else 0
    return metrics

def run_benchmark(name, func, *args, warmup=2, runs=5, **kwargs):
    # Warmup
    for _ in range(warmup):
        try:
            if asyncio.iscoroutinefunction(func):
                asyncio.run(func(*args, **kwargs))
            else:
                func(*args, **kwargs)
        except Exception:
            pass
            
    # Measure
    times = []
    for _ in range(runs):
        start = time.perf_counter()
        try:
            if asyncio.iscoroutinefunction(func):
                asyncio.run(func(*args, **kwargs))
            else:
                func(*args, **kwargs)
        except Exception:
            pass
        end = time.perf_counter()
        times.append((end - start) * 1000) # in ms
        
    if not times:
        return {"name": name, "error": "All runs failed"}
        
    return {
        "name": name,
        "runs": runs,
        "mean_ms": round(statistics.mean(times), 2),
        "median_ms": round(statistics.median(times), 2),
        "min_ms": round(min(times), 2),
        "max_ms": round(max(times), 2),
        "std_dev_ms": round(statistics.stdev(times), 2) if len(times) > 1 else 0,
        "p95_ms": round(sorted(times)[int(len(times)*0.95)-1], 2) if len(times) > 1 else round(times[0], 2)
    }

def simulate_app_startup():
    import app
    
def test_async_runner():
    from core.test_runner import execute_concurrent_tests
    tests = [
        {"test_type": "Happy Path", "payload": {"dummy": "data"}},
        {"test_type": "Edge Case", "payload": {"dummy": ""}},
        {"test_type": "Chaos Path", "payload": {"dummy": "DROP TABLE"}}
    ]
    return asyncio.run(execute_concurrent_tests(tests, "https://httpbin.org/post", "POST"))

def benchmark_db():
    from database.db import init_db, register_user, authenticate_user, save_test_session
    init_db()
    
    # Try register a random user
    username = f"bench_user_{time.time()}"
    register_user(username, "bench_pass")
    
    # Authenticate
    uid = authenticate_user(username, "bench_pass")
    
    # Save session
    if uid:
        save_test_session(uid, "https://httpbin.org/post", str(time.time()), 33.3, [
            {"test_type": "Happy Path", "payload": "{}", "status_code": 200, "response_time_ms": 150, "result_status": "PASS"}
        ])

def main():
    print("Starting ShadowQA Benchmark...")
    load_dotenv()
    api_key = os.getenv("GROQ_API_KEY")
    
    metrics = {
        "code_metrics": calculate_code_metrics(),
        "benchmarks": []
    }
    
    print("Measuring application startup...")
    start = time.perf_counter()
    import app
    startup_time = (time.perf_counter() - start) * 1000
    metrics["benchmarks"].append({
        "name": "Application Startup",
        "runs": 1,
        "mean_ms": round(startup_time, 2)
    })
    
    print("Benchmarking Endpoint Extraction (Postman Parsing)...")
    from core.coverage import parse_postman_collection
    with open("dummy_postman.json", "r") as f:
        postman_content = f.read()
    metrics["benchmarks"].append(run_benchmark("Postman JSON Parsing", parse_postman_collection, postman_content, warmup=5, runs=20))
    
    print("Benchmarking ChromaDB & RAG Indexing...")
    from core.rag_engine import chunk_document, init_vector_db
    with open("dummy_openapi.json", "r") as f:
        schema_text = f.read()
        
    def rag_pipeline():
        chunks = chunk_document(schema_text)
        return init_vector_db(chunks)
        
    metrics["benchmarks"].append(run_benchmark("ChromaDB RAG Indexing", rag_pipeline, warmup=1, runs=3))
    
    print("Benchmarking SQLite Writes...")
    metrics["benchmarks"].append(run_benchmark("SQLite Register & Save Session", benchmark_db, warmup=2, runs=10))
    
    print("Benchmarking Async HTTP Test Runner...")
    metrics["benchmarks"].append(run_benchmark("Async HTTP Execution (3 Payloads)", test_async_runner, warmup=1, runs=5))
    
    if api_key:
        print("Benchmarking Groq Inference (Test Generation)...")
        from core.llm_engine import generate_test_vectors
        # We only run this a few times to save tokens and time
        metrics["benchmarks"].append(run_benchmark("Groq LLM Prompting & Test Generation", 
            generate_test_vectors, 
            "https://httpbin.org/post", "POST", "Expects json with name and email", api_key, 
            warmup=0, runs=2))
            
        print("Benchmarking RAG Error Diagnostics...")
        from core.rag_engine import analyze_error_with_rag
        retriever = rag_pipeline()
        
        # Need to init groq client for RAG diagnostics
        from groq import Groq
        g_client = Groq(api_key=api_key)
        
        metrics["benchmarks"].append(run_benchmark("Groq RAG Error Diagnostic Inference", 
            analyze_error_with_rag, 
            "Error 500: Missing email field", retriever, g_client, 
            warmup=0, runs=2))
            
        print("Benchmarking Coverage Report Generation...")
        from core.coverage import evaluate_shadow_zones
        metrics["benchmarks"].append(run_benchmark("Groq LLM Coverage Report Generation", 
            evaluate_shadow_zones, 
            schema_text, ["POST /users", "GET /users"], g_client, 
            warmup=0, runs=2))
    else:
        print("GROQ_API_KEY not found. Skipping Groq API benchmarks.")
        
    # Calculate Total End-to-End time estimate (sum of means)
    total_time = sum(b.get("mean_ms", 0) for b in metrics["benchmarks"])
    metrics["benchmarks"].append({
        "name": "Total End-to-End Runtime Estimate",
        "runs": 1,
        "mean_ms": round(total_time, 2)
    })
        
    with open("metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)
        
    print("Benchmark complete. Results saved to metrics.json")

if __name__ == "__main__":
    main()
