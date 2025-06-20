import time
from selenium import webdriver
# from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import requests
import csv
import pickle
import os
from bs4 import BeautifulSoup 


def driver_login():
    try:
        options = Options()
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size")
        options.add_argument("--log-level=3") 
       
        # service = ChromeService(chrome_driver_path)

        return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    except Exception as e:
        print("⚠️ Login failed due to exception:", e)
        return False
    
def manual_login(driver, wait):
    """Waiting for manual login"""

    max_wait = 300
    start = time.time()

    while time.time() - start < max_wait:
        try:
            for selector in [
                (By.CLASS_NAME, "nav-user-icon"),
                (By.CSS_SELECTOR, "[data-cy='nav-user-icon']"),
                (By.XPATH, "//div[contains(@class, 'user-avatar')]")
            ]:
                try:
                    element = wait.until(EC.presence_of_element_located(selector))
                    if element:
                        return True, "✅ Logged in! Type **.LeetProblems** to view your problems"
                except:
                    continue
            
            if "login" not in driver.current_url.lower():
                return True, "Assuming successful login"
            time.sleep(2)
        
        except Exception as e:
            print(f"Error while waiting to login: {str(e)}")
            continue
    return False, "❌ TIMEOUT"

COOKIE_DIR = "cookies"

def save_cookies(driver, user_id):
    os.makedirs(COOKIE_DIR, exist_ok=True)
    with open(f"{COOKIE_DIR}/{user_id}_cookies.pkl", "wb") as file:
        pickle.dump(driver.get_cookies(), file)

def load_cookies(driver, user_id):
    path = f"{COOKIE_DIR}/{user_id}_cookies.pkl"
    if not os.path.exists(path):
        return False

    with open(path, "rb") as file:
        cookies = pickle.load(file)

    driver.get("https://leetcode.com")  # Required before adding cookies
    for cookie in cookies:
        if "sameSite" in cookie and cookie["sameSite"] == "None":
            cookie["sameSite"] = "Strict"  # Avoid errors with Chrome
        try:
            driver.add_cookie(cookie)
        except Exception as e:
            print(f"Error setting cookie: {e}")
            continue
    return True

def reset_login(user_id):
    try:
        cookie_path = f"{COOKIE_DIR}/{user_id}_{COOKIE_DIR}.pkl"
        if os.path.exists(cookie_path):
            os.remove(cookie_path)
            return "✅ Reset Login"
        return "❌ No existing login"
    except:
        return "❌ Error. No existing login"

def login(user_id):
    driver = None
    try:
        print(f"User {user_id} prompted login")
        driver = driver_login()
        wait = WebDriverWait(driver, 1)

        # Try to load existing session cookies
        if load_cookies(driver, user_id):
            driver.get("https://leetcode.com/problemset/")
            time.sleep(3)
            if "login" not in driver.current_url.lower():
                return "✅ Using saved session" # return download_problem_csv(driver, user_id)
            print("🔒 Saved session expired, user needs to log in again")

        # No valid cookies; prompt manual login
        print("➡️ Opening manual login")
        driver.get("https://leetcode.com/accounts/login/?next=%2Fproblemset%2F")
        manual, statment = manual_login(driver, wait)
        if not manual:
            return statment

        save_cookies(driver, user_id)
        return "✅ Logged in"
        # return download_problem_csv(driver, user_id)

    except Exception as e:
        print(f"Login error: {e}")
        return "Error"

    finally:
        if driver:
            driver.quit()

def problem(user_id):
    driver = None
    try:
        print(f"User {user_id} prompted login")
        driver = driver_login()

        if load_cookies(driver, user_id):
            driver.get("https://leetcode.com/problems")
            wait = WebDriverWait(driver, 30)
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "a")))
            html = driver.page_source

            soup = BeautifulSoup(html, 'html.parser')
            all_links = []
            links = []
            for link in soup.find("div", class_="w-full pb-[80px]").find_all('a'):
                links.append({"Name": link.find("div", class_="ellipsis line-clamp-1").get_text(strip=True), "Links":link.get('href', None)})
                if len(links) == 10:
                    all_links.append(links)
                    links = []
                
            return "✅ Retrieved all Problems", all_links

        return "❌ Error please log in", None

    except Exception as e:
        print(f"Login error: {e}")
        return "❌Error", None

    finally:
        if driver:
            driver.quit()

def account(user_id):
    driver = None
    try:
        print(f"User {user_id} prompted login")
        driver = driver_login()

        if load_cookies(driver, user_id):
            driver.get("https://leetcode.com/problems")
            wait = WebDriverWait(driver, 30)
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "a")))
            html = driver.page_source
            time.sleep(3)

            soup = BeautifulSoup(html, 'html.parser')
            user_link = driver.find_element(By.CSS_SELECTOR, "div.pl-3 a").get_attribute("href")
            driver.get(user_link)
            
            wait = WebDriverWait(driver, 30)
            stats_section = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,".flex-1.rounded-lg")))
            time.sleep(3)
            stats_section.screenshot(f"{user_id}_stats.png")

            return f"✅ Account info found"
            

        return "❌ Error please log in"
    except Exception as e:
        print(f"Login error: {e}")
        return "❌Error"

    finally:
        if driver:
            driver.quit()