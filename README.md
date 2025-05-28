# Devil Telegram Bot 😈

![Devil Bot Banner](https://i.pinimg.com/736x/7a/e8/00/7ae800f2ed32e454708c60476955ca4a.jpg)

**Simple yet effective moderator bot for Telegram, with reports, logs, profanity filter, and more :3**  
📲 Live bot: [@managrbot](https://t.me/managrbot)

---

## About Devil

Devil is a personal bot made for easy chat auto-moderation. It adds reporting functionality, profanity filtering (both English & Russian), logging to a private channel, spam detection, warning/mute escalation and much more!

---

## Features

- **Chat registration & admin setup**  
- **Profanity filter** (Russian & English via censure)  
- **Link**, **CAPS**, **spam**, **sticker** filters  
- **Keyword**-based warnings  
- **Reporting & logging** to a private channel  
- **Welcome messages** & **chat rules**  
- **Warnings**, **mutes**, **bans** with auto-escalation  
- **Read-only** mode toggle  
- **Reset warnings** per user or for all  

---

## Commands

| Command                                    | Description                               |
| ------------------------------------------ | ----------------------------------------- |
| `/start`                                   | Main menu & select chats to manage        |
| `/help`                                    | Show help message                         |
| `/rules`                                   | Display current chat rules                |
| `/setup`                                   | Register this chat for management         |
| `/ban [@user \| reply]`                    | Ban a user                                |
| `/unban [@user \| reply]`                  | Unban a user                              |
| `/mute [@user \| reply] [hours]`           | Mute a user for given hours               |
| `/unmute [@user \| reply]`                 | Unmute a user                             |
| `/checkperms [@user \| reply]`             | Check user’s permissions                  |
| `/ro`                                      | Toggle read-only mode                     |
| `/resetwarn [@user \| reply]`              | Reset warnings for a specific user        |
| `/resetwarnsall`                           | Reset all warnings in this chat           |

Interactive inline buttons in the “My Chats” menu let you toggle filters, set welcome messages, rules, logging, and more with one tap.

---

## Database

Uses PostgreSQL.

---

## Requirements

- Python 3.11  
- Dependencies listed in `requirements.txt`

---

## Contributing

Feel free to fork the repo and submit pull requests.  
Code is provided “as is” and can be freely extended or improved.

---

## License

Licensed under the Apache License, Version 2.0.  
© 2025 melroncod

---

# Devil Telegram Bot 😈

**Простой, но эффективный бот-модератор для Telegram с отчётами, логами, фильтром мата и многим другим :3**  
📲 Рабочий бот: [@managrbot](https://t.me/managrbot)

---

## О Devil

Devil — личный бот для простой и удобной автоматической модерации чатов.  
Поддерживает отчёты, фильтрацию нецензурной лексики (англ. и рус.), логирование в приватный канал, детектирование спама, эскалацию предупреждений/мутов и многое другое!

---

## Функционал

- **Регистрация чата и назначение админов**  
- **Фильтр мата** (русский и английский через censure)  
- **Фильтрация ссылок**, **капса**, **спама**, **стикеров**  
- **Ключевые слова** для предупреждений  
- **Отчёты и логирование** в приватный канал  
- **Приветственные сообщения** и **правила чата**  
- **Предупреждения**, **муты**, **баны** с авто-эскалацией  
- **Режим только для чтения**  
- **Сброс варнов** для пользователя или всех сразу  

---

## Команды

| Команда                                    | Описание                                 |
| ------------------------------------------ | ---------------------------------------- |
| `/start`                                   | Главное меню & выбор чатов для управления |
| `/help`                                    | Показать справку                          |
| `/rules`                                   | Показать правила чата                    |
| `/setup`                                   | Регистрация чата для управления          |
| `/ban [@user \| reply]`                    | Забанить пользователя                    |
| `/unban [@user \| reply]`                  | Разбанить пользователя                   |
| `/mute [@user \| reply] [часы]`            | Замутить пользователя на указанное время |
| `/unmute [@user \| reply]`                 | Размутить пользователя                   |
| `/checkperms [@user \| reply]`             | Проверить права пользователя             |
| `/ro`                                      | Вкл/выкл режим только для чтения         |
| `/resetwarn [@user \| reply]`              | Сбросить варны у пользователя            |
| `/resetwarnsall`                           | Сбросить все варны в чате                |

Интерактивное меню «Мои чаты» позволяет настраивать фильтры, приветствия, правила, логирование и др. одним нажатием.

---

## База данных

Используется PostgreSQL.

---

## Зависимости

- Python 3.11  
- Список зависимостей в `requirements.txt`

---

## Лицензия

Licensed under the Apache License, Version 2.0.  
© 2025 melroncod
