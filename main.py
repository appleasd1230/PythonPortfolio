#coding:utf-8
from bs4 import BeautifulSoup as bs4
from string import digits
from selenium import webdriver
import requests
import time as t
import re
import pandas as pd
import random

""" 取得論文篇數 """
def get_author_count(author_range):
    if author_range == "First":
        authon_info = "Author - First"
    elif author_range == "All":
        authon_info = "Author"
        
    global first_author_count # 醫生第一作者篇數
    global result_count # 醫生參與論文數
    global doctor_en # 醫生英文名
    global hospital_en # 類別名稱

    Pubmed = '(hyperlipidemia[MeSH Terms] OR \
    hyperlipidemia OR hypercholesterolemia OR \
    hyperlipoproteinemia OR pcsk9) AND \
    ("2014/12/01"[Date - Publication] : "3000"[Date - Publication]) AND \
    (' + doctor_en + '[' + authon_info + '] AND ' + hospital_en + ')'
    Pubmed = Pubmed.replace(' ','%20').replace('[','%5B').replace(']','%5D').replace('"','%22').replace('Date - Publication','PDAT').replace('/','%2F')
    url = 'https://www.ncbi.nlm.nih.gov/pubmed?term=' + Pubmed
    r = requests.get(url)
    soup = bs4(r.text, 'html.parser')

    if author_range == "First":
        first_author_count = int(soup.find(class_ = 'result_count left').text[-1])
    elif author_range == "All":
        result_count = int(soup.find(class_ = 'result_count left').text[-1])

"""取得各頁網址(抓出每頁的連結)"""
def get_url():
    chrome_path = "C:\\Users\\admin\\Desktop\\KOL\\chromedriver.exe" #chromedriver.exe執行檔所存在的路徑
    driver = webdriver.Chrome(chrome_path)
    global url_lst # 呼叫全域變數url_lst
    global doctor_en # 醫生英文名
    global hospital_en # 類別名稱    
    
    # 透過迴圈自動判斷哪幾頁是有資料的，再將其連結儲存起來
    while True:
        # t.sleep(random.randint(10,15))
        Pubmed = '(hyperlipidemia[MeSH Terms] OR \
        hyperlipidemia OR hypercholesterolemia OR \
        hyperlipoproteinemia OR pcsk9) AND \
        ("2014/12/01"[Date - Publication] : "3000"[Date - Publication]) AND \
        (' + doctor_en + '[Author] AND ' + hospital_en + ')'
        Pubmed = Pubmed.replace(' ','%20').replace('[','%5B').replace(']','%5D').replace('"','%22').replace('Date - Publication','PDAT').replace('/','%2F')
        # url = 'https://www.ncbi.nlm.nih.gov/pubmed?term=' + \
        # '(hyperlipidemia%5BMeSH%20Terms%5D%20OR%20hyperlipidemia%5BAll%20F \
        # ields%5D%20OR%20hypercholesterolemia%5BAll%20Fields%5D%20OR%20hyperlipoproteinemia%5BAll%20Fields%5D%20OR%20pcsk9%5BAll%20F \
        # ields%5D)%20AND%20(%222014%2F12%2F01%22%5BPDAT%5D%20%3A%20%223000%22%5BPDAT%5D)%20AND%20(Wang%20YC%5BAuthor%5D%20AND%20Asia%20University%20Hospital)'
        url = 'https://www.ncbi.nlm.nih.gov/pubmed?term=' + Pubmed
        driver.get(url)
        # 判斷當前頁面是否為最後一頁
        source = driver.page_source
        soup = bs4(source, 'html.parser')
        result_count = int(soup.find(class_ = 'result_count left').text[-1])       
        pages = 1 if result_count <= 20 else int(soup.find(class_ = 'page').find('input').get('last'))
        # 如果有下一頁就點下一頁
        for page in range(0, pages):
            item = soup.find_all(class_ = 'rprt')
            for i in item:
                url_lst.append('https://www.ncbi.nlm.nih.gov' + i.find('a').get('href'))
            try:
                driver.find_element_by_link_text('Next >').click() # 點擊下一頁按鈕
            except:
                continue
        driver.close()
        break

"""取得頁面資訊"""
def get_content():
    global first_author_count # 醫生第一作者篇數
    global result_count # 醫生參與論文數
    global url_lst # 呼叫全域變數url_lst
    global csv_lst # 呼叫全域變數csv_lst
    global first_author_lst # 第一作者
    global second_author_lst # 第二作者
    global third_author_lst # 第三作者
    global four_author_lst # 第四作者
    global five_author_lst # 第五作者
    global other_author_lst # 第5+N作者
    global contract_author_lst # 其他作者
    global doctor_ch # 醫生中文
    global doctor_en # 醫生英文
    global hospital_ch # 醫院中文
    global hospital_en # 醫院英文
    global specialty # 類別

    title_lst = [] # 標題清單
    href_lst = [] # 連結清單

    for url in url_lst:
        author_lst = []
        r = requests.get(url)
        soup = bs4(r.text, 'html.parser') # 解析Html
        content = soup.find(class_ = 'rprt_all') # 抓取涵蓋所需內容範圍的Html Tag
        title = content.find('h1').text # 文章標題
        title_lst.append(title) # 將標題存起來
        href_lst.append(url) # 將連結存起來
        authors = content.find(class_ = 'auths').text # 論文作者

        authors = re.split(', ', authors)
        for author in authors:
            author_info = str(''.join([Seq for Seq in author if Seq.isdigit()]))
            if author_info == '':
                author = remove_digits(author) + " : 通訊作者"
            else:
                author = remove_digits(author) + " : 第" + author_info + "作者"
            author_lst.append(author)
        split_author(author_lst)

    # 透過迴圈將資料存取起來
    csv_lst.append([doctor_ch, doctor_en, hospital_ch, hospital_en, specialty, result_count, first_author_count, '', '', '', '', '', '', '', '', ''])
    for i in range(0, len(title_lst)):
        csv_lst.append(['', '', '', '', '', '', '', title_lst[i], first_author_lst[i], second_author_lst[i], \
        third_author_lst[i], four_author_lst[i], five_author_lst[i], other_author_lst[i], contract_author_lst[i], href_lst[i]])

"""區分作者"""
def split_author(author_lst):
    global first_author_lst # 第一作者
    global second_author_lst # 第二作者
    global third_author_lst # 第三作者
    global four_author_lst # 第四作者
    global five_author_lst # 第五作者
    global other_author_lst # 第5+N作者
    global contract_author_lst # 通訊作者

    first_author_temp = [] # 第一作者暫存
    second_author_temp = [] # 第二作者暫存
    third_author_temp = [] # 第三作者暫存
    four_author_temp = [] # 第四作者暫存
    five_author_temp = [] # 第五作者暫存
    other_author_temp = [] # 第5+N作者暫存
    contract_author_temp = [] # 通訊作者暫存    

    for author in author_lst:
        if '第1作者' in author:
            first_author_temp.append(author.replace(' : 第1作者', ''))
        elif '第2作者' in author:
            second_author_temp.append(author.replace(' : 第2作者', ''))
        elif '第3作者' in author:
            third_author_temp.append(author.replace(' : 第3作者', ''))
        elif '第4作者' in author:
            four_author_temp.append(author.replace(' : 第4作者', ''))
        elif '第5作者' in author:
            five_author_temp.append(author.replace(' : 第5作者', ''))
        elif '通訊作者' in author:
            contract_author_temp.append(author.replace(' : 通訊作者', ''))
        else:
            other_author_temp.append(author)

    first_author_lst.append(', '.join(first_author_temp))
    second_author_lst.append(', '.join(second_author_temp))
    third_author_lst.append(', '.join(third_author_temp))
    four_author_lst.append(', '.join(four_author_temp))
    five_author_lst.append(', '.join(five_author_temp))
    other_author_lst.append(', '.join(other_author_temp))
    contract_author_lst.append(', '.join(contract_author_temp))
          
                                                          

"""判斷第幾作者"""
def remove_digits(authors):
    remove_digits = str.maketrans('', '', digits)
    res = authors.translate(remove_digits)
    return res

"""設定CSV的欄位標題"""
def writePandas(data_lst):
    df = pd.DataFrame(data=csv_lst, columns=['醫師中文', '醫生英文', '醫院中文', '醫院英文', '類別', '血脂篇數', '第一作者篇數', '論文標題',\
    '第一作者','第二作者','第三作者', '第四作者', '第五作者', '第N作者', '通訊作者', '連結'])
    return df

"""將存取的資料轉成CSV格式輸出"""
def To_csv():
    global csv_lst
    fileName = 'data' + t.strftime('%y%m%d', t.localtime())
    try:
        df = pd.read_csv('data/csv/' + fileName + '.csv')
        record = df['標題'].values.tolist()
        df = df.append(writePandas(csv_lst), ignore_index=False)
        df.to_csv('data/csv/'+fileName+'.csv', sep=',', encoding='utf_8_sig', index=False)
    except:
        with open('data/csv/'+fileName+'.csv', 'w') as new_csv:
            pass
        df = writePandas(csv_lst)
        df.to_csv(r'data/csv/'+fileName+'.csv', sep=',', encoding='utf_8_sig', index=False)


def get_test():
    chrome_path = "C:\\Users\\admin\\Desktop\\KOL\\chromedriver.exe" #chromedriver.exe執行檔所存在的路徑
    driver = webdriver.Chrome(chrome_path)
    global url_lst
    while True:
        # t.sleep(random.randint(10,15))
        Pubmed = 'Chiu CH[Author - First]'
        Pubmed = Pubmed.replace(' ','%20').replace('[','%5B').replace(']','%5D').replace('"','%22').replace('Date - Publication','PDAT').replace('/','%2F')
        # url = 'https://www.ncbi.nlm.nih.gov/pubmed?term=' + \
        # '(hyperlipidemia%5BMeSH%20Terms%5D%20OR%20hyperlipidemia%5BAll%20F \
        # ields%5D%20OR%20hypercholesterolemia%5BAll%20Fields%5D%20OR%20hyperlipoproteinemia%5BAll%20Fields%5D%20OR%20pcsk9%5BAll%20F \
        # ields%5D)%20AND%20(%222014%2F12%2F01%22%5BPDAT%5D%20%3A%20%223000%22%5BPDAT%5D)%20AND%20(Wang%20YC%5BAuthor%5D%20AND%20Asia%20University%20Hospital)'
        url = 'https://www.ncbi.nlm.nih.gov/pubmed?term=' + Pubmed
        driver.get(url)
        # 判斷當前頁面是否為最後一頁
        source = driver.page_source
        soup = bs4(source, 'html.parser')
        pages = int(soup.find(class_ = 'page').find('input').get('last'))

        for page in range(0, pages):            
            item = soup.find_all(class_ = 'rprt')
            for i in item:
                url_lst.append('https://www.ncbi.nlm.nih.gov' + i.find('a').get('href'))
            try:
                driver.find_element_by_link_text('Next >').click() # 點擊下一頁按鈕
            except:
                continue
        break

if __name__ == '__main__':
    # 設定全域變數
    doctor_ch = '' # 醫生中文
    doctor_en = '' # 醫生英文
    hospital_ch = '' # 醫院中文
    hospital_en = '' # 醫院英文
    specialty = '' # 類別

    first_author_count = 0 # 第一作者篇數
    result_count = 0 # 參與篇數

    data = pd.read_excel (r'KOL_mapping_Name_list.xlsx')
    df = pd.DataFrame(data)
    Human_English_Name = df['English Name'].tolist()
    Human_Chines_Name = df['Physician name'].tolist()
    Hospital_English_Name = df['Hospital/ clinic name'].tolist()
    Hospital_Chinese_Name = df['Hospital Chinese'].tolist()
    Specialty = df['Specialty'].tolist()

    for i in range(0, len(Human_English_Name)):
        url_lst = [] # 全頁網址
        csv_lst = [] # csv內容
        first_author_lst = [] # 第一作者
        second_author_lst = [] # 第二作者
        third_author_lst = [] # 第三作者
        four_author_lst = [] # 第四作者
        five_author_lst = [] # 第五作者
        other_author_lst = [] # 第5+N作者
        contract_author_lst = [] # 通訊作者 
        doctor_ch = Human_Chines_Name[i]
        doctor_en = Human_English_Name[i]
        hospital_ch = Hospital_Chinese_Name[i]
        hospital_en = Hospital_English_Name[i]
        specialty = Specialty[i]

        get_author_count("First") # 取得第一作者篇數
        get_author_count("All") # 取得作者篇數
        get_url()
        get_content()
        To_csv()      
        break
    # 執行函式
    # get_test()

    # get_url() 
    # get_content()  
    # To_csv()
