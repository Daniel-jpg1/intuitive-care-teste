import re
from pathlib import Path
import requests
from bs4 import BeautifulSoup


BASE_URL = "https://dadosabertos.ans.gov.br/FTP/PDA/"
DEMO_SUBDIR = "demonstracoes_contabeis/"


def _get_soup(url: str) -> BeautifulSoup:
    # Faz um GET e devolve um BeautifulSoup com o HTML da página.
    resp = requests.get(url)
    resp.raise_for_status()
    html = resp.text
    return BeautifulSoup(html, "html.parser")


def acesso_demonstracoes_contabeis() -> str | None:
    # Acessa a URL principal da ANS e retorna a URL completa da pasta 'demonstracoes_contabeis/'.
    url = BASE_URL
    soup = _get_soup(url)
    links = soup.find_all("a")

    for link in links:
        href = link.get("href")
        if href and "demonstracoes_contabeis" in href:
            nova_url = url + href
            return nova_url

    return None


def listar_anos(url_pasta_demonstracoes: str) -> list[int]:
    # Recebe a URL da pasta demonstracoes_contabeis/ e retorna uma lista de anos disponíveis.
    soup = _get_soup(url_pasta_demonstracoes)
    year_links = soup.find_all("a")

    anos: list[int] = []

    for year_link in year_links:
        href = year_link.get("href")
        if not href:
            continue

        href_limpo = href.strip("/")
        if href_limpo.isdigit():
            ano = int(href_limpo)
            anos.append(ano)

    anos.sort()
    return anos


def _listar_zips_de_ano(url_pasta_demonstracoes: str, ano: int) -> list[tuple[int, int, str]]:
    # Lista arquivos .zip de um determinado ano, tentando identificar o trimestre pelo nome. Retorna lista de tuplas: (ano, trimestre, url_zip) onde trimestre é 1, 2, 3 ou 4.
    ano_url = f"{url_pasta_demonstracoes}{ano}/"
    soup = _get_soup(ano_url)
    links = soup.find_all("a")

    resultados: list[tuple[int, int, str]] = []

    for link in links:
        href = link.get("href")
        if not href:
            continue

        if not href.lower().endswith(".zip"):
            continue

        nome = href.lower()

        # Formato antigo: "_1_trimestre", "_2_trimestre", "_3_trim", etc.
        match = re.search(r"([1-4])\s*[_-]?\s*tri", nome)

        # Formato novo: "1T2025.zip", "2T2025.zip"
        if not match:
            match = re.search(r"([1-4])\s*t", nome)

        if not match:
            continue

        trimestre_num = int(match.group(1))
        if trimestre_num not in (1, 2, 3, 4):
            continue

        zip_url = ano_url + href
        resultados.append((ano, trimestre_num, zip_url))

    return resultados



def identificar_zips_ultimos_tres_trimestres(url_pasta_demonstracoes: str) -> list[str]:
    # Varrre todos os anos da pasta demonstracoes_contabeis, encontra zips por trimestre e identifica quais são os zips dos 3 trimestres mais recentes. Retorna uma lista de URLs de zips dos 3 últimos trimestres.
    anos = listar_anos(url_pasta_demonstracoes)
    todos: list[tuple[int, int, str]] = []

    for ano in anos:
        todos.extend(_listar_zips_de_ano(url_pasta_demonstracoes, ano))

    if not todos:
        return []

    todos.sort(key=lambda t: (t[0], t[1]))

    # Pega os 3 últimos "trimestres distintos"
    trimestres_ordenados = [(ano, tri) for ano, tri, _ in todos]
    trimestres_unicos: list[tuple[int, int]] = []
    for ano, tri in trimestres_ordenados:
        if (ano, tri) not in trimestres_unicos:
            trimestres_unicos.append((ano, tri))

    ultimos_tres = trimestres_unicos[-3:]

    # Agora pega todos os zips que pertencem a esses 3 trimestres
    urls_selecionadas: list[str] = []
    for ano, tri, zip_url in todos:
        if (ano, tri) in ultimos_tres:
            urls_selecionadas.append(zip_url)

    return urls_selecionadas


def baixar_arquivos_dos_ultimos_tres_trimestres(destino_raw: Path) -> list[Path]:
    # Descobre a URL da pasta de demonstracoes contabeis, identifica os zips dos 3 últimos trimestres e baixa todos para a pasta destino_raw. Retorna a lista de caminhos dos arquivos .zip baixados.
    destino_raw.mkdir(parents=True, exist_ok=True)

    url_demonstracoes = acesso_demonstracoes_contabeis()
    if not url_demonstracoes:
        raise RuntimeError("Não foi possível localizar a pasta 'demonstracoes_contabeis'.")

    zip_urls = identificar_zips_ultimos_tres_trimestres(url_demonstracoes)
    caminhos: list[Path] = []

    for zip_url in zip_urls:
        nome_arquivo = zip_url.split("/")[-1]
        caminho = destino_raw / nome_arquivo

        resp = requests.get(zip_url, stream=True)
        resp.raise_for_status()
        with open(caminho, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        caminhos.append(caminho)

    return caminhos


if __name__ == "__main__":
    # Teste rápido
    from pathlib import Path

    base = Path(__file__).resolve().parent.parent
    raw_dir = base / "data" / "raw"
    zips = baixar_arquivos_dos_ultimos_tres_trimestres(raw_dir)
    print("Arquivos baixados:")
    for z in zips:
        print("-", z)
