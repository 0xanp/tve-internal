import os
import time
import streamlit as st
from dotenv import load_dotenv
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from pathlib import Path
from bs4 import BeautifulSoup

# getting credentials from environment variables
load_dotenv()
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
GOOGLE_CHROME_BIN = os.environ.get("GOOGLE_CHROME_BIN")

st.set_page_config(
    page_title="Tri Viet Education",
    page_icon=":pager:",
    initial_sidebar_state="expanded",
)

@st.experimental_singleton
def load_data():
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
    driver.find_element("id","user").send_keys(ADMIN_USERNAME)
    # find password input field and insert password as well
    driver.find_element("id","pass").send_keys(ADMIN_PASSWORD)
    # click login button
    driver.find_element(By.XPATH,'//*[@id="login"]/button').click()
    driver.get("https://trivietedu.ileader.vn/Default.aspx?mod=lophoc!lophoc")
    time.sleep(2)
    soup = BeautifulSoup(driver.page_source,"lxml")
    classes = {}
    class_titles = soup.find('tbody').find_all('tr')
    for class_title in class_titles:
        classes[[c.text for c in class_title][1]] = [c['href'] for c in class_title.find_all(title="Xem danh sách lớp học")][0]
    return driver, classes, soup

refresh = st.button("Refresh")
if refresh:
    st.experimental_singleton.clear()

driver, classes, soup = load_data()

class_option = st.selectbox(
    'Class',
    tuple(classes.keys()))

confirm = st.button('Select')

if confirm:
    st.write(class_option, classes[class_option])
    driver.execute_script(classes[class_option])
    time.sleep(2)
    student_soup = BeautifulSoup(driver.page_source, "lxml")
    table = [soup.find_all('tr') for soup in student_soup.find_all("tbody")][1]
    rows= [row.find_all('td') for row in table]
    students = [student[2].text for student in rows]
    st.write(students)

