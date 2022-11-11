# macrotrends-scraper
Scraper for https://macrotrends.net

Takes input of singular ticker

Requires firefox on device, will need to change absolute path to firefox profile in macro_trends_scraper.py

Line 18 of macro_trends_scraper.py requires change of absolute path to preferred location of results

Required Dependencies:

Geckodriver

````
brew (or npm) install geckodriver
````

Selenium

````
pip install selenium
````

Parsers: lxml, html5lib

````
pip install lxml html5lib
````
BeautifulSoup

````
pip install bs4
````

