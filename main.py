import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
from datetime import datetime


if __name__ == '__main__':
    location_search = ['san-francisco-bay-area', 'greater-los-angeles-area', 'greater-seattle-area']
    companies, locations, dates, total_comps, base, stock, bonus = ([] for _ in range(7))
    company_set = set()

    def parse_tc(sections):
        result = []
        for i, section in enumerate(sections):
            parsed = section.replace('K', '').strip()
            if '.' in parsed:
                parsed = parsed.replace('.', '') + '00'
            elif parsed != 'N/A':
                parsed += '000'
            result.append(parsed)

        return result

    def get_url(offset, q_location, limit):
        return f'http://www.levels.fyi/t/software-engineer/locations/{q_location}?offset={offset}&limit={limit}&yoeChoice=custom&minYoe=0&maxYoe=3&sinceDate=month&sortBy=total_compensation&sortOrder=DESC'

    page_offset, item_limit = 0, 50

    for location_index in range(len(location_search)):
        keep_going = True
        page_offset = 0
        while keep_going:
            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
            driver.get(get_url(page_offset, location_search[location_index], item_limit))

            results = set()

            button = driver.find_element(By.CLASS_NAME, "css-138d0dn").find_element(By.TAG_NAME, "div").find_element(By.TAG_NAME, "button")
            button.click()

            nxt_button = driver.find_element(By.CLASS_NAME, "css-138d0dn").find_element(By.TAG_NAME, "div").find_element(
                By.TAG_NAME, "button")
            nxt_button.click()

            content = driver.page_source
            soup = BeautifulSoup(content, "lxml")

            for row in soup.findAll(attrs={'class': 'MuiTableRow-root css-5mf6ol'}):
                if row.text == 'No salaries found':
                    keep_going = False
                    break
                for cell in row.children:
                    for element in cell.children:
                        paras = element.find_all('p')
                        spans = element.find_all('span')

                        if paras:
                            if '$' in paras[0].text:
                                total_comps.append(int(paras[0].text.replace('$', '').replace(',', '')))
                            else:
                                locations.append('N/A')
                                companies.append('N/A')
                                dates.append('N/A')

                            tc_breakdown = spans[2] if len(spans) == 3 else spans[0]
                            tc_sections = tc_breakdown.text.split('|')

                            if len(tc_sections) == 3:
                                parsed_sections = parse_tc(tc_sections)
                                base.append(parsed_sections[0])
                                stock.append(parsed_sections[1])
                                bonus.append(parsed_sections[2])
                        else:
                            for span in spans:
                                company_tag = span.find('a')
                                if company_tag:
                                    company_name = company_tag.text
                                    companies.append(company_name)
                                    if company_name not in company_set:

                                        company_set.add(company_name)
                                elif len(span.text.split('|')) == 2:
                                    location, date = span.text.split('|')
                                    locations.append(location.rstrip())
                                    date = datetime.strptime(date.lstrip(), '%m/%d/%Y')
                                    dates.append(date)

            page_offset += 50

    df = pd.DataFrame({'Company': companies, 'Location': locations, 'Date of Posting': dates,
                       'Total Compensation': total_comps, 'Base': base, 'Stock': stock, 'Bonuses': bonus})
    df.to_csv('data.csv', index=False, encoding='utf-8')

    company_df = pd.DataFrame({'CompanyName': list(company_set)})
    company_df.to_csv('companies.csv', index=False, encoding='utf-8')
