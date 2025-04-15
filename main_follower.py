import requests
import time
import json
import csv
import os
from datetime import datetime


def carregar_api_key(caminho='api_key.txt'):
    with open(caminho, 'r', encoding='utf-8') as f:
        return f.read().strip()


def criar_tarefa_conta(api_key, conta_login):
    params = {
        'key': api_key,
        'mode': 'create',
        'type': 'p1',
        'act': '1',
        'name': f"Seguidores de {conta_login}",
        'links': conta_login,
        'spec': '1,2',
        'dop': '3,8,20,21',
        'limit': '1000000',
        'limit2': '0',
        'unique': '1'
    }

    response = requests.get('https://parser.im/api.php', params=params)
    data = response.json()

    if data.get('status') == 'ok':
        return data['tid']
    else:
        raise Exception(f"Erro ao criar tarefa: {data.get('text')}")


def aguardar_conclusao(api_key, tid, timeout=1000000000):
    print("⏳ Aguardando conclusão...")
    start = time.time()
    tentativa = 1

    while True:
        if time.time() - start > timeout:
            raise TimeoutError("⏰ Tempo limite atingido.")

        response = requests.get('https://parser.im/api.php', params={
            'key': api_key,
            'mode': 'status',
            'tid': tid
        })

        data = response.json()
        status = str(data.get('tid_status')).strip().lower()
        count = data.get('count', 0)
        print(f"Tentativa {tentativa}: Status = {status} | Perfis coletados: {count}")
        tentativa += 1

        if status in ['3', 'completed']:
            break
        elif status in ['4', 'error']:
            raise Exception("❌ Erro na tarefa.")
        elif status in ['2', 'suspended']:
            raise Exception("⏸️ Tarefa suspensa.")

        time.sleep(60)


def salvar_resultado(api_key, tid, caminho_saida):
    response = requests.get('https://parser.im/api.php', params={
        'key': api_key,
        'mode': 'result',
        'tid': tid
    })

    texto = response.text.strip()

    if not texto:
        print("❌ Resposta da API está vazia.")
        return

    # Primeiro tenta JSON
    try:
        data = response.json()
        if 'data' in data and isinstance(data['data'], list) and data['data']:
            with open(caminho_saida, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=data['data'][0].keys())
                writer.writeheader()
                writer.writerows(data['data'])
            print(f"✅ CSV salvo como {caminho_saida}")
        else:
            print("⚠️ JSON válido, mas sem dados estruturados para salvar.")
        return
    except Exception:
        pass  # Se falhar, continua para salvar como texto plano

    # Se não for JSON, salva como texto plano (CSV simples)
    try:
        linhas = texto.splitlines()
        headers = linhas[0].split(":")
        dados = [linha.split(":") for linha in linhas[1:]]

        if len(dados) == 0:
            print("⚠️ Nenhum dado para salvar.")
            return

        with open(caminho_saida, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            writer.writerows(dados)

        print(f"✅ CSV salvo como {caminho_saida} (texto plano convertido)")
    except Exception as e:
        print("❌ Erro ao salvar como CSV texto plano.")
        print("Conteúdo bruto:")
        print(texto)
        print("Erro:", e)


def main():
    api_key = carregar_api_key()

    # Cria pasta com data e hora
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    pasta_resultados = f"resultados_{timestamp}"
    os.makedirs(pasta_resultados, exist_ok=True)

    # Lê o arquivo contas.csv
    with open('contas.csv', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            conta = row.get('login')
            if not conta:
                continue

            print(f"\n🚀 Iniciando tarefa para: {conta}")
            try:
                tid = criar_tarefa_conta(api_key, conta)
                print(f"✅ Tarefa criada: {tid}")
                aguardar_conclusao(api_key, tid)

                nome_arquivo = os.path.join(pasta_resultados, f"{conta}.csv")
                salvar_resultado(api_key, tid, nome_arquivo)

            except Exception as e:
                print(f"❌ Erro ao processar {conta}: {e}")


if __name__ == '__main__':
    main()