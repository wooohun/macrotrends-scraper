import re
import json
import pandas as pd
import requests
import os
import selenium
import shutil
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from bs4 import BeautifulSoup

# set path to proper directory for results placement
os.chdir(r"/Users/woohun/Desktop/CSUN Fall 2022/COMP 490/MacroTrendsScrape-main/Results")

# grabs generic url for given ticker
def get_url(driver: webdriver, ticker: str) -> str:

    base_url = 'https://www.macrotrends.net/'

    # open Firefox at macrotrends.net
    driver.get(base_url)

    # input given ticker into search box
    input_field = driver.find_element(By.CSS_SELECTOR, ".js-typeahead")
    input_field.send_keys(ticker)

    # wait for dropdown field to show, then click
    wait = WebDriverWait(driver, 10)
    field_dropdown_element = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".typeahead__item[data-index='0']")))
    field_dropdown_element.click()

    # grab url of first option, parse to get base url of targeted ticker
    cur_url = driver.current_url
    split_url = cur_url.split("/", 10)
    target_url = base_url + "stocks/charts/" + split_url[5] + "/" + split_url[6] + "/"

    return target_url

# function for scraping data from data tables
def scrape_ratios(responses: dict[str, pd.DataFrame], url: str) -> dict:
    # tabs in price ratio section
    # sections = [
    #     "pe-ratio",
    #     "price-sales",
    #     "price-book",
    #     "price-fcf",
    #     "current-ratio",
    #     "quick-ratio",
    #     "debt-equity-ratio",
    #     "roe",
    #     "roa",
    #     "roi",
    #     "return-on-tangible-equity"
    # ]
    sections = {
        "Price-Earnings": "pe-ratio",
        "Price-Sales": "price-sales",
        "Price-Book": "price-book",
        "Price-Free-Cash-Flow": "price-fcf",
        "Current": "current-ratio",
        "Quick": "quick-ratio",
        "Debt-Equity": "debt-equity-ratio",
        "Return On Equity": "roe",
        "Return On Assets": "roa",
        "Return On Investment": "roi",
        "Return On Tangible Equity": "return-on-tangible-equity"
    }
    # create driver to grab page sources
    driver = create_driver()

    # use bs4 to gather tables from each section
    for name, resource in sections.items():
        # section url
        updated_url = url + resource
        # get section page
        driver.get(updated_url)
        # create soup with lxml parser
        soup = BeautifulSoup(driver.page_source, 'lxml')
        # select historical data table in each section
        table = soup.select("#style-1 > .table")
        # turn table into pandas dataframe
        df = pd.read_html(str(table), index_col = 0)[0]

        # dataframe formatting 
        # name table index column
        df.index.name = 'Date'
        labels = []
        # change multi-indexed column names to singular index
        for column in df.columns:
            labels.append(column[1])
        df.columns = labels
        responses[name] = df
    driver.quit()
    return responses

# only way to scrape financial data is through json + regex, data is loaded in upon request with javascript 
def scrape_financials(responses: dict[str, pd.DataFrame], url: str, **kwargs) -> dict:
    sections = {
        "Income": "income-statement",
        "Balance Sheet": "balance-sheet",
        "Cash Flow": "cash-flow-statement",
        "Financial Ratios": "financial-ratios"
    }
    session = requests.Session()
    session.headers.update(
        {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.121 Safari/537.36'}
    )
    # 4 sections of financial statements
    for name, resource in sections.items():
        # flag for quarterly, set to False if not needed
        quarterly = True
        if quarterly:
            updated_url = url + resource + "?freq=Q"
        else:
            updated_url = url + resource
        # returns object of type Response, contains server's response to HTTP request made by Session object
        response = session.get(updated_url, **kwargs)
        # get data from unicode text of response, store dataframe as value keyed by section name
        responses[name] = financial_data_to_df(response)
    return responses

def financial_data_to_df(response: requests.Response) -> pd.DataFrame:

    #regex to find the data
    num=re.findall('(?<=div\>\"\,)[0-9\.\"\:\-\, ]*',response.text)
    text=re.findall('(?<=s\: \')\S+(?=\'\, freq)',response.text)

    #convert text to dict via json
    dicts=[json.loads('{'+i+'}') for i in num]

    #create dataframe
    df=pd.DataFrame()
    for ind,val in enumerate(text):
        df[val]=dicts[ind].values()
    df.index=dicts[ind].keys()
    
    return df

# create folder for output if doesnt exist, place outputs there
def create_output(responses: dict[str, pd.DataFrame], ticker: str) -> None:
    # target directory for given ticker, change ticker string to upper case for consistency
    path = os.getcwd() + "/" + ticker.upper()
    # check if ticker folder already exists
    if not os.path.exists(path):
        # if not, then create folder
        os.makedirs(path)
    # enter folder
    os.chdir(path)
    # add results into folder
    for section, response in responses.items():
        # default setting is overwriting if existing file of same name exists
        response.to_csv(section + ".csv")
    return

# helper to create Firefox WebDriver
def create_driver() -> webdriver:
    # initialize firefox settings
    opts = Options()
    opts.add_argument("-profile")
    # profile path with adblock already installed
    opts.add_argument("/Users/woohun/Library/Application Support/Firefox/Profiles/csgziamy.selenium-adblock")

    # create driver instance
    driver = webdriver.Firefox(options=opts)
    return driver

def main():
    # get input, 1 ticker only (for now)
    ticker = input('Ticker: ')

    # create driver
    driver = create_driver()
    # open browser instance, search for ticker
    base_url = get_url(driver, ticker)
    # close driver instance
    driver.quit()

    # create dictionary of responses of (section, data) key-value pairs
    responses = dict()
    # different scraping methods for each section: financial statements, ratios(price ratios, other ratios)
    for section in [scrape_financials , scrape_ratios]:
        section(responses, base_url)
    create_output(responses, ticker)
    return

if __name__ == "__main__":
    main()