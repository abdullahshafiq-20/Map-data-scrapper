import csv
import time
import threading
import customtkinter as ctk
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from concurrent.futures import ThreadPoolExecutor, as_completed
import os

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)



def wind_mode_headless():
    chrome_options = Options()
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.6478.127 Safari/537.36")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)

    driver = webdriver.Chrome(options=chrome_options)

    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver

def wind_mode_no_headless():
    chrome_options = Options()
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--no-sandbox")
    # chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.6478.127 Safari/537.36")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)

    driver = webdriver.Chrome(options=chrome_options)

    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver

def extract_links(driver):

    links = set()
    try:
        elements = driver.find_elements(By.CSS_SELECTOR, "a.hfpxzc")
        for element in elements:
            href = element.get_attribute('href')
            if href and 'maps/place/' in href:
                links.add(href)
    except StaleElementReferenceException:
        print("Encountered stale elements, continuing...")
    return list(links)

def save_links_to_csv(links, filename='links.csv'):
    with open(filename, 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['Link'])
        for link in links:
            writer.writerow([link])

def extract_info(driver):
    def custom_wait_condition(driver):
        name = website = phone = None
        try:
            name = driver.find_element(By.CSS_SELECTOR, "h1.DUwDvf").text
        except:
            pass
        try:
            website = driver.find_element(By.CSS_SELECTOR, "a[data-item-id='authority']").get_attribute('href')
        except:
            pass
        try:
            phone = driver.find_element(By.CSS_SELECTOR, "button.CsEnBe[data-tooltip='Copy phone number'] div.Io6YTe").text
        except:
            pass
        return name, website, phone

    try:
        name, website, phone = WebDriverWait(driver, 5).until(custom_wait_condition)
    except TimeoutException:
        print("Timed out waiting for elements")
        name = website = phone = ''

    # If any information is missing, try to extract it using JavaScript
    if not all([name, website, phone]):
        js_result = driver.execute_script("""
            return {
                name: document.querySelector('h1.DUwDvf')?.textContent || '',
                website: document.querySelector('a[data-item-id="authority"]')?.href || '',
                phone: document.querySelector('button.CsEnBe[data-tooltip="Copy phone number"] div.Io6YTe')?.textContent || ''
            }
        """)
        name = name or js_result['name']
        website = website or js_result['website']
        phone = phone or js_result['phone']

    return name, website, phone

def extract_info_parallel(drivers):
    with ThreadPoolExecutor(max_workers=len(drivers)) as executor:
        future_to_driver = {executor.submit(extract_info, driver): driver for driver in drivers}
        results = []
        for future in as_completed(future_to_driver):
            results.append(future.result())
    return results

def save_info_to_csv(info, filename='results.csv', mode='a'):
    with open(filename, mode, newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        if mode == 'w':
            writer.writerow(['NAME', 'WEBSITE', 'PHONE NUMBER'])
        writer.writerow(info)

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Google Maps Scraper")
        self.geometry("600x500")
        ctk.set_appearance_mode("light")
        try:
            ctk.set_default_color_theme(resource_path("color.json"))
        except Exception as e:
            print(f"Error loading color theme: {e}")
            print("Falling back to default theme")
        icon_path = "icon.ico"
        if os.path.exists(icon_path):
            self.after(200, lambda: self.iconbitmap(icon_path))

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(6, weight=1)

        self.title_label = ctk.CTkLabel(self.main_frame, text="Google Maps Scraper", font=ctk.CTkFont(size=20, weight="bold"))
        self.title_label.grid(row=0, column=0, padx=10, pady=(10, 20))

        self.url_entry = ctk.CTkEntry(self.main_frame, placeholder_text="Enter Google Maps URL")
        self.url_entry.grid(row=1, column=0, padx=10, pady=10, sticky="ew")

        self.scroll_time_entry = ctk.CTkEntry(self.main_frame, placeholder_text="Scroll Time (seconds)")
        self.scroll_time_entry.grid(row=2, column=0, padx=10, pady=10, sticky="ew")

        self.csv_filename_entry = ctk.CTkEntry(self.main_frame, placeholder_text="CSV File Name (without extension)")
        self.csv_filename_entry.grid(row=3, column=0, padx=10, pady=10, sticky="ew")

        self.start_button = ctk.CTkButton(self.main_frame, text="Start Scraping", command=self.start_scraping)
        self.start_button.grid(row=4, column=0, padx=10, pady=20)

        self.progress_bar = ctk.CTkProgressBar(self.main_frame)
        self.progress_bar.grid(row=5, column=0, padx=10, pady=10, sticky="ew")
        self.progress_bar.set(0)

        self.cli_output = ctk.CTkTextbox(self.main_frame, height=150)
        self.cli_output.grid(row=6, column=0, padx=10, pady=10, sticky="nsew")
        self.cli_output.insert("0.0", "CLI Output:\n")

    def update_cli_output(self, message):
        self.cli_output.insert("end", message + "\n")
        self.cli_output.see("end")

    def start_scraping(self):
        url = self.url_entry.get()
        scroll_time = int(self.scroll_time_entry.get())
        csv_filename = self.csv_filename_entry.get()

        self.update_cli_output("Scraping in progress...")
        self.start_button.configure(state="disabled")

        threading.Thread(target=self.scrape, args=(url, scroll_time, csv_filename), daemon=True).start()

    def scrape(self, url, scroll_time, csv_filename):
        driver= wind_mode_no_headless()
        driver.get(url)
        self.update_cli_output(f"Scrolling for {scroll_time} seconds...")
        time.sleep(scroll_time)

        links = extract_links(driver)
        save_links_to_csv(links, f"{csv_filename}_links.csv")
        self.update_cli_output(f"Found and saved {len(links)} links.")

        save_info_to_csv([], filename=f"{csv_filename}_results.csv", mode='w')

        driver= wind_mode_headless()
        for i, link in enumerate(links, 1):
            try:
                driver.get(link)
                name, website, phone = extract_info(driver)
                save_info_to_csv([name, website, phone], filename=f"{csv_filename}_results.csv")
                progress = i / len(links)
                self.progress_bar.set(progress)
                self.update_cli_output(f"Processed link {i} of {len(links)}: {name}")
            except Exception as e:
                self.update_cli_output(f"Error processing link {link}: {str(e)}")

        driver.quit()
        self.update_cli_output("Scraping completed!")
        self.start_button.configure(state="normal")

if __name__ == "__main__":
    app = App()
    app.mainloop()