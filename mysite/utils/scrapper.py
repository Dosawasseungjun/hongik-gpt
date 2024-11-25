from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from requests import get
import time
import json
from collections import OrderedDict
import re
from selenium_stealth import stealth
import sys
import os
import re
import requests


def remove_special_characters(text):
    # 한글, 영어, 숫자, 공백만 유지하고 나머지 제거
    return re.sub(r"[^a-zA-Z0-9\s가-힣]", "", text)


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from configure import (
    NOTICE_URL,
    NOTICE_ADD_URL,
    NOTICE_FILE_PATH,
    PHONE_NUMBER_OFFICE_URL,
    PHONE_NUMBER_PERSON_URL,
    PHONE_NUMBER_FILE_PATH,
    STUDYROOM_URL,
)


class Scrapper:
    _instance = None
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--blink-settings=imagesEnabled=false")
    options.add_argument("--no-sandbox")
    options.add_argument("enable-automation")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-dev-shm-usage")
    browser = webdriver.Chrome(options=options)

    stealth(
        browser,  # driver 객체를 인자로 전달
        languages=["en-US", "en"],
        vendor="Google Inc.",
        platform="Win32",
        webgl_vendor="Intel Inc.",
        renderer="Intel Iris OpenGL Engine",
        fix_hairline=True,
    )

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(Scrapper, cls).__new__(cls)
        return cls._instance

    def get_notice(self):

        self.browser.get(NOTICE_URL)
        self.browser.implicitly_wait(10)
        soup = BeautifulSoup(self.browser.page_source, "html.parser")

        table = soup.find_all("table")[1]
        sub = re.compile(r"pkid=[0-9]*\^")
        data_list = []
        for notice in table.find_all("tr")[1:]:
            data = OrderedDict()
            td_list = notice.find_all("td")
            data["subject"] = td_list[1].find("span").text
            link = td_list[1].a["href"]
            link = sub.findall(link)[0][:-1]
            data["link"] = f"{NOTICE_ADD_URL}{link}"
            data["name"] = td_list[2].text
            data["date"] = td_list[4].text
            data_list.append(data)

        with open(NOTICE_FILE_PATH, "w") as f:
            json.dump(data_list, f, ensure_ascii=False, indent="\t")

    def get_studyroom_status(self, mode):
        # mode 0 : 학관, mode 1 : T동, mode 2 : R동
        """
        academy_studyroom_url = 'http://203.249.67.222/'
        T_studyroom_url = 'http://203.249.65.81/'
        R_studyroom_url = 'http://223.194.83.66/'
        """

        url_to_studyroom_num = {
            STUDYROOM_URL[0]: 6,
            STUDYROOM_URL[1]: 6,
            STUDYROOM_URL[2]: 3,
        }
        base_url = STUDYROOM_URL[mode]
        # HTTP 요청 헤더
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Referer": "https://www.hongik.ac.kr/"
        }
        
        # HTTP GET 요청
        response = requests.get(base_url, headers=headers)

        # self.browser.get(base_url)
        # self.browser.implicitly_wait(10)
        # 응답 확인
        if response.status_code != 200:
            raise Exception(f"Failed to fetch data. Status code: {response.status_code}")
        soup = BeautifulSoup(response.text, "html.parser")
        # Table 찾기
        tables = soup.find_all("table", {"cellpadding": "0", "cellspacing": "0", "border": "0", "width": "100%"})

        if tables:
            studyroom_status = []
            for table in tables:
                rows = table.find_all("tr")
                main_col = rows[2].find_all("td")
                cols = main_col + rows[3].find_all("td")
                # print(f"{len(cols)}Row data: {[col.text.strip() for col in cols]}")  # 디버깅용
                for i in range(0, 5 * url_to_studyroom_num[STUDYROOM_URL[mode]], 5) :
                    room_name = cols[i].text.strip()
                    total_seats = cols[i+1].text.strip()
                    used_seats = cols[i+2].text.strip()
                    remaining_seats = cols[i+3].text.strip()
                    utilization_rate = cols[i+4].text.strip()
                    studyroom_status.append(
                        {
                            "room_name": room_name,
                            "total_seats": total_seats,
                            "used_seats": used_seats,
                            "remaining_seats": remaining_seats,
                            "utilization_rate": utilization_rate,
                        }
                    )
            # 테스트용
            # for status in studyroom_status:
            #     print(status)
            return studyroom_status
        else:
            print("No tables found.")
            return []

        # # 특정 <td> 요소 찾기
        # td_element = soup.find("td", {"id": "tbl_table", "colspan": "2"})

        # if td_element:
        #     print(td_element.prettify())
        # else:
        #     print("Element not found.")


async def get_phone_number(search_query, mode):
    ##mode 0 : office , 1 : person

    base_url = PHONE_NUMBER_OFFICE_URL if mode == 0 else PHONE_NUMBER_PERSON_URL
    search_query = remove_special_characters(search_query)
    if mode == 0:
        base_url = base_url + f"?mode=list&srSearchKey=name&srSearchVal={search_query}"
    else:
        base_url = base_url + f"?mode=list&srSearchKey=onename&srSearchVal={search_query}"

    # HTTP 요청 헤더
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Referer": "https://www.hongik.ac.kr/",
    }

    # HTTP GET 요청
    response = requests.get(base_url, headers=headers)

    # 응답 확인
    if response.status_code != 200:
        raise Exception(f"Failed to fetch data. Status code: {response.status_code}")
    soup = BeautifulSoup(response.text, "html.parser")
    try:
        data_list = []
        if mode == 1:
            query_result = soup.find("div", "bn-list-card faculty")
            for query in query_result.ul.find_all("li", recursive=False):
                data = OrderedDict()
                data["name"] = query.find("div", "b-name-box").p.text.strip().replace(" ", "")
                data["belong"] = query.find("p", "b-belong").text
                data["spot"] = query.find("p", "b-spot").text
                phone_num = query.find("ul", "ul-type01").li
                data["phone_num"] = phone_num.text if phone_num is not None else "전화번호가 없습니다."
                data_list.append(data)
        else:
            data_list = []
            query_result = soup.find("div", "bn-list-card phone-search")
            for query in query_result.ul.find_all("li", recursive=False):
                data = OrderedDict()
                data["name"] = query.find("p").text.strip().replace(" ", "")
                phone_num = query.find("ul", "ul-type01").li
                data["phone_num"] = phone_num.text if phone_num is not None else "전화번호가 없습니다."
                data_list.append(data)
        return data_list
    except Exception as e:
        print(e)
        return {}


if __name__ == "__main__":
    a = Scrapper()
    dormitory_url = "https://www.hongik.ac.kr/kr/life/seoul-cafeteria-view.do?articleNo=5414&restNo=2"
    staff_url = "https://www.hongik.ac.kr/kr/life/seoul-cafeteria-view.do?articleNo=5413&restNo=3"
    # d1 = a.get_phone_number("요건없을걸", 0)
    # d2 = a.get_phone_number("배성일", 1)
    # print(d1)
    # print(d2)
    a.get_studyroom_status(0)
    a.get_studyroom_status(1)
    a.get_studyroom_status(2)
    # a.get_phone_number("안녕하세요", 0)
    # a.get_phone_number('?', 0)
    # a.get_phone_number('!', 0)
    print(a.get_phone_number("지금 열람실 현황 어때?", 0))
    print(a.get_phone_number("지금 열람실 현황 어때?", 1))
    print(a.get_phone_number("김민", 0))
    print(a.get_phone_number("김민", 1))
