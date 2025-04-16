import os
import re
import ctypes
import asyncio
import platform
from urllib.parse import urlparse
import time
import aiohttp
from bs4 import BeautifulSoup
import json
from datetime import datetime
from colorama import init, Fore, Style
from urllib.parse import unquote


init(autoreset=True)  # Initialize colorama

def set_console_title(title):
    system = platform.system()
    if system == "Windows":
        ctypes.windll.kernel32.SetConsoleTitleW(title)
    else:
        print(f"\33]0;{title}\a", end="", flush=True)

async def get_fuckingfast_link(session, download_url):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"}
    async with session.get(download_url, headers=headers) as response:
        response_text = await response.text()
        soup = BeautifulSoup(response_text, "html.parser")
        scripts = soup.find_all("script")
        pattern = re.compile(r'https://fuckingfast.co/dl/[a-zA-Z0-9_-]+')
        for script in scripts:
            if script.string:
                match = pattern.search(script.string)
                if match:
                    return match.group()
    return None

async def get_datanodes_link(session, download_url):
    parsed_url = urlparse(download_url)
    path_segments = parsed_url.path.split("/")
    file_code = path_segments[1].encode("latin-1", "ignore").decode("latin-1")
    file_name = path_segments[-1].encode("latin-1", "ignore").decode("latin-1")
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Cookie": f"lang=english; file_name={file_name}; file_code={file_code};",
        "Host": "datanodes.to",
        "Origin": "https://datanodes.to",
        "Referer": "https://datanodes.to/download",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    }
    payload = {
        "op": "download2",
        "id": file_code,
        "rand": "",
        "referer": "https://datanodes.to/download",
        "method_free": "Free Download >>",
        "method_premium": "",
        "dl": 1
    }
    async with session.post("https://datanodes.to/download", data=payload, headers=headers, allow_redirects=False) as response:
        if response.status == 200:
            response_text = await response.json()
            url = response_text.get("url")
            # URL decode the link if it exists
            if url:
                url = unquote(url)
            return url
        return None

async def process_links(urls):
    async with aiohttp.ClientSession() as session:
        results = []
        total_urls = len(urls)
        successful = 0
        failed_urls = []
        
        start_time = time.time()
        
        print(f"{Fore.CYAN}[*] Processing {total_urls} URLs...")
        print(f"{Fore.YELLOW}╔{'═' * 70}╗")
        
        for index, url in enumerate(urls):
            url = url.strip()
            if url:
                parsed_url = urlparse(url)
                download_link = None
                service_name = ""
                
                if "fuckingfast.co" in parsed_url.netloc:
                    service_name = "Fuckingfast"
                    progress = f"[{index + 1}/{total_urls}] Processing {service_name}"
                    print(f"{Fore.YELLOW}║ {Fore.CYAN}{progress:<68}{Fore.YELLOW}║")
                    set_console_title(f"Fuckingfast Link Generator - {index + 1}/{total_urls}")
                    download_link = await get_fuckingfast_link(session, url)
                elif "datanodes.to" in parsed_url.netloc:
                    service_name = "Datanodes"
                    progress = f"[{index + 1}/{total_urls}] Processing {service_name}"
                    print(f"{Fore.YELLOW}║ {Fore.CYAN}{progress:<68}{Fore.YELLOW}║")
                    set_console_title(f"Datanodes Link Generator - {index + 1}/{total_urls}")
                    download_link = await get_datanodes_link(session, url)
                
                if download_link:
                    successful += 1
                    status_msg = f"✓ {service_name} link extracted"
                    print(f"{Fore.YELLOW}║ {Fore.GREEN}{status_msg:<68}{Fore.YELLOW}║")
                else:
                    failed_urls.append(url)
                    status_msg = f"✗ Failed to extract {service_name} link"
                    print(f"{Fore.YELLOW}║ {Fore.RED}{status_msg:<68}{Fore.YELLOW}║")
                
                results.append({
                    "original_url": url,
                    "download_link": download_link,
                    "success": download_link is not None,
                    "service": service_name
                })
        
        print(f"{Fore.YELLOW}╚{'═' * 70}╝")
        elapsed_time = time.time() - start_time
        
        return {
            "results": results,
            "stats": {
                "total": total_urls,
                "successful": successful,
                "failed": total_urls - successful,
                "success_rate": (successful / total_urls * 100) if total_urls > 0 else 0,
                "elapsed_time": elapsed_time,
                "failed_urls": failed_urls
            }
        }

if __name__ == "__main__":
    if not os.path.exists("links.txt"):
        with open("links.txt", "w") as file:
            print(f"{Fore.RED}[!] Created empty links.txt file. Please add URLs and run again.")
            exit()
            
    with open("links.txt", "r") as file:
        urls = [url.strip() for url in file.readlines() if url.strip()]
    
    if not urls:
        print(f"{Fore.RED}[!] No URLs found in links.txt")
        exit()
    
    print(f"{Fore.CYAN}[*] Starting processing of {len(urls)} URLs...")
    result_data = asyncio.run(process_links(urls))
    
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    
    with open(f"outputs_links_{timestamp}.txt", "w", encoding="utf-8") as output_file:
        for item in result_data["results"]:
            if item["download_link"]:
                output_file.write(f"{item['download_link']}\n")
    
    stats = result_data["stats"]
    
    print("\n")
    print(f"{Fore.CYAN}{Style.BRIGHT}{'╔' + '═' * 48 + '╗'}")
    print(f"{Fore.CYAN}{Style.BRIGHT}║{' ' * 18}SUMMARY REPORT{' ' * 17}║")
    print(f"{Fore.CYAN}{Style.BRIGHT}{'╠' + '═' * 48 + '╣'}")
    
    success_color = Fore.GREEN if stats['success_rate'] > 80 else Fore.YELLOW if stats['success_rate'] > 50 else Fore.RED
    
    print(f"{Fore.CYAN}{Style.BRIGHT}║ {Fore.WHITE}Total URLs processed:{' ' * 16}{stats['total']:<10}{Fore.CYAN}{Style.BRIGHT}║")
    print(f"{Fore.CYAN}{Style.BRIGHT}║ {Fore.GREEN}Successful extractions:{' ' * 14}{stats['successful']:<10}{Fore.CYAN}{Style.BRIGHT}║")
    print(f"{Fore.CYAN}{Style.BRIGHT}║ {Fore.RED}Failed extractions:{' ' * 18}{stats['failed']:<10}{Fore.CYAN}{Style.BRIGHT}║")
    print(f"{Fore.CYAN}{Style.BRIGHT}║ {success_color}Success rate:{' ' * 24}{stats['success_rate']:.2f}%{' ' * 5}{Fore.CYAN}{Style.BRIGHT}║")
    print(f"{Fore.CYAN}{Style.BRIGHT}║ {Fore.WHITE}Time elapsed:{' ' * 24}{stats['elapsed_time']:.2f}s{' ' * 4}{Fore.CYAN}{Style.BRIGHT}║")
    print(f"{Fore.CYAN}{Style.BRIGHT}{'╚' + '═' * 48 + '╝'}")
    
    if stats['failed'] > 0:
        print(f"\n{Fore.RED}{Style.BRIGHT}FAILED URLS:")
        print(f"{Fore.RED}{'─' * 50}")
        for i, failed_url in enumerate(stats['failed_urls'], 1):
            print(f"{Fore.RED}{i}. {failed_url}")
    
    print(f"\n{Fore.GREEN}[*] Download links saved to {Fore.YELLOW}outputs_links_{timestamp}.txt")
    
    # Service-specific stats
    service_stats = {}
    for result in result_data["results"]:
        service = result["service"]
        if service not in service_stats:
            service_stats[service] = {"total": 0, "success": 0, "failed": 0}
        service_stats[service]["total"] += 1
        if result["success"]:
            service_stats[service]["success"] += 1
        else:
            service_stats[service]["failed"] += 1
    
    if service_stats:
        print(f"\n{Fore.CYAN}{Style.BRIGHT}SERVICE-SPECIFIC STATS:")
        print(f"{Fore.CYAN}{'─' * 50}")
        for service, stats in service_stats.items():
            success_rate = (stats["success"] / stats["total"]) * 100 if stats["total"] > 0 else 0
            status_color = Fore.GREEN if success_rate > 80 else Fore.YELLOW if success_rate > 50 else Fore.RED
            print(f"{Fore.WHITE}{service}: {status_color}{stats['success']}/{stats['total']} ({success_rate:.2f}%)")
