import streamlit as st
import docx
from dotenv import load_dotenv
import os
import time
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

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

@st.experimental_singleton
def load_options():
    # initialize the Chrome driver
    options = Options()
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    options.binary_location = GOOGLE_CHROME_BIN
    #options.add_argument('--headless')
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")
    driver = webdriver.Chrome(options=options, service=ChromeService(ChromeDriverManager().install()))

    # login page
    driver.get("https://trivietedu.ileader.vn/login.aspx")
    # find username/email field and send the username itself to the input field
    driver.find_element("id","user").send_keys(MANAGER_USERNAME)
    # find password input field and insert password as well
    driver.find_element("id","pass").send_keys(MANAGER_PASSWORD)
    # click login button
    driver.find_element(By.XPATH,'//*[@id="login"]/button').click()

    driver.get('https://trivietedu.ileader.vn/Default.aspx?mod=lophoc!lophoc_baihoc')

    class_select = Select(WebDriverWait(driver, 2).until(
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
        if 'DAYS' in row_data.keys() and row_data['DAYS'] != 'DAYS':
            data.append(row_data)

    return data

if st.button("Refresh"):
    st.experimental_singleton.clear()

driver, class_select = load_options()

class_option = st.selectbox(
    'Class',
    tuple([class_name.text for class_name in class_select.options]))

class_select.select_by_visible_text(class_option)
time.sleep(1.5)
baihoc_soup = BeautifulSoup(driver.page_source, "lxml")
hrefs = [delete.a['href'] for delete in baihoc_soup.find_all("li")[17::2]]
if hrefs:
    st.error('This will delete the entire course outline for this class', icon="⚠️")
    if st.button("Delete"):
        with st.spinner('Deleting...'):  
            for href in hrefs:
                driver.execute_script(href)
                time.sleep(.5)
                ok_button = WebDriverWait(driver, 20).until(
                        EC.element_to_be_clickable((By.XPATH,'//*[@id="popup_ok"]')))
                ok_button.click()
                st.write(href)
        st.success("Finished deleting")
        st.experimental_singleton.clear()
else:
    uploaded_file = st.file_uploader("Choose a file")
    if uploaded_file is not None:
        data = docx_to_data(uploaded_file)
        confirm = st.button('Confirm adding course')
        if confirm:
            with st.spinner('Adding...'):
                for i in range(len(data)):
                    time.sleep(1)
                    driver.execute_script("baihoc_add()")
                    time.sleep(1)
                    # Add ngay
                    add_ngay = WebDriverWait(driver, 20).until(
                        EC.element_to_be_clickable((By.XPATH,'//*[@id="zLophoc_baihoc_ngay"]')))
                    add_ngay.clear()
                    ngay = data[i]['DAYS'].split('\n')[1]
                    add_ngay.send_keys(ngay, Keys.ENTER)
                    # Add Lesson
                    driver.switch_to.frame(0)
                    add_lesson = WebDriverWait(driver, 20).until(
                        EC.element_to_be_clickable((By.XPATH,'/html/body')))
                    add_lesson.click()
                    lesson = f"{data[i]['UNITS']}\n{data[i]['PAGES']}\n{data[i]['LANGUAGE FOCUS']}"
                    add_lesson.send_keys(lesson)
                    driver.switch_to.default_content()
                    # Submit
                    driver.execute_script("checkform()")
                    st.success(f"{class_option}-{ngay}", icon="✅")
                st.experimental_singleton.clear()