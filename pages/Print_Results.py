import os
import time
import base64
import json
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from PyPDF2 import PdfFileMerger
import streamlit as st

# getting credentials from environment variables(streamlit secrets)
load_dotenv()
MANAGER_USERNAME = os.getenv("MANAGER_USERNAME")
MANAGER_PASSWORD = os.getenv("MANAGER_PASSWORD")
CHROMEDRIVER_PATH = os.environ.get("CHROMEDRIVER_PATH")
GOOGLE_CHROME_BIN = os.environ.get("GOOGLE_CHROME_BIN")

st.set_page_config(
    page_title="Tri Viet Education",
    page_icon=":pager:",
    layout="wide",
    initial_sidebar_state="expanded",
)

#@st.experimental_singleton
def load_options():
    # initialize the Chrome driver
    options = Options()
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    options.binary_location = GOOGLE_CHROME_BIN
    options.add_argument('--headless')
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")
    driver = webdriver.Chrome(options=options, service=ChromeService(ChromeDriverManager().install()))

    #set up a second driver just for printing 
    temp_options = webdriver.ChromeOptions()
    settings = {
        "recentDestinations": [{
                "id": "Save as PDF",
                "origin": "local",
                "account": "",
            }],
            "selectedDestinationId": "Save as PDF",
            "version": 2
        }
    prefs = {'printing.print_preview_sticky_settings.appState': json.dumps(settings)}
    temp_options.binary_location = GOOGLE_CHROME_BIN
    temp_options.add_experimental_option('prefs', prefs)
    temp_options.add_argument('--kiosk-printing')
    temp_options.add_argument("--disable-dev-shm-usage")
    temp_options.add_argument("--no-sandbox")
    temp_options.add_argument('--headless')
    temp_driver = webdriver.Chrome(options=options, service=ChromeService(ChromeDriverManager().install()))

    # login page
    driver.get("https://trivietedu.ileader.vn/login.aspx")
    # find username/email field and send the username itself to the input field
    driver.find_element("id","user").send_keys(MANAGER_USERNAME)
    # find password input field and insert password as well
    driver.find_element("id","pass").send_keys(MANAGER_PASSWORD)
    # click login button
    driver.find_element(By.XPATH,'//*[@id="login"]/button').click()

    # click lop hoc
    lop_hoc_button = WebDriverWait(driver, 2).until(
            EC.presence_of_element_located((By.XPATH,'//*[@id="content"]/section/section/section/section/div/div[1]/div[1]/div/div[4]/a')))
    lop_hoc_button.click()

    # click nhap diem
    nhap_diem_button = WebDriverWait(driver, 2).until(
            EC.presence_of_element_located((By.XPATH,'//*[@id="menutop_nhapdiem"]/a/span[2]/span')))
    nhap_diem_button.click() 
    class_select = Select(WebDriverWait(driver, 2).until(
                EC.presence_of_element_located((By.XPATH,'//*[@id="cp_lophoc"]'))))

    return driver, temp_driver, class_select

#if st.button("Refresh"):
#    st.experimental_singleton.clear()
driver, temp_driver, class_select = load_options()

class_option = st.selectbox(
    'Class',
    tuple([class_name.text for class_name in class_select.options]))

class_select.select_by_visible_text(class_option)
# give some time for the webdriver to refresh the site after class selection
time.sleep(1)

test_select = Select(WebDriverWait(driver, 2).until(
                EC.presence_of_element_located((By.XPATH,'//*[@id="maudiem"]'))))

test_option = st.selectbox(
    'Test',
    tuple([test.text for test in test_select.options]))

PDFbyte = bytes('', 'utf-8')
placeholder = st.empty()
printing = placeholder.button('Confirm and Print',disabled=False, key='1')
if printing:
    placeholder.button('Confirm and Print', disabled=True, key='2')
    test_select.select_by_visible_text(test_option)
    time.sleep(2)
    rows = driver.find_elements(By.XPATH,"//table/tbody/tr")
    st.write("Combining", len(rows)-1)
    files = []
    for i in range(1, len(rows)):
        name = WebDriverWait(driver, 2).until(
            EC.presence_of_element_located((By.XPATH,f'//*[@id="dyntable"]/tbody/tr[{i}]/td[2]/div'))).text
        files.append(f'{name}.pdf')
        print_url = WebDriverWait(driver, 2).until(
            EC.presence_of_element_located((By.XPATH,f'//*[@id="dyntable"]/tbody/tr[{i}]/td[2]/a'))).get_attribute('href')
        temp_driver.get(print_url)
        pdf = temp_driver.execute_cdp_cmd("Page.printToPDF", {
        "printBackground": True,"pageRanges":"1"
        }) 
        with open(f'{name}.pdf','wb') as f:
            f.write(base64.b64decode(pdf['data']))
        st.success(f'{name}', icon="✅")
    merger = PdfFileMerger()
    #Iterate over the list of the file paths
    for pdf_file in files:
        #Append PDF files
        merger.append(pdf_file)
    merger.write(f"{class_option}{test_option}.pdf")
    merger.close()
    files.append(f"{class_option}{test_option}.pdf")
    time.sleep(1)
    with open(f"{class_option}{test_option}.pdf", "rb") as pdf_file:
        PDFbyte = pdf_file.read()
    st.download_button(label="Download_PDF",
                    data=PDFbyte,
                    file_name=f"{class_option}{test_option}.pdf",
                    mime='application/pdf')
    for f in files:
        os.remove(f)
    placeholder.button('Confirm and Print', disabled=False, key='3')
    placeholder.empty()
    #st.experimental_singleton.clear()

