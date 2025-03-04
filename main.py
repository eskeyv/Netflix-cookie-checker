import json
import os
import sys
import asyncio
import time
import aiohttp
from bs4 import BeautifulSoup
from colorama import Fore

print(Fore.YELLOW + "Initializing!, Please wait...\n" + Fore.RESET)
working_cookies_path = "working_cookies"
exceptions = 0
working_cookies = 0
expired_cookies = 0
duplicate_cookies = 0
start = time.time()
plan = None
email = None

num_threads = 5  # <--- Define the number of threads here

# ___________________________________________
# | Network Speed | Recommended no. threads |
# |---------------|-------------------------|
# | < 5 Mbps      | 1-3                     |
# | 5-20 Mbps     | 3-5                     |
# | 20-100 Mbps   | 5-10                    |
# | > 100 Mbps    | 10-20                   |
# |_________________________________________|


headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "Referer": "https://www.netflix.com/login",
    "DNT": "1",
    "Sec-GPC": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-User": "?1",
}


async def load_cookies_from_json(json_cookies_path):
    with open(json_cookies_path, "r", encoding="utf-8") as cookie_file:
        cookie = json.load(cookie_file)
    return cookie


async def open_webpage_with_cookies(session, link, json_cookies, filename):
    global working_cookies, expired_cookies, plan, email, duplicate_cookies

    # Request the page
    await session.get(link)

    # Clear all existing cookies
    session.cookie_jar.clear()

    for cookie in json_cookies:
        session.cookie_jar.update_cookies({cookie["name"]: cookie["value"]})

    async with session.get(link, headers=headers, timeout=10) as response:
        content = await response.text()
        soup = BeautifulSoup(content, "lxml")
        if soup.find(string="Sign In") or soup.find(string="Sign in"):
            print(Fore.RED + f"[❌] Cookie Not working - {filename}" + Fore.RESET)
            expired_cookies += 1
        else:
            try:
                plan = (
                    soup.select_one(
                        "div.account-section:nth-child(2) > section:nth-child(2) > div:nth-child(1) > div:nth-child(1) > div:nth-child(1) > div:nth-child(1) > b:nth-child(1)"
                    ).text
                    or soup.select_one(".default-ltr-cache-10ajupv").text
                )
                email = soup.select_one(".account-section-email").text
            except AttributeError:
                plan = (
                    "Premium"
                    if soup.find(string="Premium")
                    else (
                        "Basic"
                        if soup.find(string="Basic")
                        else "Standard" if soup.find(string="Standard") else "Unknown"
                    )
                )

                os.mkdir(working_cookies_path)
                return content  # Return content if the cookie is working


async def process_cookie_file(filename):
    global duplicate_cookies, working_cookies
    filepath = os.path.join("json_cookies", filename)
    if os.path.isfile(filepath):
        with open(filepath, "r", encoding="utf-8"):
            url = "https://www.netflix.com/YourAccount"
            try:
                cookies = await load_cookies_from_json(filepath)
                async with aiohttp.ClientSession() as session:
                    content = await open_webpage_with_cookies(
                        session, url, cookies, filename
                    )

                    additional_json = {
                        "_comment": "Cookie Checked by https://github.com/matheeshapathirana/Netflix-cookie-checker",
                        "Credits": "Matheesha Pathirana",
                        "Discord Server": "https://discord.gg/RSCdKeKB5X",
                        "Special Thanks": "- To all the contributors who have helped improve this project by submitting pull requests.\n- To everyone who has starred the project and supported our work",
                        "Disclaimer": "This project is for educational purposes only. The authors and contributors are not responsible for how it is used.",
                        "Support": "If you find this project helpful, consider supporting it by starring the project on GitHub, contributing to the code, or making a donation on Ko-fi. Your support helps keep the project alive and encourages further improvements!",
                    }
                    if content:
                        try:
                            cookies.append(additional_json)
                            # Save working cookies to JSON file
                            with open(
                                f"working_cookies/[{email}] - {plan}.json", "w"
                            ) as json_file:
                                json.dump(cookies, json_file, indent=4)
                            working_cookies += 1
                        except FileExistsError:
                            print(
                                Fore.YELLOW
                                + f"[⚠️] Duplicate Cookie - {filename} | Plan: {plan} | Email: {email}"
                                + Fore.RESET
                            )
                            duplicate_cookies += 1

                        print(
                            Fore.GREEN
                            + f"[✔️] Cookie Working - {filename} | Plan: {plan} | Email: {email}"
                            + Fore.RESET
                        )

            except json.decoder.JSONDecodeError:
                print(
                    Fore.RED
                    + f"[⚠️] Please use cookie_converter.py to convert your cookies to json format! (File: {filename})\n"
                    + Fore.RESET
                )
                global exceptions
                exceptions += 1
            except FileExistsError:
                print(
                    Fore.YELLOW
                    + f"[⚠️] Duplicate Cookie - {filename} | Plan: {plan} | Email: {email}"
                    + Fore.RESET
                )
                duplicate_cookies += 1

            except Exception as e:
                print(
                    Fore.RED + f"[⚠️] Error occurred: {str(e)} - {filename}" + Fore.RESET
                )
                exceptions += 1


async def main():
    try:
        os.path.isdir("json_cookies")
        try:
            if os.path.isdir("working_cookies"):
                print(
                    Fore.RED
                    + "[⚠️] working_cookies folder already exists, new cookies will be appended.\n"
                    + Fore.RESET
                )

            tasks = []
            for filename in os.listdir("json_cookies"):
                task = asyncio.create_task(process_cookie_file(filename))
                tasks.append(task)
                if len(tasks) >= num_threads:
                    await asyncio.gather(*tasks)
                    tasks = []
            if tasks:
                await asyncio.gather(*tasks)
        except FileNotFoundError:
            tasks = []
            for filename in os.listdir("json_cookies"):
                task = asyncio.create_task(process_cookie_file(filename))
                tasks.append(task)
                if len(tasks) >= num_threads:
                    await asyncio.gather(*tasks)
                    tasks = []
            if tasks:
                await asyncio.gather(*tasks)
    except FileNotFoundError:
        print(
            Fore.RED
            + "[⚠️] Error Occurred: Please use cookie_converter.py to convert cookies."
            + Fore.RESET
        )
        sys.exit()


try:
    asyncio.run(main())
    end = time.time()
    print(
        Fore.YELLOW
        + f"\nSummary:\nTotal Cookies: {len(os.listdir('json_cookies'))}\nWorking Cookies: {working_cookies}\nExpired Cookies: {expired_cookies}\nDuplicate Cookies: {duplicate_cookies}\nInvalid Cookies: {exceptions}\nTime Elapsed: {round((end - start))} Seconds"
        + Fore.RESET
    )
except KeyboardInterrupt:
    print(Fore.RED + "\n\nProgram Interrupted by user" + Fore.RESET)
    sys.exit()
