import streamlit as st
import pandas as pd
from dotenv import load_dotenv
import os
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC

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
        columns = row.find_elements(By.XPATH,"./td") # Use dot in the xpath to find elements with in element.
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

def styling():
    # CSS to inject contained in a string
    hide_table_row_index = """
                <style>
                thead tr th:first-child {display:none}
                tbody th {display:none}
                </style>
                """

    # Inject CSS with Markdown
    st.markdown(hide_table_row_index, unsafe_allow_html=True)

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
    course_df = html_to_dataframe(table_header, table_data)
    return driver, course_df

driver, course_df = load_options()

all_courses = st.checkbox('Show All Course')

placeholder = st.empty()

course_option = placeholder.selectbox(
    'Course',
    (list(course_df['Tên Lớp'])),
    disabled=False, 
    key='1'
)

if all_courses:
    placeholder.selectbox(
    'Class',
    (list(course_df['Tên Lớp'])),
    disabled=True, 
    key='2'
    )
    st.table(course_df)

else:
    course_index = course_df.loc[course_df['Tên Lớp']==course_option].index.tolist()[0]+1
    siso_button = WebDriverWait(driver, 3).until(
                EC.element_to_be_clickable((By.XPATH, f'//*[@id="showlist"]/tr[{course_index}]/td[5]/a[1]')))
    driver.execute_script("arguments[0].click();", siso_button)
    table_header = WebDriverWait(driver, 3).until(
                EC.presence_of_all_elements_located((By.XPATH,'//*[@id="static"]/thead/tr/th')))
    table_data = WebDriverWait(driver, 3).until(
                EC.presence_of_all_elements_located((By.XPATH,'//*[@id="ctl10_container"]/tr')))
    temp_df = html_to_dataframe(table_header, table_data)
    # navigate to lop hoc
    driver.get('https://trivietedu.ileader.vn/Default.aspx?mod=lophoc!lophoc')
    st.table(temp_df)
