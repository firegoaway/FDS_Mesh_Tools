# FMT - FDS Mesh Tools

> Язык: **Python**

> Интерфейс: **Tkinter**

## Особенности и описание работы утилиты
Утилита позволяет взаимодействовать с расчетной областью, разбивать её на несколько мелких расчетных областей, увеличивать или уменьшать размер ячейки.

### Поддерживаемые версии FDS
> [**FDS 6.9.1**](https://github.com/firemodels/fds/releases/tag/FDS-6.9.1)
> [**FDS 6.9.0**](https://github.com/firemodels/fds/releases/tag/FDS-6.9.0)
> [**FDS 6.8.0**](https://github.com/firemodels/fds/releases/tag/FDS-6.8.0)

## Как установить и пользоваться

|	№ п/п	|	Действие	|
|---------|---------|
|	1	|	Скачайте последнюю версию **ZmejkaFDS** в разделе [**Releases**](https://github.com/firegoaway/Zmejka/releases)	|
|	2	|	Запустите **ZmejkaFDS.exe**. Нажмите **"Выбрать .fds"** и выберите файл сценария FDS	|
|	3	|	Для разбиения расчётной области во вкладке **"Параметры"** нажмите **"Partition"**. Откроется новое окно	|
|	4	|	В окне **FMT Partitioner** введине количество расчётных областей, которое вы хотите получить и нажмите **"Разбить"**	|
|	5	|	Для уменьшения или увеличения размера ячеек в одной или нескольких расчётных областях во вкладке **"Параметры"** нажмите **"Refine/Coarsen"**. Откроется новое окно	|
|	6	|	В окне **FMT Refiner-Coarsener** выберите одну или несколько расчётных областей из списка ниже, укажите значение **Csw** и нажмите **"Преобразовать"**	|
|	7	|	Готово! Файл сценария **.fds** готов к запуску	|

> **FMT** работает как самостоятельно, так и в связке с утилитой [**ZmejkaFDS**](https://github.com/firegoaway/Zmejka)

## Статус разработки
> **Альфа**

## Профилактика вирусов и угроз
- Утилиты **"FMT"** предоставляются **"как есть"**.
- Актуальная версия утилиты доступна в разделе [**Releases**](https://github.com/firegoaway/Fds_SURF_fix/releases), однако использовать утилиту в отрыве от [**ZmejkaFDS**](https://github.com/firegoaway/Zmejka) не рекомендуется.
- Файлы, каким-либо образом полученные не из текущего репозитория, несут потенциальную угрозу вашему ПК.
- Файл с расширением **.exe**, полученный из данного репозитория, имеет уникальную Хэш-сумму, позволяющую отличить оригинальную утилиту от подделки.
- Хэш-сумма обновляется только при обновлении версии утилиты и всегда доступна в конце файла **README.md**.

### Актуальные Хэш-суммы
> FMT Partitioner.exe - **70169f86c5b9dac5a29a431d41882242**

> FMT Refiner-Coarsener.exe - **40c7f61a46c483965361443f8a434735**
