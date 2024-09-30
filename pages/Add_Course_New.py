import streamlit as st
import docx
from dotenv import load_dotenv
import os
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

# getting credentials from environment variables(streamlit secrets)
load_dotenv()
MANAGER_USERNAME = os.getenv("MANAGER_USERNAME")
MANAGER_PASSWORD = os.getenv("MANAGER_PASSWORD")
CHROMEDRIVER_PATH = os.environ.get("CHROMEDRIVER_PATH")
GOOGLE_CHROME_BIN = os.environ.get("GOOGLE_CHROME_BIN")

@st.cache_resource
def load_options():
    # initialize the Chrome driver
    options = Options()
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    options.binary_location = GOOGLE_CHROME_BIN
    options.add_argument('--headless')
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")
    options.add_argument("--ignore-certificate-errors")
    driver = webdriver.Chrome(options=options, service=ChromeService(ChromeDriverManager().install()))
    # login page
    driver.get("http://trivietedu.ileader.vn/login.aspx")
    # find username/email field and send the username itself to the input field
    driver.find_element("id","user").send_keys(MANAGER_USERNAME)
    # find password input field and insert password as well
    driver.find_element("id","pass").send_keys(MANAGER_PASSWORD)
    # click login button
    driver.find_element(By.XPATH,'//*[@id="login"]/button').click()

    driver.get('http://trivietedu.ileader.vn/Default.aspx?mod=lophoc!lophoc_baihoc')

    class_select = Select(WebDriverWait(driver, 2).until(
                EC.element_to_be_clickable((By.XPATH,'//*[@id="idlophoc"]'))))

    return driver, class_select

def generate_dates(start_date, num_dates, target_days):
    days_mapping = {
        'monday': 0,
        'tuesday': 1,
        'wednesday': 2,
        'thursday': 3,
        'friday': 4,
        'saturday': 5,
        'sunday': 6
    }

    # Hardcoded holidays to exclude
    holidays = ["01/01/2024",
                "05/02/2024",
                "06/02/2024",
                "07/02/2024",
                "08/02/2024",
                "09/02/2024",
                "10/02/2024",
                "11/02/2024",
                "12/02/2024",
                "13/02/2024",
                "14/02/2024",
                "15/02/2024",
                "16/02/2024",
                "18/04/2024",
                "30/04/2024",
                "01/05/2024",
                "02/09/2024",
                "03/09/2024"]  # Add more holidays as needed

    target_day_nums = [days_mapping.get(day.lower()) for day in target_days]
    if None in target_day_nums:
        raise ValueError("Invalid day of the week")
    result_dates = []
    current_date = start_date
    while len(result_dates) < num_dates:
        if current_date.weekday() in target_day_nums and current_date.strftime("%d/%m/%Y") not in holidays:
            ordinal_number = len(result_dates) + 1
            result_dates.append((current_date, current_date.strftime("%A"), ordinal_number))
        current_date += timedelta(days=1)

    return result_dates

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

path = "COURSE OUTLINE/COURSE OUTLINE/"
dir_list = os.listdir(path)

driver, class_select = load_options()

class_option = st.selectbox(
    'Class',
    tuple([class_name.text for class_name in class_select.options]))

class_select.select_by_visible_text(class_option)
time.sleep(2)
baihoc_soup = BeautifulSoup(driver.page_source, "lxml")
hrefs = [delete.a['href'] for delete in baihoc_soup.find_all("li")[22::2]]
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
        st.cache_resource.clear()
else:
    # search for correct outline in all courses
    for dir in dir_list:
        file_list = os.listdir(path+dir)
        for f in file_list:
            if "".join(class_option.split("-")[0].split(" ")[:2]).upper() == "".join(f.split(" ")[:2]).upper():
                selected_course_path = path+dir+"/"+f
    course_df = pd.DataFrame(docx_to_data(selected_course_path))
    # Create a form for user input
    with st.form("date_generator_form"):
        start_date = st.date_input("Select start date:", datetime.today())
        target_days = st.multiselect("Select target days of the week:", ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'], ['Friday'])
        
        # Submit button
        submitted = st.form_submit_button("Submit")

    # Process user input and generate dates after form submission
    if submitted:
        # Convert selected target days to lowercase for consistency with the function
        target_days_lower = [day.lower() for day in target_days]

        # Generate dates
        result = generate_dates(start_date, len(course_df) , target_days_lower)
        result = [date[0].strftime('%d/%m/%Y') for date in result]
        course_df['DAYS'] = result
        st.write(course_df)

        with st.spinner('Adding...'):
            for i in range(len(course_df)):
                time.sleep(2)
                driver.execute_script("baihoc_add()")
                time.sleep(2)
                # Add ngay
                add_ngay = WebDriverWait(driver, 20).until(
                    EC.element_to_be_clickable((By.XPATH,'//*[@id="zLophoc_baihoc_ngay"]')))
                add_ngay.clear()
                ngay = course_df.iloc[i]['DAYS']
                add_ngay.send_keys(ngay, Keys.ENTER)
                # Add Lesson
                driver.switch_to.frame(0)
                add_lesson = WebDriverWait(driver, 20).until(
                    EC.element_to_be_clickable((By.XPATH,'/html/body')))
                add_lesson.click()
                lesson = f"{course_df.iloc[i]['UNITS']}\n{course_df.iloc[i]['PAGES']}\n{course_df.iloc[i]['LANGUAGE FOCUS']}"
                add_lesson.send_keys(lesson)
                driver.switch_to.default_content()
                # Submit
                driver.execute_script("checkform()")
                st.success(f"{class_option}-{ngay}", icon="✅")
            st.cache_resource.clear()


        
