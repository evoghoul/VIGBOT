import os, requests
api_key = os.getenv("GEMINI_API_KEY")
url = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}'
resp = requests.post(url, headers={'Content-Type': 'application/json'}, json={'contents': [{'parts': [{'text': 'Tell me a long story about a cat'}]}], 'generationConfig': {'maxOutputTokens': 600}})
print(resp.json())
