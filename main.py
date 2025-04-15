import requests
import time
import json
import csv
import argparse
from datetime import datetime


def carregar_api_key(caminho='api_key.txt'):
    with open(caminho, 'r', encoding='utf-8') as f:
        return f.read().strip()


def criar_tarefa(api_key, instagram_link):
    params = {
        'key': api_key,
        'mode': 'create',
        'type': 'p2',
        'act': '2',
        'name': f'Coleta do post {instagram_link[-12:]}',
        'links': instagram_link,
        'spec': '1,2',
        'dop': '3',   # Avatar removido (sem o 17)
        'limit': '10000',
        'posts_limit': '1',
        'unique': '1'
    }
    response = requests.get('https://parser.im/api.php', params=params)
    data = response.json()

    if data.get('status') == 'ok':
        return data['tid']
    else:
        raise Exception(f"Erro ao criar tarefa: {data.get('text')}")


def aguardar_conclusao(api_key, tid, timeout=10000):
    print("⏳ Aguardando coleta ser concluída...")
    start_time = time.time()
    tentativa = 1

    while True:
        if time.time() - start_time > timeout:
            raise TimeoutError("⏰ Tempo limite atingido. A tarefa não foi concluída.")

        response = requests.get('https://parser.im/api.php', params={
            'key': api_key,
            'mode': 'status',
            'tid': tid
        })
        data = response.json()
        status = str(data.get('tid_status')).strip().lower()
        print(f"Tentativa {tentativa}: Status = {status}")
        tentativa += 1

        if status in ["3", "completed"]:
            print("✅ Coleta concluída!")
            break
        elif status in ["4", "error"]:
            raise Exception("❌ Erro na execução da tarefa.")
        elif status in ["2", "suspended"]:
            raise Exception("⏸️ Tarefa suspensa.")

        time.sleep(60)


def buscar_resultado_e_salvar(api_key, tid, base_nome="resultado"):
    import os

    response = requests.get('https://parser.im/api.php', params={
        'key': api_key,
        'mode': 'result',
        'tid': tid
    })

    texto = response.text.strip()

    if not texto:
        print("❌ Resposta da API está vazia.")
        return None

    # 🧩 Tentar interpretar como JSON
    try:
        data_result = response.json()

        # Salvar JSON
        with open(f"{base_nome}.json", "w", encoding="utf-8") as f_json:
            json.dump(data_result, f_json, indent=4, ensure_ascii=False)
        print(f"✅ JSON salvo em {base_nome}.json")

        # Tentar salvar CSV se houver dados
        if 'data' in data_result and isinstance(data_result['data'], list) and data_result['data']:
            with open(f"{base_nome}.csv", "w", newline='', encoding="utf-8") as f_csv:
                writer = csv.DictWriter(f_csv, fieldnames=data_result['data'][0].keys())
                writer.writeheader()
                writer.writerows(data_result['data'])
            print(f"✅ CSV salvo em {base_nome}.csv")
        else:
            print("⚠️ JSON válido, mas sem dados para salvar como CSV.")

        return data_result

    except Exception:
        # 📄 Se não for JSON, tratar como texto plano e tentar salvar como CSV
        linhas = texto.strip().splitlines()
        if len(linhas) < 2:
            print("❌ Resposta inesperada e insuficiente para salvar.")
            print(texto)
            return None

        headers = linhas[0].split(":")
        dados = [linha.split(":") for linha in linhas[1:]]

        with open(f"{base_nome}.csv", "w", newline='', encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            writer.writerows(dados)

        print(f"✅ CSV salvo como texto plano em {base_nome}.csv")
        return None



def main(link):
    print("🔑 Iniciando coleta com Parser.im")
    api_key = carregar_api_key()

    try:
        tid = criar_tarefa(api_key, link)
        print(f"✅ Tarefa criada com sucesso. TID: {tid}")
        aguardar_conclusao(api_key, tid)

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        base_nome = f"resultado_{timestamp}"

        resultado = buscar_resultado_e_salvar(api_key, tid, base_nome)

        if resultado:
            print("\n📦 Resultado estruturado:")
            print(json.dumps(resultado, indent=2, ensure_ascii=False))

    except Exception as e:
        print(f"❌ Erro: {e}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Extrator de dados do Parser.im via API')
    parser.add_argument('--link', type=str, help='Link do post do Instagram')

    args = parser.parse_args()

    if args.link:
        main(args.link)
    else:
        link = input("Digite o link do post do Instagram: ").strip()
        main(link)