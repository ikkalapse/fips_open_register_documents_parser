# -*- coding: utf-8 -*-
import re


class FIPSDocParser:

    def __init__(self):
        self.__html_data = None
        self.parsed = None

    @property
    def html_data(self):
        return self.__html_data

    @html_data.setter
    def html_data(self, value):
        self.__html_data = re.sub(r"[\s\t]+", " ", re.sub(r"\n", "", str(value)))
        self.parsed = {}

    def parse(self):
        """
        Выполняет парсинг свидетельства/патента.
        автоматически вызывает все методы класса, которые начинаются с find_
        """
        for func in dir(self):
            f = getattr(self, func)
            if callable(f) and func.startswith("find_"):
                f()

    def find_reg_number(self):
        data = re.search(r"<a title=\"Ссылка на реестр \(открывается в отдельном окне\).+DocNumber=(.+?)&amp;TypeFile=html",
                         self.html_data)
        self.parsed['reg_number'] = data.group(1) if data is not None else ''

    def find_reg_date(self):
        data = re.search(r"<p>Дата регистрации:[\s\n\t]*(?:<br>)?[\s\n\t]*<b>(\d{2}\.\d{2}\.\d{4})</b>", self.html_data)
        self.parsed['reg_date'] = data.group(1) if data is not None else ''


class FIPSDocPatentParser(FIPSDocParser):

    def find_status(self):
        status = re.search(r"<td id=\"StatusR\">(.+)(\n|<br)", self.html_data)
        self.parsed['status'] = status.group(1) if status is not None else ''

    def find_app_data(self):
        app_data = re.search(r"\(21\)\s*\(22\)\s*Заявка:\s*<b><a\s.+\">(.+)</a>,?[\s\n\t]*(\d{1,2}\.\d{1,2}\.\d{4})</b>",
                             self.html_data)
        self.parsed['app_number'] = app_data.group(1) if app_data is not None else ''
        self.parsed['app_date'] = app_data.group(2) if app_data is not None else ''

    def find_pub_date(self):
        data = re.search(r"<p>(?:\(45\))?\s*Опубликовано:\s*(?:<br>)?[\s\n\t]*<b>(?:<a title=.+target=\"_blank\">)(\d{1,2}\.\d{1,2}\.\d{4})(?:</a>)?</b>", self.html_data)
        self.parsed['pub_date'] = data.group(1) if data is not None else ''

    def find_authors(self):
        data = re.search(r"<p>\(72\) Автор\(ы\):<b>[\s\n\t](?:<br>)?(.+?)</b>", self.html_data)
        self.parsed['authors'] = data.group(1) if data is not None else ''

    def find_holders(self):
        data = re.search(r"<p>\(73\) Патентообладатель\(и\):<b>[\s\n\t]*(?:<br>)?(.+?)</b>", self.html_data)
        self.parsed['holders'] = data.group(1) if data is not None else ''

    def find_title(self):
        data = re.search(r"\(54\) <b>(.+?)</b>", self.html_data)
        self.parsed['title'] = data.group(1) if data is not None else ''

    def find_prior_app(self):
        data = re.search(r"<p class=\"prior\">Приоритет\(ы\):</p>[\s\n\t]*<p>[\s\n\t]*\(22\) Дата подачи заявки: <b>(.+?)</b>",
                         self.html_data)
        self.parsed['prior_app'] = data.group(1) if data is not None else ''

    def find_prior_conv(self):
        data = re.search(r"<p class=\"prior\">Приоритет\(ы\):</p>[\s\n\t]*<p>[\s\n\t]*\(30\) Конвенционный приоритет:<b>;<br>(\d\{2}.\d{2}\.\d{2,4})",
                         self.html_data)
        self.parsed['prior_conv'] = data.group(1) if data is not None else ''

    def find_start_date(self):
        data = re.search(r"\(24\) Дата начала отсчета срока действия патента:\s*<br>\n<b>(.+?)<\/b>",
                         self.html_data)
        self.parsed['start_date'] = data.group(1) if data is not None else ''


class FIPSDocEVMDBParser(FIPSDocParser):

    def find_pub_date(self):
        data = re.search(r"<p>Дата публикации:[\s\n\t]*<b>(?:<a.+target=\"_blank\">)?(.+?)(?:</a>)?</b>",
                         self.html_data)
        self.parsed['pub_date'] = data.group(1) if data is not None else ''

    def find_app_data(self):
        app_data = re.search(r"<p>Номер и дата поступления заявки:<br>[\s\n\t]*<b>(.+?) (.+?)</b>",
                             self.html_data)
        self.parsed['app_number'] = app_data.group(1) if app_data is not None else ''
        self.parsed['app_date'] = app_data.group(2) if app_data is not None else ''

    def find_authors(self):
        data = re.search(r"<p>[\s\n\t]*Автор(?:ы)?:[\s\n\t]*<br>[\s\n\t]*<b>(.+?)</b>", self.html_data)
        self.parsed['authors'] = data.group(1) if data is not None else ''

    def find_holders(self):
        data = re.search(r"<p>[\s\n]*Правообладател(?:и|ь):[\s\n]*<br>[\s\n]*<b>(.+?)</b>",
                         self.html_data)
        self.parsed['holders'] = data.group(1) if data is not None else ''

    def find_abstract(self):
        data = re.search(r"<p class=\"TitAbs\">[\s\n\t]*(?:<b>)?Реферат:(?:</b>)?[\s\n\t]*<br>(.+?)</p>",
                         self.html_data)
        self.parsed['abstract'] = data.group(1) if data is not None else ''

    def find_holders_new(self):
        """Правообладатели, которые указаны в извещении (последние данные)."""

        '''try:
            # Учитываем вхождение слова "правообладатель" в любых вариантах
            data = content.find_all('p', {'class': 'izv'},
                                   text=re.compile(".*правообладатель.*",
                                                   flags=re.IGNORECASE))[-1]
            data = data.next_element.next_element.next_element
            if re.match(r'следует\s+читать', data.get_text(), re.IGNORECASE) is not None:
                data = data.next_element.next_element.next_element
            return data.get_text()
        except (IndexError, AttributeError):
            return '''''
        return ''

    def find_title(self):
        data = re.search(r"<p class=\"TitAbs\">[\s\n\t]*Название.+:[\s\n\t]*<br>[\s\n\t]*<b>(.+?)</b>", self.html_data)
        self.parsed['title'] = data.group(1) if data is not None else ''

    def find_title_new(self):

        '''try:
            # Учитываем вхождение слова "правообладатель" в любых вариантах
            data = content.find_all('p', {'class': 'izv'},
                                   text=re.compile(".*название (базы данных|программы для ).*",
                                                   flags=re.IGNORECASE))[-1]
            data = data.next_element.next_element.next_element
            if re.match(r'следует\s+читать', data.get_text(), re.IGNORECASE) is not None:
                data = data.next_element.next_element.next_element
            return data.get_text()
        except (IndexError, AttributeError):
            return '''''
        return ''


class FIPSDocEVMParser(FIPSDocEVMDBParser):
    """Парсер свидетельства о регистрации ПрЭВМ."""

    def find_tool(self):
        data = re.match(r"<p class=\"TitAbs\">[\s\n]*<b>[\s\n]*Язык программирования:[\s\n]*</b>[\s\n]*(.+?)</p>",
                        self.html_data)
        self.parsed['tool'] = data.group(1) if data is not None else ''

    def find_size(self):
        data = re.match(r"<p class=\"TitAbs\">[\s\n]*<b>[\s\n]*Объ[её]м программы для ЭВМ:[\s\n]*</b>[\s\n]*(.+?)</p>",
                        self.html_data)
        self.parsed['size'] = data.group(1) if data is not None else ''


class FIPSDocDBParser(FIPSDocEVMDBParser):
    """Парсер свидетельства о регистрации БД."""

    def find_tool(self):
        data = re.match(r"<p class=\"TitAbs\">[\s\n]*<b>Вид и версия системы управления базой данных: </b>[\s\n\t]*(.+?)</p>",
                        self.html_data)
        self.parsed['tool'] = data.group(1) if data is not None else ''

    def find_size(self):
        data = re.match(r"<p class=\"TitAbs\">[\s\n\t]*<b>[\s\n\t]*Объ[её]м базы данных:[\s\n\t]*</b>[\s\n\t]*(.+?)</p>",
                        self.html_data)
        self.parsed['size'] = data.group(1) if data is not None else ''


class FIPSDocTIMSParser(FIPSDocEVMDBParser):
    """Парсер свидетельства о регистрации ТИМС."""
    pass
