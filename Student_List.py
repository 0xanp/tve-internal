'''
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
'''