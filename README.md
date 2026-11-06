# depgraph — визуализатор графа зависимостей (вариант 17, pip)

## Общее описание

Консольный инструмент для анализа зависимостей Python-пакетов (формат
pip). Конечная цель работы — построить граф зависимостей пакета и
вывести его на языке PlantUML. Готовые менеджеры пакетов и библиотеки
для получения зависимостей не используются.

**Реализован этап 1**: консольное приложение, настройка через
YAML-файл, проверка всех параметров.

## Параметры конфигурации (YAML)

| Параметр       | Обязателен | Описание                                             |
|----------------|------------|------------------------------------------------------|
| `package_name` | да         | имя анализируемого пакета                            |
| `repository`   | да         | URL репозитория или путь к файлу тестового репозитория |
| `test_mode`    | нет        | `true` — `repository` это файл; по умолчанию `false`  |
| `filter`       | нет        | подстрока для фильтрации пакетов; по умолчанию пусто  |

Пример `config.yaml`:

```yaml
package_name: requests
repository: https://pypi.org/pypi
test_mode: false
filter: ""
```

Ошибки проверяются для каждого параметра (пустое или некорректное имя,
не-URL, отсутствующий файл тестового репозитория, неверный тип
`test_mode` и `filter`, неизвестные параметры, повреждённый YAML,
отсутствующий файл). Все найденные проблемы выводятся сразу, код
возврата 1.

## Установка, запуск и тесты

Нужен Python 3.8+.

```
pip install -r requirements.txt
run.bat --config config.yaml
python -m unittest discover -v
scripts\demo_stage1.bat
```

`--config PATH` — путь к YAML (по умолчанию `config.yaml`).
`scripts\demo_stage1.bat` прогоняет корректные и некорректные
конфигурации из папки `configs`.

## Пример

```
> run.bat --config configs\remote.yaml
package_name: flask
repository: https://pypi.org/pypi
test_mode: false
filter: werk

> run.bat --config configs\errors\all_wrong.yaml
error: package_name: must not be empty
error: repository: 'ftp://x' is not an http(s) URL (use test_mode: true ...)
error: test_mode: must be true or false, got 5
error: filter: must be a string, got [1]
```
