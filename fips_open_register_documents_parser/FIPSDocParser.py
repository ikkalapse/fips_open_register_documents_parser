# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup
import re


class FIPSDOCParser:

    def __init__(self, html_data, **kwargs):
        self.html_data = html_data
        self.soup = BeautifulSoup(self.html_data, 'html.parser')
        self.main = self.soup.find('div', {'id': 'main'})
        self.bib = self.soup.find('table', {'id': 'bib'})
        self.parsed = {'title': None,
                       'authors': None,
                       'holders': None,
                       'reg_number': None,
                       'reg_date': None,
                       'app_number': None,
                       'app_date': None}

    def parse(self):
        raise NotImplementedError()


class FIPSDocEVMparser(FIPSDOCParser):

    def parse(self):
        self.parsed['registration number'] = self.find_regnumber(self.bib)  # registration number
        self.parsed['registration date'] = self.find_regdate(self.bib)  # registration date
        self.parsed['publication date'] = self.find_pubdate(self.bib)  # publication date
        self.parsed['application data'] = self.find_application(self.bib)  # application
        self.parsed['application number'] = self.parsed['application data'][0]  # application number
        self.parsed['application date'] = self.parsed['application data'][1]  # application date
        self.parsed['authors'] = self.find_authors(self.bib)  # authors
        self.parsed['right holders'] = self.find_right_holders(self.bib)  # right holders
        self.parsed['title'] = self.find_title(self.main)  # title
        self.parsed['abstract'] = self.find_abstract(self.main)  # abstract
        self.parsed['tool'], self.parsed['size'], self.parsed['pc'], self.parsed['os'], self.parsed['abstract'] = \
            self.find_extra(self.main)  # extra data

    def find_extra(self, main):
        titabs = main.find_all('p', {'class': 'TitAbs'})
        tool = '' # tool
        size = '' # size
        pc = '' # pc
        os = '' # operation system
        abstract = '' # abstract
        if len(titabs) == 6:
            tool = self.find_tool_db(main)
            size = self.find_size_db(main)
            pc = self.find_pc_db(main)
            os = self.find_os_db(main)
        else:
            tool = self.find_tool_evm(main)
            size = self.find_size_evm(main)
            pc = self.find_pc_evm(main, abstract)
            os = self.find_os_evm(main, abstract)
            abstract = self.clear_abstract_evm(abstract)
        return tool, size, pc, os, abstract

    def find_regnumber(self, content):
        """Finds a registration number in the content."""

        if content is not None:
            return content.find('a', {'title': 'Ссылка на реестр (открывается в отдельном окне)'}).text
        return ''

    def find_regdate(self, content):
        """Finds a registration date in the content."""

        try:
            tmp = content.find_all('td')[0].find_all('p')[1].find('b').text
            return tmp
        except (IndexError, AttributeError):
            return ''

    def find_pubdate(self, content):
        """Finds a publication date in the content."""

        try:
            tmp = content.find_all('td')[0].find_all('p')[3].find('b').text
            return tmp
        except (IndexError, AttributeError):
            return ''

    def find_application(self, content):
        """Finds an application date and application number in the content."""

        appdata_pattern = re.compile(r'([0-9]{5,})\s+([0-9]{2}\.[0-9]{2}\.[0-9]{4})', flags=re.M)
        appdata = appdata_pattern.findall(content.text)
        res = ['', '']
        if (len(appdata) == 1):
            res = list(appdata[0])
        return res

    def find_authors(self, content):
        """Finds authors in the content."""

        try:
            tmp = content.find('td', {'id': 'bibl'}) \
                .find_all('p')[0].find('b').text
        except (IndexError, AttributeError):
            tmp = ''
        return tmp

    def find_right_holders(self, content):
        """Finds right holders in the content."""

        try:
            tmp = content.find('td', {'id': 'bibl'}) \
                .find_all('p')[1].find('b').text \
                .replace('\n\t\t\t\t\t\t\t\t\t', '')
            return tmp
        except IndexError:
            return ''

    def find_title(self, content):
        """Finds a title in the content."""

        try:
            tmp = content.find_all('p', {'class': 'TitAbs'})[0] \
                .find('b').text
            return tmp
        except IndexError:
            return ''

    def find_abstract(self, content):
        """Finds an abstract in the content."""

        try:
            tmp = content.find_all('p', {'class': 'TitAbs'})[1] \
                .text.replace('\nРеферат:\n', '')
            return tmp
        except IndexError:
            return ''

    def find_pc_db(self, content):
        """Finds a PC information for a database in the content."""

        try:
            tmp = content.find_all('p', {'class': 'TitAbs'})[2] \
                .text.replace('\nТип реализующей ЭВМ: ', '')
            return tmp
        except IndexError:
            return ''

    def find_tool_db(self, content):
        """Finds a DB Tool information in the content."""

        try:
            tmp = content.find_all('p', {'class': 'TitAbs'})[3] \
                .text.replace('\nВид и версия системы управления базой данных: ', '')
            return tmp
        except IndexError:
            return ''

    def find_os_db(self, content):
        """Finds an OS information for a database in the content."""

        try:
            tmp = content.find_all('p', {'class': 'TitAbs'})[4] \
                .text.replace('\nВид и версия операционной системы: ', '')
            return tmp
        except IndexError:
            return ''

    def find_size_db(self, content):
        """Finds a volume information for a database in the content."""

        try:
            tmp = content.find_all('p', {'class': 'TitAbs'})[5] \
                .text.replace('\n\n\t\t\t\t\t\t\tОбъем базы данных:\n\t\t\t\t\t\t', '')
            return tmp
        except IndexError:
            return ''

    def find_tool_evm(self, content):
        """Finds a language information in the content."""

        try:
            tmp = content.find_all('p', {'class': 'TitAbs'})[2] \
                .text.replace('\nЯзык программирования: ', '')
            return tmp
        except IndexError:
            return ''

    def find_size_evm(self, content):
        """Finds a volume information for a computer program in the content."""

        try:
            tmp = content.find_all('p', {'class': 'TitAbs'})[3] \
                .text.replace('\n\n\t\t\t\t\t\t\tОбъем программы для ЭВМ:\n\t\t\t\t\t\t', '')
            return tmp
        except IndexError:
            return ''

    def find_os_evm(self, content, abstract):
        """Finds an OS information for a computer program in the content."""

        os_pattern = re.compile(r'ОС:\s+(.+)\.$', flags=re.M)
        os = os_pattern.findall(abstract)
        return os[0] if len(os) == 1 else ''

    def find_pc_evm(self, content, abstract):
        """Finds a PC information for a computer program in the content."""

        pc_pattern = re.compile(r'Тип ЭВМ:\s+(.+)\.\s*ОС:.+\.$', flags=re.M)
        pc = pc_pattern.findall(abstract)
        return pc[0] if len(pc) == 1 else ''

    def clear_abstract_evm(self, abstract):
        """Clear an abstract in the content."""

        return re.sub(r"\s*Тип ЭВМ:\s+(.+)\.\s*ОС:.+\.$", "", abstract)
