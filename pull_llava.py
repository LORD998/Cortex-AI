import requests

print("A iniciar o download do Córtex Visual (Llava - 4.7GB)...")
print("Este processo está a decorrer em segundo plano. Quando terminar, a Cortex poderá ver imagens.")

try:
    response = requests.post("http://localhost:11434/api/pull", json={"name": "llava"})
    if response.status_code == 200:
        print("✅ Download completo! O Módulo de Visão está operacional.")
    else:
        print(f"Erro: {response.text}")
except Exception as e:
    print(f"Falha de comunicação com o servidor Ollama: {e}")
