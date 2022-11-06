import re
import json
import pandas as pd
import requests
import os
import selenium
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from bs4 import BeautifulSoup
os.chdir(r"/Users/woohun/Desktop/CSUN Fall 2022/COMP 490/MacroTrendsScrape-main")

def get_url(driver, ticker):

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

def scrape_financials(responses, url, **kwargs):
    session = requests.Session()
    session.headers.update(
        {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.121 Safari/537.36'}
    )
    # 4 sections of financial statements
    for section in ["income-statement", "balance-sheet", "cash-flow-statement", "financial-ratios"]:
        # flag for quarterly, set to False if not needed
        quarterly = True
        if quarterly:
            url += section + "?freq=Q"
        else:
            url += section
        responses[section] = session.get(url, **kwargs)
    return responses

# scrape from passed url
def scrape(url, **kwargs):

    session = requests.Session()
    session.headers.update(
        {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.121 Safari/537.36'}
    )
    response = session.get(url, **kwargs)
    return response

def main():
    # get input, 1 ticker only (for now)
    ticker = input('Ticker: ')

    # initialize firefox settings
    opts = Options()
    opts.add_argument("-profile")
    # profile path with adblock already installed
    opts.add_argument("/Users/woohun/Library/Application Support/Firefox/Profiles/csgziamy.selenium-adblock")

    # create driver instance
    driver = webdriver.Firefox(options=opts)

    # open browser instance, search for ticker
    base_url = get_url(driver, ticker)

    # possible sections: "stock-price-history", "financial statements", "revenue", "total-assets",
    #                    "profit margins", "pe-ratio", "current-ratio", "divident-yield-history"
    # create dictionary of responses of (section, data) key-value pairs
    responses = dict()
    for section in [scrape_financials]:
        section(responses, base_url)
    print(responses["income-statement"].text)
    return

if __name__ == "__main__":
    main()