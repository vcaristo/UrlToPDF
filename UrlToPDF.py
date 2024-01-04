#!/usr/bin/env python

import base64
import json
import logging
import time
from io import BytesIO
from typing import List
import re
import requests

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from webdriver_manager.chrome import ChromeDriverManager


class UrlToPDF:
    """
     Simple use case:
        pdf_file = UrlToPDF(['https://google.com']).toPDF()
        with open('new_pdf.pdf', "wb") as outfile:
            outfile.write(pdf_file[0].getbuffer())
    """
    driver = None
    print_options = {
        'landscape': False,
        'displayHeaderFooter': True,
        'printBackground': True,
        'preferCSSPageSize': True,
        'paperWidth': 8.5,
        'paperHeight': 11,
        'scale':0.82,
        'headerTemplate':'<span></span>',
    }

    def __init__(self, urls: List[str]):
        self.urls = urls

    def _get_pdf_from_url(self, url, *args, **kwargs):
        self.driver.get(url)

        time.sleep(3)  # allow the page to load, increase/decrease as needed

        print_options = self.print_options.copy()
        result = self._send_devtools(self.driver, "Page.printToPDF", print_options)
        return base64.b64decode(result['data'])

    @staticmethod
    def _send_devtools(driver, cmd, params):
        """
        Method uses cromedriver's api to pass various commands to it.
        """
        resource = "/session/%s/chromium/send_command_and_get_result" % driver.session_id
        url = driver.command_executor._url + resource
        body = json.dumps({'cmd': cmd, 'params': params})
        response = driver.command_executor._request('POST', url, body)
        return response.get('value')

    def _generate_pdfs(self):
        pdf_files = []

        for url in self.urls:
            result = self._get_pdf_from_url(url)
            file = BytesIO()
            file.write(result)
            pdf_files.append(file)

        return pdf_files

    def toPDF(self) -> List[BytesIO]:
        webdriver_options = ChromeOptions()
        webdriver_options.add_argument('--headless')
        webdriver_options.add_argument('--disable-gpu')

        try:
            self.driver = webdriver.Chrome(
                service=ChromeService(ChromeDriverManager().install()),
            )
            result = self._generate_pdfs()
        finally:
            self.driver.close()

        return result

def main():
   
    # scrape the URL for each chapter in the book
    page = requests.get('https://criticallyconsciouscomputing.org/').text


    chs = []

    for i in re.findall('(?:href=\"/[a-z]+\")', page):
        if i not in chs:
            chs.append(i)

    chs = list(map(lambda f: "https://criticallyconsciouscomputing.org/" + f.split('/')[1][:-1] + ".html", chs))
    
    # print each chapter as a PDF
    for idx, item in enumerate(chs):
        name = item.split('/')[-1].split('.')[0]
        with open(f"{idx}_{name}", 'wb') as out:
            print(item)
            pdf = UrlToPDF([item]).toPDF()
            out.write(pdf[0].getbuffer())

main()
