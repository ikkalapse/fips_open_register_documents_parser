import re
from operator import itemgetter


class DocumentNotExistsInOpenRegistry(Exception):
    pass


class FIPSDocParser:

    def __init__(self):
        self.__html_data = None
        self.__html_data_min = None
        self.parsed = None

    @property
    def html_data(self):
        return self.__html_data

    @property
    def html_data_min(self):
        return self.__html_data_min

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
        self.__html_data_min = "".join(self.html_data.split("\n"))
        self.parsed = {}
        # print(self.html_data)
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

        status = re.search(r"<td id=\"StatusR\">(.+?)(\(|\n|<br)", self.html_data)
        self.parsed['status'] = status.group(1) if status is not None else ''

    def find_app_data(self):
        """Данные заявки на выдачу патента."""

        app_data = re.search(
            r"\(21\)\s*\(22\)\s*Заявка:\s*<b><a\s.+\">(.+?)</a>,?[\s\n\t]*(.+?)</b>",
            self.html_data)
        self.parsed['app_number'] = app_data.group(1) if app_data is not None else ''
        self.parsed['app_date'] = app_data.group(2) if app_data is not None else ''

    def find_pub_date(self):
        """Дата публикации."""

        #<p>(45) Опубликовано:
		#							<b>10.08.2000</b>
		#										Бюл. № <b>22</b>
        data = re.search(
            r"<p>(?:\(45\))?\s*Опубликовано:\s*(?:<br>)?[\s\n\t]*<b>(?:<a title=\WОфициальная "
            r"публикация.+?target=\"_blank\">)?([\d\.]{10}?)(?:</a>)?",
            self.html_data)
        self.parsed['pub_date'] = data.group(1) if data is not None else ''

    def find_authors(self):
        """Авторы изобретения/полезной модели."""

        data = re.search(r"<p>\(72\) Автор\(ы\):<b>[\s\n\t]*(?:<br>)?(.+?)</b>", self.html_data)
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

        data = re.search(r"<p class=\"prior\">Приоритет\(ы\):</p>[\s\n\t]*<p>[\s\n\t]*\(30\) Конвенционный "
                         r"приоритет:(?:.*?)?<br>(.+?)</b>",
                         self.html_data)
        self.parsed['prior_conv'] = data.group(1) if data is not None else ''

    def find_start_date(self):
        """Дата начала срока действия патента."""

        data = re.search(r"\(24\) Дата начала отсчета срока действия патента:\s*<br>\n<b>(.+?)<\/b>",
                         self.html_data)
        self.parsed['start_date'] = data.group(1) if data is not None else ''

    def find_izv(self):
        """Извещения об изменениях в патенте."""

        r = re.compile(r"<p class=\"NameIzv\">"
                       r"(?P<full_name>(?:(?P<code>[A-Z\d]{4}?) (?:\- )?)?(?P<name>.+?))</p>"
                       r"(<p class=\"izv2\"></p>)?"
                       r"(?P<text>.+?)"  # текст извещения до даты внесения записи в Госреестр
                       r"<p class=\"izv\">(?:Дата публикации|Извещение опубликовано|Дата публикации и номер бюллетеня): <b>.*?"
                       r"(?P<pub_date>\d{2}\.\d{2}\.\d{4}?)</[a-z]>",
                       flags=re.IGNORECASE)
        # Оставляем извещения, связанные с изменением данных о правообладателях и авторах
        codes = 'PD4A PC4A TK4A TC4A'.split()
        self.parsed['izv'] = [x for x in [m.groupdict() for m in r.finditer(self.html_data_min)] if x['code'] in codes]
        self.extract_izv()

    def extract_izv(self):
        """Извлечение имён новых авторов и/или патентообладателей."""

        for i, izv in enumerate(self.parsed['izv']):
            if izv['code'] == 'TK4A':
                data = re.search(r"<p class=\"izv\">Следует читать.+?"
                                 r"\(73\) Патентообладатель\(и\):\s*"
                                 r"<br>(?:<b>)?(.+?)(?:</ru-[a-z\d]+>|</b>|<br>)",
                                 izv['text'],
                                 flags=re.IGNORECASE)
                self.parsed['izv'][i]['holder'] = data.group(1) if data is not None else ''
                # проверка авторов -- соотвтствие шаблону 1
                data = re.search(r"<p class=\"izv\">Следует читать.+?"
                                 r"\(72\) Автор\(ы\):\s*"
                                 r"<br>(?:<b>)?(.+?)(?:</b>|<br>)",
                                 izv['text'],
                                 flags=re.IGNORECASE)
                self.parsed['izv'][i]['authors'] = data.group(1) if data is not None else ''
                # проверка авторов -- соответствие шаблону 2
                if self.parsed['izv'][i]['authors'] == '':
                    # пример:
                    # <p class="izv">Следует читать: <b><ru-b906i>(72) иванов, Петров, Сидоров</ru-b906i></b></p>
                    data = re.search(r"<p class=\"izv\">Следует читать.+?"
                                     r"(?:<b>)?(?:<ru\-[\da-z]+>)?"
                                     r"\(72\)\s*(?:<b>)?(.+?)(?:</ru\-[\da-z]+>)?(?:</b>|<br>|</p>)",
                                     izv['text'],
                                     flags=re.IGNORECASE)
                    self.parsed['izv'][i]['authors'] = data.group(1) if data is not None else ''

            if izv['code'] == 'TC4A':
                data = re.search(r"\(72\) Автор\(ы\):\s*"
                                 r"<br><b>(.+?)</b>",
                                 izv['text'],
                                 flags=re.IGNORECASE)
                self.parsed['izv'][i]['authors'] = data.group(1) if data is not None else ''
            '''
            <p class="NameIzv">PD4A - Изменение наименования обладателя патента Российской Федерации на изобретение</p>
            <p class="izv">
                                    (73) Новое наименование патентообладателя:
                                <br>
            <b>Открытое акционерное общество "Металлург" (RU)</b>
            </p>
            '''
            if izv['code'] == 'PD4A':
                data = re.search(r"\(73\) (?:Нов[а-яё]{2}\s+)?(?:\s*наименование\s+)?Патентообладател[ь|я](?:\(и\))?:<br><b>(.+?)</b>",
                                 izv['text'],
                                 flags=re.IGNORECASE)
                self.parsed['izv'][i]['holder'] = data.group(1) if data is not None else ''

            if izv['code'] == 'PC4A':
                data = re.search(r"\(73\) (?:Новый\s+)?Патентообладатель(?:\(и\))?:<br><b>(.+?)</b>",
                                 izv['text'],
                                 flags=re.IGNORECASE)
                self.parsed['izv'][i]['holder'] = data.group(1) if data is not None else ''
        self.parsed['izv'] = sorted(self.parsed['izv'], key=itemgetter('pub_date'), reverse=True)


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

    def find_authors_new(self):
        """Авторы, которые указаны в извещениях."""

        data = re.findall(r"<p class=\"izv\">.*?Автор[ы]?.*</p>\n?(?:<p class=\"izv2\">Следует "
                          r"читать:</p>\n?)?<p class=\"izvValue\">(.+?)</p>",
                          self.html_data, flags=re.IGNORECASE)
        self.parsed['authors_izv'] = data

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
