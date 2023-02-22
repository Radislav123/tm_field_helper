# Генерация истории изменений

## Генератор истории изменений
Ссылка на библиотеку - [*auto-changelog*](https://github.com/KeNaCo/auto-changelog). Сгенерировать историю:

```shell
auto-changelog
```

Сгенерировать историю, включая коммиты без релиза

```shell
auto-changelog -u
```

## Установка версии

За установку версии генератором истории изменений отвечают [*git-теги*](https://git-scm.com/docs/git-tag). Проект содержит файл [*version.txt*](version.txt),
содержащий текущую версию. Чтобы установить тег версии, достаточно использовать [*update_version.py*](update_version.py):

```shell
python .\update_version.py
```

Удалить тег:

```shell
python .\update_version.py --remove
```

Посмотреть помощь по аргументам:

```shell
python .\update_version.py --help
```


Отправить тег в удаленный репозиторий ([*Stack Overflow*](https://stackoverflow.com/a/5195913/13186004)):

```shell
git push origin <tag_name>
git push origin 0.0.1
```


Отправить все теги в удаленный репозиторий:

```shell
git push --tags
```


# Генерация списка зависимостей
`pip freeze > .\requirements.txt`

## Использование списка зависимостей
`pip install -r .\requirements.txt`


# Настройка распознания
Предполагаемая структура расположения файлов для настройки:
```
└── resources
    └── tuning fields
        ├── field_0
        │   ├── image.PNG       # изображение стола
        │   └── mapping.txt     # соответствие стола типам ячеек
        ├── field_1
        ├── ...
        └── field_n
```

1) размер изображения может быть любым, но код проверялся на размере `324x324`
2) легенда `mapping.txt`
    1) `e` - `empty`
    2) `s` - `skull`
    3) `r` - `red`
    4) `g` - `green`
    5) `b` - `blue`

