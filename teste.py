from selenium import webdriver
from selenium.webdriver.chrome.options import Options

print("1 - Criando opções")

options = Options()
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

print("2 - Iniciando Chrome")

driver = webdriver.Chrome(options=options)

print("3 - Chrome iniciado")

driver.get("https://www.google.com")

print("4 - Google abriu")
print("Título:", driver.title)
print("URL:", driver.current_url)

input("Pressione ENTER para fechar...")

driver.quit()

print("5 - Chrome fechado")