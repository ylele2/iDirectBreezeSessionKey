import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import pyotp
from breeze_connect import BreezeConnect
import urllib
from credentials import breeze_api_key, breeze_secret_key, breeze_username, breeze_password, breeze_i_secret
from urllib.parse import urlparse, parse_qs
from breeze_connect import BreezeConnect
import datetime
from tabulate import tabulate
import csv



class Browser:
    browser, service = None, None

    # Initialise the webdriver with the path to chromedriver.exe
    def __init__(self, driver: str):
        chrome_options = Options()
        # user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36'
        # profile_path = "C:\\Users\\yashe\\AppData\\Local\\Google\\Chrome\\User Data"
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--user-agent")
        # chrome_options.add_argument(f"user-data-dir={profile_path}")
        # chrome_options.add_argument("--start-maximized")
        #chrome_options.add_argument('--headless=new')
        chrome_options.add_argument("--enalbe-extensions")
        #chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument('--disable-guest-mode')
        chrome_options.add_argument("--incognito")
        #chrome_options.add_argument("--private")
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        self.service = Service(driver)
        self.browser = webdriver.Chrome(service=self.service, options=chrome_options)

        #self.browser.add_cookie(cookie_dict=cookie)
        #self.browser.add_cookie('Path', '/')

    def open_page(self, url: str):
        self.browser.get(url)

    def close_browser(self):
        self.browser.close()

    def add_input(self, by: By, value: str, text: str):
        field = self.browser.find_element(by=by, value=value)
        field.send_keys(text)
        time.sleep(1)

    def click_button(self, by: By, value: str):
        button = self.browser.find_element(by=by, value=value)
        button.click()
        time.sleep(1)


    def login_breeze(self, username: str, password: str):

        self.browser.refresh()
        time.sleep(5)
        self.add_input(by=By.ID, value="txtuid", text=username)
        self.add_input(by=By.ID, value="txtPass",text=password)
        self.click_button(by=By.ID, value="chkssTnc")
        self.click_button(by=By.ID, value="btnSubmit")

        time.sleep(5)


        
        totp = pyotp.TOTP(breeze_i_secret)
        current_time = int(time.time())
        otp = totp.at(current_time)
        print(otp)
        otp_str = str(otp)

        if otp_str != "":            
            i = 1
            for j in otp_str:                
                myval = f'//*[@id="pnlOTP"]/div[2]/div[2]/div[3]/div/div[{i}]/input'
                self.add_input(by=By.XPATH, value=myval, text=j)
                i = i + 1

            self.click_button(by=By.ID, value="Button1")            
            parsed_url = urlparse(self.browser.current_url)
            # Extract query parameters
            query_params = parse_qs(parsed_url.query)
            # Get the 'apisession' parameter value
            apisession_value = query_params.get('apisession', [None])[0]
            return apisession_value
        else:
            print("No OTP Found")
        return self.browser.current_url


if __name__ == '__main__':
    browser = Browser('./driver/chromedriver.exe')

    
    url = "https://api.icicidirect.com/apiuser/login?api_key="+urllib.parse.quote_plus(breeze_api_key)  # Replace with your URL
    
    browser.open_page(url)
    session_key = browser.login_breeze(breeze_username, breeze_password)
    print(session_key)
    browser.close_browser()

    breeze = BreezeConnect(api_key=breeze_api_key)
    breeze.generate_session(api_secret=breeze_secret_key,
                        session_token=session_key)

    iso_date_string = datetime.datetime.strptime("15/06/2024","%d/%m/%Y").isoformat()[:10] + 'T05:30:00.000Z'
    iso_date_time_string = datetime.datetime.strptime("15/07/2024 23:59:59","%d/%m/%Y %H:%M:%S").isoformat()[:19] + '.000Z'

    data = breeze.get_portfolio_holdings(exchange_code="NSE",
                                from_date="2024-01-01T06:00:00.000Z",
                                to_date="2024-07-15T06:00:00.000Z",
                                stock_code="",
                                portfolio_type="")
    



    # Define the headers
    headers = ["Stock Code", "Exchange Code", "Quantity", "Average Price", "Booked Profit/Loss", "Current Market Price", "Change Percentage", "Answer Flag", "Product Type", "Expiry Date", "Strike Price", "Right", "Category Index per Stock", "Action", "Realized Profit", "Unrealized Profit", "Open Position Value", "Portfolio Charges"]

    # Extract the rows from the data
    rows = [
        [
            stock['stock_code'], stock['exchange_code'], stock['quantity'], stock['average_price'], stock['booked_profit_loss'], stock['current_market_price'], stock['change_percentage'], stock['answer_flag'], stock['product_type'], stock['expiry_date'], stock['strike_price'], stock['right'], stock['category_index_per_stock'], stock['action'], stock['realized_profit'], stock['unrealized_profit'], stock['open_position_value'], stock['portfolio_charges']
        ]
        for stock in data['Success']
    ]

    # Print the table
    print(tabulate(rows, headers=headers, tablefmt='grid'))


    # Define the CSV file name
    csv_file_name = 'stock_data.csv'

    # Define the headers
    headers = [
        "stock_code", "exchange_code", "quantity", "average_price", "booked_profit_loss", 
        "current_market_price", "change_percentage", "answer_flag", "product_type", 
        "expiry_date", "strike_price", "right", "category_index_per_stock", "action", 
        "realized_profit", "unrealized_profit", "open_position_value", "portfolio_charges"
    ]

    # Open the CSV file in write mode
    with open(csv_file_name, mode='w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=headers)
        
        # Write the header row
        writer.writeheader()
        
        # Write the data rows
        for stock in data['Success']:
            writer.writerow(stock)

    print(f"Data has been written to {csv_file_name}")

    #print(breeze.get_demat_holdings())
    #print(breeze.get_funds())

    historydata = breeze.get_historical_data(interval="1minute",
                            from_date= "2024-07-14T07:00:00.000Z",
                            to_date= "2024-07-15T07:00:00.000Z",
                            stock_code="ICIBAN",
                            exchange_code="NFO",
                            product_type="futures",
                            expiry_date="2022-08-25T07:00:00.000Z",
                            right="others",
                            strike_price="0")
                            
    #print(historydata)
    

