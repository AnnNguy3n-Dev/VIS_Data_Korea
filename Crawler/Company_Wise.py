from Crawler.Base import Base, Chrome
from selenium.webdriver.common.by import By
import time
import json


class Financial_Statements(Base):
    def __init__(self, crawler_type="S"):
        super().__init__(crawler_type)

    def check_valid_request(br, code, rpt_id):
        del br.driver.requests
        time.sleep(1)

        br.find_item(By.ID, f"rpt_tab{rpt_id+1}").click()
        time.sleep(1)
        requests = br.driver.requests
        for _ in range(60):
            try:
                list_valid = []
                for rq in requests:
                    if rq.method == "GET":
                        if rq.url.startswith(
                            f"https://comp.wisereport.co.kr/company/cF3002.aspx?cmp_cd={code}&frq=0&rpt={rpt_id}&finGubun=MAIN&frqTyp=0&cn=&encparam="
                        ) and rq.response is not None:
                            list_valid.append(rq)

                assert len(list_valid) == 1, len(list_valid)
                return list_valid[0]
            except Exception as ex:
                time.sleep(1)
                requests = br.driver.requests
        else:
            raise Exception("Timeout waiting for report!!!!!!")

    def get_data_json(self, code):
        try:
            self.driver.get(f"https://comp.wisereport.co.kr/company/c1030001.aspx?cmp_cd={code}&cn=")
            time.sleep(1)

            try:
                alert = self.driver.switch_to.alert
                alert.accept()
                return "Alert"
            except:
                print(code, "OK")

            tab1 = self.check_valid_request(code, 0)
            tab2 = self.check_valid_request(code, 1)
            tab3 = self.check_valid_request(code, 2)

            return {
                "Tab1": json.loads(tab1.response.body.decode()),
                "Tab2": json.loads(tab2.response.body.decode()),
                "Tab3": json.loads(tab3.response.body.decode()),
            }
        except Exception as ex:
            return f"Error: {ex.args}"
