import os
import time
from dotenv import load_dotenv
from webdriver_manager.chrome import ChromeDriverManager
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from pathlib import Path

# getting credentials from environment variables
load_dotenv()
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
DOWNLOAD_PATH = r'{}'.format(os.getenv("DOWNLOAD_PATH"))
STUDENT_LISTS_PATH = r'{}'.format(os.getenv("STUDENT_LISTS_PATH"))

# check if the the download is finished
def is_download_finished(temp_folder):
    firefox_temp_file = sorted(Path(temp_folder).glob('*.part'))
    chrome_temp_file = sorted(Path(temp_folder).glob('*.crdownload'))
    downloaded_files = sorted(Path(temp_folder).glob('*.*'))
    if (len(firefox_temp_file) == 0) and \
       (len(chrome_temp_file) == 0) and \
       (len(downloaded_files) >= 1):
        return True
    else:
        return False

# handling renaming and moving the files
def rename_and_move(class_name):
    time.sleep(1)
    dst = f"{class_name}.xls"
    dst =f"{STUDENT_LISTS_PATH}{dst}"
    os.rename(f"{DOWNLOAD_PATH}download.xls", dst)
    
# initialize the Chrome driver
options = Options()
options.add_experimental_option('excludeSwitches', ['enable-logging'])
driver = webdriver.Chrome(r"C:\Users\anbin\Downloads\chromedriver_win32\chromedriver.exe",chrome_options=options)

# login page
driver.get("https://trivietedu.ileader.vn/login.aspx")
# find username/email field and send the username itself to the input field
driver.find_element("id","user").send_keys(ADMIN_USERNAME)
# find password input field and insert password as well
driver.find_element("id","pass").send_keys(ADMIN_PASSWORD)
# click login button
driver.find_element(By.XPATH,'//*[@id="login"]/button').click()

# click lop hoc
lop_hoc_button = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH,'//*[@id="content"]/section/section/section/section/div/div[1]/div[1]/div/div[4]/a')))
lop_hoc_button.click()

i = 1
while True:
    try:
        class_name = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH,f'//*[@id="showlist"]/tr[{i}]/td[2]/b/a'))).text
        lop_hoc_button = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH,'//*[@id="menutop_lophoc"]/a/span[2]/span')))
        lop_hoc_button.click()
        siso_button = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH,f'/html/body/section/section/section/section/section/section/section/section/div/div/section/div/table/tbody/tr[{i}]/td[5]/a[1]')))
        driver.execute_script("arguments[0].click();", siso_button)
        xuat_excel_button = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH,'/html/body/div[4]/div[1]/div[2]/div[2]/div[1]/div/form[1]/a')))
        driver.execute_script("arguments[0].click();", xuat_excel_button)
        x_button = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH,'//*[@id="cboxClose"]')))
        driver.execute_script("arguments[0].click();", x_button)
        i += 1
        # make sure there's no downloading in progress
        if is_download_finished(DOWNLOAD_PATH):
            rename_and_move(class_name)
        else:
            driver.implicitly_wait(3)
            rename_and_move(class_name)
    except:
        break

# close the webdriver
driver.close()