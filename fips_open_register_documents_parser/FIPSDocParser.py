# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup
import re


class FIPSDocParser:

    def __init__(self):
        self.__html_data = None
        self.__soup = None
        self.__main = None
        self.__bib = None
        self.parsed = None

    @property
    def soup(self):
        return self.__soup

    @property
    def main(self):
        return self.__main

    @property
    def bib(self):
        return self.__bib

    @property
    def html_data(self):
        return self.__html_data

    @html_data.setter
    def html_data(self, value):
        self.__html_data = str(value)
        self.__soup = BeautifulSoup(self.__html_data, 'html.parser')
        self.__main = self.soup.find('div', {'id': 'main'})
        self.__bib = self.soup.find('table', {'id': 'bib'})
        self.parsed = {}

    def parse(self):
        raise NotImplementedError()


class FIPSDocPatentParser(FIPSDocParser):

    def parse(self):
        self.parsed['status'] = self.find_status()
        self.parsed['application'] = self.find_application()
        self.parsed['reg_number'] = self.find_regnumber()
        self.parsed['reg_date'] = self.find_regdate()
        self.parsed['authors'] = self.find_authors()
        self.parsed['holders'] = self.find_holders()
        self.parsed['title'] = self.find_title()
        self.parsed['prior'] = self.find_prior()

    def find_status(self):
        status = re.search(r"<td id=\"StatusR\">(.+)(\n|<br)", self.html_data)
        return status.group(1) if status is not None else ''

    def find_application(self):
        app_data = re.search(r"\(21\)\s*\(22\)\s*Заявка:\s*<b><a\s.+\">(.+)<\/a>, (\d{1,2}\.\d{1,2}\.\d{4})<\/b>",
                             self.html_data)
        return {'number': app_data.group(1) if app_data is not None else '',
                'date': app_data.group(2) if app_data is not None else ''}

    def find_regnumber(self):
        data = re.search(r"<a title=\"Ссылка на реестр.+DocNumber=(\d+)&amp;TypeFile=html", self.html_data)
        return data.group(1) if data is not None else ''

    def find_regdate(self):
        data = re.search(r"<p>Дата регистрации:<br>\n<b>(.+)</b>", self.html_data)
        return data.group(1) if data is not None else ''

    def find_authors(self):
        data = re.search(r"<p>\(72\) Автор\(ы\):<b>\n(?:<br>)?(.+)</b>", self.html_data)
        return data.group(1) if data is not None else ''

    def find_holders(self):
        data = re.search(r"<p>\(73\) Патентообладатель\(и\):<b>\n(?:<br>)?(.+)</b>", self.html_data)
        return data.group(1) if data is not None else ''

    def find_title(self):
        data = re.search(r"\(54\) <b>(.+)<\/b>", self.html_data)
        return data.group(1) if data is not None else ''

    def find_aprior(self):
        data = re.search(r"<p class=\"prior\">Приоритет\(ы\):<\/p>\n<p>\n\t+\(22\) Дата подачи заявки: <b>(.+)</b>",
                         self.html_data)
        return data.group(1) if data is not None else ''

    def find_kprior(self):
        data = re.search(r"<p class=\"prior\">Приоритет\(ы\):<\/p>\n<p>\n\t+\(30\) Конвенционный приоритет:<b>;<br>(\d\{2}.\d{2}\.\d{2,4})",
                         self.html_data)
        return data.group(1) if data is not None else ''

    def find_dprior(self):
        data = re.search(r"\(24\) Дата начала отсчета срока действия патента:\s*<br>\n<b>(.+)<\/b>",
                         self.html_data)
        return data.group(1) if data is not None else ''

    def find_prior(self):
        aprior = self.find_aprior()
        kprior = self.find_kprior()
        dprior = self.find_dprior()
        return aprior if aprior is not '' else dprior if dprior is not '' else kprior


class FIPSDocEVMDBParser(FIPSDocParser):

    def parse(self):
        self.parsed['reg_number'] = self.find_regnumber(self.bib)  # registration number
        self.parsed['reg_date'] = self.find_regdate(self.bib)  # registration date
        self.parsed['pub_date'] = self.find_pubdate(self.bib)  # publication date
        app_data = self.find_application(self.bib)  # application data
        self.parsed['app_number'] = app_data[0]  # application number
        self.parsed['app_date'] = app_data[1]  # application date
        self.parsed['title'] = self.find_title(self.main)  # title
        self.parsed['title_new'] = self.find_title_new(self.soup)  # title new
        self.parsed['authors'] = self.find_authors(self.bib)  # authors
        self.parsed['holders'] = self.find_right_holders(self.bib)  # right holders
        self.parsed['holders_new'] = self.find_right_holders_new(self.soup)  # right holders new
        self.parsed['abstract'] = self.find_abstract(self.main)  # abstract
        self.parsed['tool'] = self.find_tool(self.main.text) if self.main is not None else ''
        self.parsed['size'] = self.find_size(self.main.text) if self.main is not None else ''

    @staticmethod
    def find_tool(content):
        return ''

    @staticmethod
    def find_size(content):
        return ''

    @staticmethod
    def find_regnumber(content):
        """Номер регистрации."""

        if content is not None:
            return content.find('a', {'title': 'Ссылка на реестр (открывается в отдельном окне)'}).text
        return ''

    @staticmethod
    def find_regdate(content):
        """Дата регистрации."""

        try:
            tmp = content.find_all('td')[0].find_all('p')[1].find('b').text
            return tmp
        except (IndexError, AttributeError):
            return ''

    @staticmethod
    def find_pubdate(content):
        """Дата публикации."""

        try:
            tmp = content.find_all('td')[0].find_all('p')[3].find('b').text
            return tmp
        except (IndexError, AttributeError):
            return ''

    @staticmethod
    def find_application(content):
        """Данные заявки."""

        res = ['', '']
        try:
            appdata_pattern = re.compile(r'([0-9]{5,})\s+([0-9]{2}\.[0-9]{2}\.[0-9]{4})', flags=re.M)
            appdata = appdata_pattern.findall(content.text)
            if len(appdata) == 1:
                res = list(appdata[0])
        except (IndexError, AttributeError):
            pass
        return res

    @staticmethod
    def find_authors(content):
        """Авторы."""

        try:
            tmp = content.find('td', {'id': 'bibl'}).find_all('p')
            return str(tmp[0].find('b').extract()).replace('<b>', '').replace('</b>', '') \
                if len(tmp) == 2 else ''
        except (IndexError, AttributeError):
            return ''

    @staticmethod
    def find_right_holders(content):
        """Правообладатели."""

        try:
            tmp = content.find('td', {'id': 'bibl'}).find_all('p')
            holders = str(tmp[1].find('b').extract()).replace('<b>', '').replace('</b>', '') \
                if len(tmp) == 2 else str(tmp[0].find('b').extract()).replace('<b>', '').replace('</b>', '')
            return holders.replace('\n\t\t\t\t\t\t\t\t\t', '')
        except (IndexError, AttributeError):
            return ''

    @staticmethod
    def find_right_holders_new(content):
        """Правообладатели, которые указаны в извещении (последние данные)."""

        try:
            # Учитываем вхождение слова "правообладатель" в любых вариантах
            data = content.find_all('p', {'class': 'izv'},
                                   text=re.compile(".*правообладатель.*",
                                                   flags=re.IGNORECASE))[-1]
            data = data.next_element.next_element.next_element
            if re.match(r'следует\s+читать', data.get_text(), re.IGNORECASE) is not None:
                data = data.next_element.next_element.next_element
            return data.get_text()
        except (IndexError, AttributeError):
            return ''

    @staticmethod
    def find_title(content):
        """Название ОИС."""

        try:
            tmp = content.find_all('p', {'class': 'TitAbs'})[0] \
                .find('b').text
            return tmp
        except (IndexError, AttributeError):
            return ''

    @staticmethod
    def find_title_new(content):
        """Новое название ОИС, которое указано в извещении (последние данные)."""

        try:
            # Учитываем вхождение слова "правообладатель" в любых вариантах
            data = content.find_all('p', {'class': 'izv'},
                                   text=re.compile(".*название (базы данных|программы для ).*",
                                                   flags=re.IGNORECASE))[-1]
            data = data.next_element.next_element.next_element
            if re.match(r'следует\s+читать', data.get_text(), re.IGNORECASE) is not None:
                data = data.next_element.next_element.next_element
            return data.get_text()
        except (IndexError, AttributeError):
            return ''

    # <p class="izv">Изменения в поле: Название базы данных:</p>

    @staticmethod
    def find_abstract(content):
        """Находит реферат."""

        try:
            tmp = content.find_all('p', {'class': 'TitAbs'})[1] \
                .text.replace('\nРеферат:\n', '')
            return tmp
        except (IndexError, AttributeError):
            return ''


class FIPSDocEVMParser(FIPSDocEVMDBParser):
    """Парсер свидетельства о регистрации ПрЭВМ."""

    @staticmethod
    def find_tool(content):
        """Язык программирования."""

        pattern = re.compile(r'Язык программирования:[\s\n\t]*([^\t].+)$', flags=re.M)
        data = pattern.findall(content)
        return data[0] if len(data) == 1 else ''

    @staticmethod
    def find_size(content):
        """Объём ПрЭВМ."""

        pattern = re.compile(r'Объем программы для ЭВМ:[\s\n\t]*([^\t].+)$', flags=re.M)
        data = pattern.findall(content)
        return data[0] if len(data) == 1 else ''


class FIPSDocDBParser(FIPSDocEVMDBParser):
    """Парсер свидетельства о регистрации БД."""

    @staticmethod
    def find_tool(content):
        """Вид и версия СУБД."""

        pattern = re.compile(r'Вид и версия системы управления базой данных:\s+(.+)$', flags=re.M)
        tool = pattern.findall(content)
        return tool[0] if len(tool) == 1 else ''

    @staticmethod
    def find_size(content):
        """Размер БД."""

        pattern = re.compile(r'Объем базы данных:\n?\t+([^\t].+)$', flags=re.M)
        tool = pattern.findall(content)
        return tool[0] if len(tool) == 1 else ''


class FIPSDocTIMSParser(FIPSDocEVMDBParser):
    """Парсер свидетельства о регистрации ТИМС."""
    pass
