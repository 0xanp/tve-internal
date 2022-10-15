import streamlit as st
import pandas as pd
from dotenv import load_dotenv
import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait
from datetime import datetime, timedelta

# getting credentials from environment variables
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

def html_to_dataframe(table_header, table_data, course_name=None):
    header_row = []
    df_data = []
    for header in table_header:
        header_row.append(header.text)
    for row in table_data:
        columns = row.find_elements(By.XPATH,"./td")
        table_row = []
        for column in columns:
            table_row.append(column.text)
        df_data.append(table_row)
    df = pd.DataFrame(df_data,columns=header_row)
    df = df.iloc[: , 1:]
    if course_name:
        temp = [course_name for i in range(len(df))]
        df['Course'] = temp
    return df

@st.cache(allow_output_mutation=True)
def load_options():
    # initialize the Chrome driver
    options = Options()
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    options.binary_location = GOOGLE_CHROME_BIN
    options.add_argument('--headless')
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
    # navigate to lop hoc
    driver.get('https://trivietedu.ileader.vn/Default.aspx?mod=lophoc!lophoc')
    # pulling the main table
    table_header = WebDriverWait(driver, 3).until(
                EC.presence_of_all_elements_located((By.XPATH,'//*[@id="dyntable"]/thead/tr/th')))
    table_data = WebDriverWait(driver, 3).until(
                EC.presence_of_all_elements_located((By.XPATH,'//*[@id="showlist"]/tr')))
    courses_df = html_to_dataframe(table_header, table_data)
    # navigate to bai hoc
    driver.get('https://trivietedu.ileader.vn/Default.aspx?mod=lophoc!lophoc_baihoc')
    course_select = Select(WebDriverWait(driver, 2).until(
            EC.element_to_be_clickable((By.XPATH,'//*[@id="idlophoc"]'))))
    courses = [course.text for course in course_select.options]
    
    return driver, course_select, courses, courses_df

driver, course_select, courses, courses_df = load_options()

start_date = st.date_input('Select Start Date', datetime.today())

end_date = st.date_input('Select End Date', datetime.today() + timedelta(days=7))

confirm = st.button('Get Test Dates')

if confirm:
    filtered_courses = []
    filtered_tests = []
    filtered_dates = []
    filtered_course_time = []
    filtered_course_rooms = []
    for course in courses:
        course_select.select_by_visible_text(course)
        time.sleep(1)
        # pulling the main table
        table_header = WebDriverWait(driver, 3).until(
                    EC.presence_of_all_elements_located((By.XPATH,'//*[@id="dyntable"]/thead/tr/th')))
        table_data = WebDriverWait(driver, 3).until(
                    EC.presence_of_all_elements_located((By.XPATH,'//*[@id="showlist"]/tr')))

        course_df = html_to_dataframe(table_header, table_data)

        midterm_name = course_df[course_df['Bài học/Lesson'].str.match(r'MIDTERM TEST*') == True]['Bài học/Lesson'].to_list()
        midterm_date = course_df[course_df['Bài học/Lesson'].str.match(r'MIDTERM TEST*') == True]['Ngày'].to_list()
        final_name = course_df[course_df['Bài học/Lesson'].str.match(r'FINAL TEST*') == True]['Bài học/Lesson'].to_list()
        final_date = course_df[course_df['Bài học/Lesson'].str.match(r'FINAL TEST*') == True]['Ngày'].to_list()
        if midterm_date:
            for i in range(len(midterm_date)):
                class_date = datetime.strptime(midterm_date[i],'%d/%m/%Y').date()
                #st.write(courses_df[courses_df['Tên Lớp'].str.match(course)== True]['Diễn Giải'].values[0].split('-'))
                if "CORRECTION" not in str(midterm_name[i]) and class_date <= end_date and class_date >= start_date:
                    filtered_courses.append(course)
                    filtered_tests.append(midterm_name[i])
                    temp = courses_df[courses_df['Tên Lớp'].str.match(course)== True]['Diễn Giải'].values[0].split('-')
                    course_time = f'{temp[0].split("Room")[0]}-{temp[1].split(")")[0]})'
                    filtered_course_time.append(course_time)
                    temp_1 = temp[2].split(" ")[1]
                    temp_2 = temp[2].split(" ")[2].split("\n")[0]
                    room = f'{temp[1].split(")")[1]}-{temp_1} {temp_2}'
                    filtered_course_rooms.append(room)
                    class_date = f"{class_date.strftime('%A')} {midterm_date[i]}"
                    filtered_dates.append(class_date)
                    st.write(f'{course}-{midterm_name[i]}-{course_time}-{room}-{class_date}')
                    st.success(course, icon="✅")
        if final_date:
            for i in range(len(final_date)):
                class_date = datetime.strptime(final_date[i],'%d/%m/%Y').date()
                if  class_date <= end_date and class_date >= start_date:
                    filtered_courses.append(course)
                    filtered_tests.append(final_name[i])
                    temp = courses_df[courses_df['Tên Lớp'].str.match(course)== True]['Diễn Giải'].values[0].split('-')
                    course_time = f'{temp[0].split("Room")[0]}-{temp[1].split(")")[0]})'
                    filtered_course_time.append(course_time)
                    temp_1 = temp[2].split(" ")[1]
                    temp_2 = temp[2].split(" ")[2].split("\n")[0]
                    room = f'{temp[1].split(")")[1]}-{temp_1} {temp_2}'
                    filtered_course_rooms.append(room)
                    class_date = f"{class_date.strftime('%A')} {final_date[i]}"
                    filtered_dates.append(class_date)
                    st.write(f'{course}-{final_name[i]}-{course_time}-{room}-{class_date}')
                    st.success(course, icon="✅")
    df = pd.DataFrame()
    df['Course'] = filtered_courses
    df['Test'] = filtered_tests
    df['Date'] = filtered_dates
    df['Class Time'] = filtered_course_time
    df['Room'] = filtered_course_rooms
    st.table(df)