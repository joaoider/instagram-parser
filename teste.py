import requests

# Lê a API key do arquivo txt
with open('api_key.txt', 'r') as f:
    API_KEY = f.read().strip()

# Endpoint para testar a chave
url = 'https://parser.im/api.php'
params = {
    'key': API_KEY,
    'mode': 'countries'
}

response = requests.get(url, params=params)
data = response.json()

if data.get('status') == 'ok':
    print("✅ Sua chave está funcionando!")
    print("Países disponíveis (exemplo):")
    for country in data.get('countries', [])[:1]:  # mostra os 5 primeiros
        print(f"- {country['name']}")
else:
    print("❌ Erro ao validar a chave:")
    print(data.get('text'))