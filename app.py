import time
import urllib.parse
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table
from rich.progress import track
from rich.text import Text
import yaml

console = Console()

def create_driver(use_path=False):
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-logging")
    chrome_options.add_argument("--log-level=3")
    chrome_options.add_argument("--disable-software-rasterizer")
    chrome_options.add_experimental_option("excludeSwitches", ['enable-automation'])
    chrome_options.add_argument("--window-size=900,700")
    chrome_options.add_argument("--window-position=200,100")

    if use_path:
        path = "chromedriver.exe"
        service = Service(path)
    else:
        service = Service(ChromeDriverManager().install())

    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def scrape_tokopedia(keyword, max_scroll=20, wait_time=3):
    keyword_encoded = urllib.parse.quote(keyword)
    main_link = f"https://www.tokopedia.com/search?st=&q={keyword_encoded}"

    driver = create_driver(use_path=False)
    driver.get(main_link)
    time.sleep(wait_time)

    last_count = 0
    for _ in track(range(max_scroll), description="[bold cyan]🔍 Scrolling halaman...[/bold cyan]"):
        driver.execute_script("window.scrollBy(0, 500);")
        time.sleep(wait_time)

        html = driver.page_source
        soup = BeautifulSoup(html, "html.parser")
        produk_containers = soup.find_all("div", class_="gG1uA844gIiB2+C3QWiaKA==")

        if len(produk_containers) == last_count:
            break
        last_count = len(produk_containers)

    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")
    produk_containers = soup.find_all("div", class_="gG1uA844gIiB2+C3QWiaKA==")

    data = []
    for produk in produk_containers:
        nama_produk = produk.find("span", class_="+tnoqZhn89+NHUA43BpiJg==")
        nama_toko = produk.find("span", class_="si3CNdiG8AR0EaXvf6bFbQ== gxi+fsEljOjqhjSKqjE+sw== flip")
        lokasi_toko = produk.find("span", class_="gxi+fsEljOjqhjSKqjE+sw== flip")
        harga = produk.find("div", class_=[
            "urMOIDHH7I0Iy1Dv2oFaNw== HJhoi0tEIlowsgSNDNWVXg==",
            "urMOIDHH7I0Iy1Dv2oFaNw=="
        ])
        promo = produk.find("span", class_="_7UCYdN8MrOTwg0MKcGu8zg==")
        terjual = produk.find("span", class_="u6SfjDD2WiBlNW7zHmzRhQ==")
        rating = produk.find("span", class_="_2NfJxPu4JC-55aCJ8bEsyw==")

        data.append({
            "Nama Produk": nama_produk.get_text(strip=True) if nama_produk else None,
            "Nama Toko": nama_toko.get_text(strip=True) if nama_toko else None,
            "Lokasi Toko": lokasi_toko.get_text(strip=True) if lokasi_toko else None,
            "Harga": harga.get_text(strip=True) if harga else None,
            "Promo/Diskon": promo.get_text(strip=True) if promo else None,
            "Terjual": terjual.get_text(strip=True) if terjual else None,
            "Rating": rating.get_text(strip=True) if rating else None,
        })

    driver.quit()
    return pd.DataFrame(data)

def main():
    banner = Text("""
                  /                                             /               
 /               //                                            //  //           
//////  //////   //   //  //////     //////    //////    ////////  //    ////// 
//    //     //  /////   //     // //     // ///     // //     //  //  //     //
//    //     //  //   // //     // //     // //         //     //  //  //      /
 /////  //////   //   //  ///////  ////////    //////    //////    //    ///// /
                                   //                                            
""", style="bold green")
    console.print(banner)
    console.print(Text("by: iamgalenc", style="bold white"))
    console.print(Panel("[bold yellow]Tokopedia Scraper CLI[/bold yellow]", expand=False))

    keyword = Prompt.ask("[cyan]Masukkan keyword pencarian[/cyan]")
    console.print(f"[cyan]🔎 Mulai scraping data untuk keyword:[/cyan] [bold magenta]{keyword}[/bold magenta]\n")

    df = scrape_tokopedia(keyword, max_scroll=10, wait_time=2)

    console.print(f"[green]Scraping selesai ✅. Total produk terkumpul: {len(df)}[/green]\n")

    if not df.empty:
        table = Table(show_header=True, header_style="bold magenta")
        for col in df.columns:
            table.add_column(col)

        for _, row in df.head(10).iterrows(): 
            table.add_row(*[str(x) if x is not None else "-" for x in row.tolist()])

        console.print(Panel(table, title="[bold cyan]📦 Preview Data[/bold cyan]", expand=False))
        user_format = Prompt.ask("\n[cyan]Pilih format penyimpanan (csv/xlsx/json/yaml)[/cyan]", choices=["csv", "xlsx", "json", "yaml"], default="csv")
        filename = f"tokopedia_scrapper{keyword}.{user_format}"
        if user_format == "csv":
            df.to_csv(filename, index=False, encoding="utf-8-sig")
        elif user_format == "xlsx":
            df.to_excel(filename, index=False, engine="openpyxl")
        elif user_format == "json":
            df.to_json(filename, orient="records", force_ascii=False, indent=2)
        elif user_format == "yaml":
            with open(filename, "w", encoding="utf-8") as f:
                yaml.dump(df.to_dict(orient="records"), f, allow_unicode=True)
        
        console.print(f"[bold green]💾 Data disimpan ke:[/bold green] [yellow]{filename}[/yellow]")

if __name__ == "__main__":
    main()
