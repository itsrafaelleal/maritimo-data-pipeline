import requests

url = "https://lp.julianoalvesinvest.com.br/p1-black-vitalicia-pml/?sck=1794220500251_17942206525252"

headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    )
}

response = requests.get(url, headers=headers, timeout=30)

# Verifica se a requisição foi bem-sucedida
response.raise_for_status()

# Salva o HTML
with open("pagina.html", "w", encoding="utf-8") as arquivo:
    arquivo.write(response.text)

print(f"Status HTTP: {response.status_code}")
print(f"HTML capturado: {len(response.text)} caracteres")
print("Arquivo salvo como pagina.html")