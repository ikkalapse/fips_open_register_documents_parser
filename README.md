# fips_open_register_documents_parser

Библиотека выполняет синтаксический разбор HTML-кода патента на изобретение/полезную модель или свидетельства о регистрации базы данных (БД), программы для ЭВМ (ПрЭВМ), топологии интегральных микросхем (ТИМС) из Открытых реестров ФИПС (https://new.fips.ru/registers-web/). 


## Шаг 1 &mdash; импорт библиотеки и инициализация парсера (в зависимости от вида документа)  

Для разбора HTML-кода свидетельства о регистрации ПрЭВМ:  
`from fips_open_register_documents_parser.FIPSDocParser import FIPSDocEVMParser`  
`parser = FIPSDocEVMParser()`  

Для разбора HTML-кода свидетельства о регистрации БД:  
`from fips_open_register_documents_parser.FIPSDocParser import FIPSDocDBParser`  
`parser = FIPSDocDBParser()`  

Для разбора HTML-кода свидетельства о регистрации ТИМС:  
`from fips_open_register_documents_parser.FIPSDocParser import FIPSDocTIMSParser`  
`parser = FIPSDocTIMSParser()`  

Для разбора HTML-кода патента:  
`from fips_open_register_documents_parser.FIPSDocParser import FIPSDocPatentParser`  
`parser = FIPSDocPatentParser()`  


## Шаг 2 &mdash; передача HTML-кода патента/свидетельства в парсер  

Можно прочитать страницу патента/свидетельства с сайта ФИПС или предварительно скачать страницу и прочитать с локального файла.  
В парсер передаётся содержимое файла патента/свидетельства:  
`parser.html_data = ...`

## Шаг 3 &mdash; синтаксический разбор HTML-кода  

`parser.parse()`

## Шаг 4 &mdash; получение извлечённых из патента/свидетельства данных

`parser.parsed` &mdash; словарь с извлечёнными данными. 


