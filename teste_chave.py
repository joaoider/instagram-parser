with open('api_key.txt', 'r') as f:
    API_KEY = f.read().strip()

print(f"Sua chave lida foi: >>>{API_KEY}<<<")