from seleniumwire.webdriver import Chrome, ChromeOptions
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests
import time


class Base:
    def __init__(self, crawler_type = "S"):
        """
        crawler_type:
            * S : selenium
            * R : requests
        """
        assert crawler_type in ["S", "R"]
        self.crawler_type = crawler_type

        self.driver = None
        self.session = None

        self.reset_crawler()

    def reset_crawler(self):
        self.quit_crawler()

        if self.crawler_type == "S":
            options = ChromeOptions()
            options.add_argument("--disable-blink-features=AutomationControlled")

            prefs = {
                "profile.managed_default_content_settings.images": 2,
                "profile.managed_default_content_settings.geolocation": 2
            }
            options.add_experimental_option("prefs", prefs)
            self.driver = Chrome(options=options)
        elif self.crawler_type == "R":
            self.session = requests.Session()

    def quit_crawler(self):
        try:
            if self.crawler_type == "S":
                self.driver.quit()
            elif self.crawler_type == "R":
                self.session.close()
        except: pass

    def find_item(self, key, value, timeout=30):
        return WebDriverWait(self.driver, timeout).until(EC.presence_of_element_located((key, value)))

    def scroll_to_bottom(self, wait_page_load=3):
        current_height = self.driver.execute_script("return document.body.scrollHeight;")
        while True:
            self.driver.execute_script(f"window.scrollTo(0, {current_height});")
            time.sleep(wait_page_load)
            new_height = self.driver.execute_script("return document.body.scrollHeight;")
            if new_height == current_height: break
            current_height = new_height
