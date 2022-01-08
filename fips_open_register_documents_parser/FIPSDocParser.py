import re


class DocumentNotExistsInOpenRegistry(Exception):
    pass


class FIPSDocParser:

    def __init__(self):
        self.__html_data = None
        self.parsed = None

    @property
    def html_data(self):
        return self.__html_data

    @html_data.setter
    def html_data(self, value):
        """
        Выполняет очистку HTML-документа от лишних знаков и
        выбрасывает исключение DocumentNotExistsInOpenRegistry в случае,
        если документ содержит указание на отсутствие документа в Реестре ФИПС.
        """

        value = str(value)
        value = re.sub(r"\t+", " ", value)
        value = re.sub(r"\r?\n+\s+", "", value)
        self.__html_data = value
        self.parsed = {}
        if re.search(r'Документ с данным номером отсутствует', self.__html_data) is not None:
            raise DocumentNotExistsInOpenRegistry()

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
        """Номер регистрации."""

        data = re.search(
            r"<a title=\"Ссылка на реестр \(открывается в отдельном окне\).+DocNumber=(.+?)&amp;TypeFile=html",
            self.html_data)
        self.parsed['reg_number'] = data.group(1) if data is not None else ''

    def find_reg_date(self):
        """Дата регистрации."""

        data = re.search(r"<p>Дата регистрации:[\s\n\t]*(?:<br>)?[\s\n\t]*<b>(\d{2}\.\d{2}\.\d{4})</b>", self.html_data)
        self.parsed['reg_date'] = data.group(1) if data is not None else ''


class FIPSDocPatentParser(FIPSDocParser):

    def find_status(self):
        """Статус патента."""

        status = re.search(r"<td id=\"StatusR\">(.+)(\n|<br)", self.html_data)
        self.parsed['status'] = status.group(1) if status is not None else ''

    def find_app_data(self):
        """Данные заявки на выдачу патента."""

        app_data = re.search(
            r"\(21\)\s*\(22\)\s*Заявка:\s*<b><a\s.+\">(.+)</a>,?[\s\n\t]*(\d{1,2}\.\d{1,2}\.\d{4})</b>",
            self.html_data)
        self.parsed['app_number'] = app_data.group(1) if app_data is not None else ''
        self.parsed['app_date'] = app_data.group(2) if app_data is not None else ''

    def find_pub_date(self):
        """Дата публикации."""

        data = re.search(
            r"<p>(?:\(45\))?\s*Опубликовано:\s*(?:<br>)?[\s\n\t]*<b>(?:<a title=.+target=\"_blank\">)(\d{1,2}\.\d{1,"
            r"2}\.\d{4})(?:</a>)?</b>",
            self.html_data)
        self.parsed['pub_date'] = data.group(1) if data is not None else ''

    def find_authors(self):
        """Авторы изобретения/полезной модели."""

        data = re.search(r"<p>\(72\) Автор\(ы\):<b>[\s\n\t](?:<br>)?(.+?)</b>", self.html_data)
        self.parsed['authors'] = data.group(1) if data is not None else ''

    def find_holders(self):
        """Патентообладатели."""

        data = re.search(r"<p>\(73\) Патентообладатель\(и\):<b>[\s\n\t]*(?:<br>)?(.+?)</b>", self.html_data)
        self.parsed['holders'] = data.group(1) if data is not None else ''

    def find_title(self):
        """Навзание изобретения/полезной модели."""

        data = re.search(r"\(54\) <b>(.+?)</b>", self.html_data)
        self.parsed['title'] = data.group(1) if data is not None else ''

    def find_prior_app(self):
        """Приоритет (дата подачи заявки)."""

        data = re.search(
            r"<p class=\"prior\">Приоритет\(ы\):</p>[\s\n\t]*<p>[\s\n\t]*\(22\) Дата подачи заявки: <b>(.+?)</b>",
            self.html_data)
        self.parsed['prior_app'] = data.group(1) if data is not None else ''

    def find_prior_conv(self):
        """Конвенционный приоритет."""

        data = re.search(
            r"<p class=\"prior\">Приоритет\(ы\):</p>[\s\n\t]*<p>[\s\n\t]*\(30\) Конвенционный приоритет:<b>;<br>(\d\{"
            r"2}.\d{2}\.\d{2,4})",
            self.html_data)
        self.parsed['prior_conv'] = data.group(1) if data is not None else ''

    def find_start_date(self):
        """Дата начала срока действия патента."""

        data = re.search(r"\(24\) Дата начала отсчета срока действия патента:\s*<br>\n<b>(.+?)<\/b>",
                         self.html_data)
        self.parsed['start_date'] = data.group(1) if data is not None else ''


class FIPSDocEVMDBParser(FIPSDocParser):

    def find_pub_date(self):
        """Дата публикации сведений об ОИС."""

        data = re.search(r"<p>Дата публикации:[\s\n\t]*<b>(?:<a.+target=\"_blank\">)?(.+?)(?:</a>)?</b>",
                         self.html_data)
        self.parsed['pub_date'] = data.group(1) if data is not None else ''

    def find_app_data(self):
        """Данные заявки на регистрацию ОИС."""

        app_data = re.search(r"<p>Номер и дата поступления заявки:<br>[\s\n\t]*<b>(.+?) (.+?)</b>",
                             self.html_data)
        self.parsed['app_number'] = app_data.group(1) if app_data is not None else ''
        self.parsed['app_date'] = app_data.group(2) if app_data is not None else ''

    def find_authors(self):
        """Авторы ОИС."""

        data = re.search(r"<p>[\s\n\t]*Автор(?:ы)?:[\s\n\t]*<br>[\s\n\t]*<b>(.+?)</b>", self.html_data)
        self.parsed['authors'] = data.group(1) if data is not None else ''

    def find_holders(self):
        """Правообладатели ОИС."""

        data = re.search(r"<p>[\s\n]*Правообладател(?:и|ь):[\s\n]*<br>[\s\n]*<b>(.+?)</b>",
                         self.html_data)
        self.parsed['holders'] = data.group(1) if data is not None else ''

    def find_abstract(self):
        data = re.search(r"<p class=\"TitAbs\">[\s\n\t]*(?:<b>)?Реферат:(?:</b>)?[\s\n\t]*<br>(.+?)</p>",
                         self.html_data)
        self.parsed['abstract'] = data.group(1) if data is not None else ''

    def find_holders_new(self):
        """Правообладатели, которые указаны в извещениях."""

        data = re.findall(r"<p class=\"izv\">.*?правообладател[ьи].*</p>\n?(?:<p class=\"izv2\">Следует "
                          r"читать:</p>\n?)?<p class=\"izvValue\">(.+?)</p>",
                          self.html_data, flags=re.IGNORECASE)
        self.parsed['holders_izv'] = data

    def find_title(self):
        """Название ОИС."""

        data = re.search(r"<p class=\"TitAbs\">[\s\n\t]*Название.+:[\s\n\t]*<br>[\s\n\t]*<b>(.+?)</b>", self.html_data)
        self.parsed['title'] = data.group(1) if data is not None else ''

    def find_title_new(self):
        """Новые названия ОИС, указанные в извещениях."""

        data = re.findall(r"<p class=\"izv\">.*?название (?:базы данных|программы для ).*</p>\n?(?:<p "
                          r"class=\"izv\d*\">Следует "
                          r"читать:</p>\n?)?<p class=\"izvValue\">(.+?)</p>",
                          self.html_data, flags=re.IGNORECASE)
        self.parsed['title_izv'] = data


class FIPSDocEVMParser(FIPSDocEVMDBParser):
    """Парсер свидетельства о регистрации ПрЭВМ."""

    def find_tool(self):
        data = re.search(r"<b>Язык программирования:[\n\s]*</b>[\n\s]*(.+?)</p>", self.html_data)
        self.parsed['tool'] = data.group(1) if data is not None else ''

    def find_size(self):
        data = re.search(r"<b>Объ[её]м программы для ЭВМ:[\n\s]*</b>[\n\s]*(.+?)</p>",
                         self.html_data)
        self.parsed['size'] = data.group(1) if data is not None else ''


class FIPSDocDBParser(FIPSDocEVMDBParser):
    """Парсер свидетельства о регистрации БД."""

    def find_tool(self):
        data = re.search(r"<b>Вид и версия системы управления базой данных:[\n\s]*</b>[\n\s]*(.+?)</p>",
                         self.html_data)

        self.parsed['tool'] = data.group(1) if data is not None else ''

    def find_size(self):
        data = re.search(r"<b>Объ[её]м базы данных:[\n\s]*</b>[\n\s]*(.+?)</p>",
                         self.html_data)
        self.parsed['size'] = data.group(1) if data is not None else ''


class FIPSDocTIMSParser(FIPSDocEVMDBParser):
    """Парсер свидетельства о регистрации ТИМС."""
    pass
