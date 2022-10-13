import streamlit as st
import pandas as pd
import docx
import io
from dotenv import load_dotenv
import os
import time
import json
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select

# getting credentials from environment variables(streamlit secrets)
load_dotenv()
MANAGER_USERNAME = os.getenv("MANAGER_USERNAME")
MANAGER_PASSWORD = os.getenv("MANAGER_PASSWORD")
CHROMEDRIVER_PATH = os.environ.get("CHROMEDRIVER_PATH")
GOOGLE_CHROME_BIN = os.environ.get("GOOGLE_CHROME_BIN")

st.set_page_config(
    page_title="Tri Viet Education",
    page_icon=":pager:",
    initial_sidebar_state="expanded",
)

@st.cache(allow_output_mutation=True)
def load_options():
    # initialize the Chrome driver
    options = Options()
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    options.binary_location = GOOGLE_CHROME_BIN
    #options.add_argument('--headless')
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")
    driver = webdriver.Chrome(chrome_options=options, executable_path=CHROMEDRIVER_PATH)

    # login page
    driver.get("https://trivietedu.ileader.vn/login.aspx")
    # find username/email field and send the username itself to the input field
    driver.find_element("id","user").send_keys(MANAGER_USERNAME)
    # find password input field and insert password as well
    driver.find_element("id","pass").send_keys(MANAGER_PASSWORD)
    # click login button
    driver.find_element(By.XPATH,'//*[@id="login"]/button').click()

    driver.get('https://trivietedu.ileader.vn/Default.aspx?mod=lophoc!lophoc_baihoc')

    class_select = Select(WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH,'//*[@id="idlophoc"]'))))

    return driver, class_select

def docx_to_data(file):
    document = docx.Document(file)
    table = document.tables[1]

    # Data will be a list of rows represented as dictionaries
    # containing each row's data.
    data = []
    keys = None
    for i, row in enumerate(table.rows):
        text = (cell.text for cell in row.cells)
        # Establish the mapping based on the first row
        # headers; these will become the keys of our dictionary
        if i == 0:
            keys = tuple(text)
            continue

        # Construct a dictionary for this row, mapping
        # keys to values for this row
        
        row_data = dict(zip(keys, text))
        st.write(row_data)
        if 'DAYS' in row_data.keys() and row_data['DAYS'] != 'DAYS':
            data.append(row_data)

    return data

driver, class_select = load_options()

class_option = st.selectbox(
    'Class',
    tuple([class_name.text for class_name in class_select.options]))

class_select.select_by_visible_text(class_option)

uploaded_file = st.file_uploader("Choose a file")

if uploaded_file is not None:
    data = docx_to_data(uploaded_file)
    #st.write(data)
    confirm = st.button('Confirm adding course')
    if confirm:
        for i in range(3):
            time.sleep(1)
            driver.execute_script("baihoc_add()")
            time.sleep(1)
            # Add ngay
            add_ngay = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH,'//*[@id="zLophoc_baihoc_ngay"]')))
            add_ngay.clear()
            st.write(data[i]['DAYS'])
            ngay = data[i]['DAYS'].split()[1]
            add_ngay.send_keys(ngay, Keys.ENTER)
            break
            # Add Lesson
            driver.switch_to.frame(0)
            add_lesson = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH,'/html/body')))
            add_lesson.click()
            lesson = f"{data[i]['UNITS']}\n\nSB: {data[i]['SB']}\nWB: {data[i]['WB']}\n\n{data[i]['LANGUAGE FOCUS']}"
            add_lesson.send_keys(lesson)
            driver.switch_to.default_content()

            # Add Homework if there is one
            if data[i]['NOTES']:
                driver.switch_to.frame(1)
                add_homework = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH,'/html/body')))
                add_homework.click()
                add_homework.send_keys(data[i]['NOTES'])
                driver.switch_to.default_content()
            
            # Add Thong Bao if there is one
            if data[i]['NOTES']:
                driver.switch_to.frame(2)
                add_thongbao = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH,'/html/body')))
                add_thongbao.click()
                add_thongbao.send_keys(data[i]['NOTES'])
                driver.switch_to.default_content()
            
            # Submit
            driver.execute_script("checkform()")
            st.success(f"{class_option}-{ngay}", icon="✅")
