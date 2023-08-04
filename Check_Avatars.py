import os
import time
from datetime import datetime
import streamlit as st
from dotenv import load_dotenv
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

# getting credentials from environment variables
load_dotenv()
MANAGER_USERNAME = os.getenv("MANAGER_USERNAME")
MANAGER_PASSWORD = os.getenv("MANAGER_PASSWORD")
CHROMEDRIVER_PATH = os.environ.get("CHROMEDRIVER_PATH")
GOOGLE_CHROME_BIN = os.environ.get("GOOGLE_CHROME_BIN")


@st.cache_resource
def load_data():
    # initialize the Chrome driver
    options = Options()
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    options.binary_location = GOOGLE_CHROME_BIN
    options.add_argument('--headless')
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
    driver.get("https://trivietedu.ileader.vn/Default.aspx?mod=lophoc!lophoc")
    helper_driver = webdriver.Chrome(options=options, service=ChromeService(ChromeDriverManager().install()))
    # login page
    helper_driver.get("https://trivietedu.ileader.vn/login.aspx")
    # find username/email field and send the username itself to the input field
    helper_driver.find_element("id","user").send_keys(MANAGER_USERNAME)
    # find password input field and insert password as well
    helper_driver.find_element("id","pass").send_keys(MANAGER_PASSWORD)
    # click login button
    helper_driver.find_element(By.XPATH,'//*[@id="login"]/button').click()
    soup = BeautifulSoup(driver.page_source,"lxml")
    classes = {}
    class_titles = soup.find('tbody').find_all('tr')
    for class_title in class_titles:
        classes[[c.text for c in class_title][1]] = [c['href'] for c in class_title.find_all(title="Xem danh sách lớp học")][0]
    return driver, helper_driver, classes, soup

if st.button("Refresh"):
    st.cache_resource.clear()

driver, helper_driver, classes, soup = load_data()

col1, col2 = st.columns(2)

with col1:
    options = st.multiselect(
        'Select your classes:',
        classes.keys(),
        list(classes.keys())[-1], label_visibility = "collapsed")

with col2:
    all = st.checkbox("All")

if st.button("Check"):
    start_time = datetime.now()
    if all:
        for option in classes.keys():
            driver.execute_script(classes[option])
            time.sleep(2)
            student_soup = BeautifulSoup(driver.page_source, "lxml")
            table = [soup.find_all('tr') for soup in student_soup.find_all("tbody")][1]
            rows= [row.find_all('td') for row in table]
            students = dict(zip([student[2].text for student in rows], [student[1].a['href'] for student in rows]))
            st.success(option)
            for student in students.keys():
                helper_driver.get(f"https://trivietedu.ileader.vn{students[student]}")
                time.sleep(1)
                helper_soup = BeautifulSoup(helper_driver.page_source, "lxml")
                if [img['src'] for img in helper_soup.find_all('img')][-1] == "/images/avatar.png":
                    st.warning(f"{student} : No avatar")
        end_time = datetime.now()
        st.write('Duration: {}'.format(end_time - start_time))
    else:
        start_time = datetime.now()
        for option in options:
            driver.execute_script(classes[option])
            time.sleep(2)
            student_soup = BeautifulSoup(driver.page_source, "lxml")
            table = [soup.find_all('tr') for soup in student_soup.find_all("tbody")][1]
            rows= [row.find_all('td') for row in table]
            students = dict(zip([student[2].text for student in rows], [student[1].a['href'] for student in rows]))
            st.success(option)
            for student in students.keys():
                helper_driver.get(f"https://trivietedu.ileader.vn{students[student]}")
                time.sleep(1)
                helper_soup = BeautifulSoup(helper_driver.page_source, "lxml")
                if [img['src'] for img in helper_soup.find_all('img')][-1] == "/images/avatar.png":
                    st.warning(f"{student} : No avatar")
        end_time = datetime.now()
        st.write('Duration: {}'.format(end_time - start_time))