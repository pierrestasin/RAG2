#!/usr/bin/env python3
"""
Test rapide de la réponse API
"""
import requests
import json

# Test query
response = requests.post('http://localhost:8000/query', json={
    "question": "What is this document about?",
    "model": "gemini-pro-latest",
    "selected_files": ["sciadv.ady9493.pdf"]
})

data = response.json()

print("✅ Response status:", response.status_code)
print("\n📊 Response structure:")
print(json.dumps({
    "model_used": data.get("model_used"),
    "chunks_retrieved": data.get("chunks_retrieved"),
    "sources_count": len(data.get("sources", [])),
    "sources": data.get("sources", [])[:2]  # First 2 sources
}, indent=2))

print("\n📚 Sources format:")
for i, source in enumerate(data.get("sources", [])[:2], 1):
    print(f"\nSource {i}:")
    print(f"  - filename: {source.get('filename')}")
    print(f"  - pages: {source.get('pages')}")
    print(f"  - page_count: {source.get('page_count')}")

print("\n✅ Sources summary:", data.get("sources_summary"))
