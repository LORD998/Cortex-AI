import requests

payload = {
    "model": "llama3.1",
    "messages": [{"role": "user", "content": "Que horas são?"}],
    "stream": False,
    "tools": [
        {
            "type": "function",
            "function": {
                "name": "get_current_time",
                "description": "Obtém a data e hora atual do sistema local.",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        }
    ]
}

response = requests.post("http://localhost:11434/api/chat", json=payload)
print("STATUS:", response.status_code)
print("RESPONSE:", response.text)
