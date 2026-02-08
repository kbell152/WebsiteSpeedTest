#!/usr/bin/env python3
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time


def test_load_time_with_selenium(url):
    # Path to your WebDriver (change to your local path)
    webdriver_path = "/usr/local/bin/chromedriver"
    service = ChromeService(executable_path=webdriver_path)
    driver = webdriver.Chrome(service=service)

    try:
        # Record the start time
        start_time = time.time()

        # Open the URL
        driver.get(url)

        # Wait for the page to fully load (you can customize this wait condition)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        # Record the end time
        end_time = time.time()

        # Calculate the load time
        load_time = end_time - start_time

        print(f"Website {url} loaded successfully.")
        print(f"Load Time: {load_time:.2f} seconds")

    except Exception as e:
        print(f"An error occurred: {e}")

    finally:
        # Close the browser
        driver.quit()


# Example usage
url_to_test = "https://gtmetrix.com/"
test_load_time_with_selenium(url_to_test)
