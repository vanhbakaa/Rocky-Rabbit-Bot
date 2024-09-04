## Recommendation before use

# Join the bot [here](https://t.me/rocky_rabbit_bot/play?startapp=frId6624523270)

# 🔥🔥 Use PYTHON 3.10 - 3.11.5 🔥🔥

## Features  
| Feature                                                     | Supported  |
|---------------------------------------------------------------|:----------------:|
| Multithreading                                                |        ✅        |
| Proxy binding to session                                      |        ✅        |
| Auto tap                                                      |        ✅        |
| Specify number of taps                                        |        ✅        |
| Auto do tasks                                                 |        ✅        |
| Claim daily combo                                             |        ✅        |
| Claim daily enigma                                            |        ✅        |
| Claim daily rewards                                           |        ✅        |
| Claim daily easter eggs                                       |        ✅        |
| Auto apply boosts                                             |        ✅        |
| Auto upgrade boosts                                           |        ✅        |
| Random sleep time between taps                                |        ✅        |
| Auto upgrade cards                                            |        ✅        |
| Auto init new account                                         |        ✅        |
| Support for tdata / pyrogram .session / telethon .session     |        ✅        |


## [Settings](https://github.com/vanhbakaa/Rocky-Rabbit-Bot/blob/main/.env-example)
| Settings | Description |
|----------------------------|:-------------------------------------------------------------------------------------------------------------:|
| **API_ID / API_HASH**      | Platform data from which to run the Telegram session (default - android)                                      |
| **AUTO_TAP**               | Automatically tapping (default: True)                                                                         |                                
| **TAP_COUNT**              | How many taps will be clicked (default: [50, 125])                                                            |
| **DELAY_BETWEEN_TAPS**     | Random delay between taps (default: [15, 20])                                                                 |
| **AUTO_BOOST**             | Auto apply boosts (turbo or full energy) (default: True)                                                      |
| **AUTO_UPGRADE_BOOST**     | Auto upgrade (multi-tap, max-energy, passive-income) (default: True)                                          |
| **MAX_ENERGY_BOOST_LVL**   | Max level to upgrade max-energy (default: 5)                                                                  |
| **MULTI_TAP_LVL**          | Max level to upgrade multi-tap (default: 5)                                                                   |
| **PASSIVE_INCOME_LVL**     | Max level to upgrade passive-income (default: 3)                                                              |
| **AUTO_TASK**              | Auto clear tasks (default: True)                                                                              |
| **AUTO_ENIGMA**            | Auto apply daily enigma (default: True)                                                                       |
| **AUTO_SUPERSET**          | Auto apply daily superset (default: True)                                                                     |
| **AUTO_EASTER**            | Auto apply daily easter eggs (default: True)                                                                  |
| **AUTO_UPGRADE_CARDS**     | Auto upgrade cards if possible and claim cards (default: True)                                                |
| **USE_PROXY_FROM_FILE**    | Whether to use a proxy from the bot/config/proxies.txt file (True / False)                                    |


## Quick Start 📚

To install libraries and run bot - open run.bat on Windows

## Prerequisites
Before you begin, make sure you have the following installed:
- [Python](https://www.python.org/downloads/) **version 3.10 - 3.11.5**

## Obtaining API Keys
1. Go to my.telegram.org and log in using your phone number.
2. Select "API development tools" and fill out the form to register a new application.
3. Record the API_ID and API_HASH provided after registering your application in the .env file.

## Installation
You can download the [**repository**](https://github.com/vanhbakaa/Rocky-Rabbit-Bot) by cloning it to your system and installing the necessary dependencies:
```shell
git clone https://github.com/vanhbakaa/Rocky-Rabbit-Bot.git
cd Rocky-Rabbit-Bot
```

Then you can do automatic installation by typing:

Windows:
```shell
run.bat
```

Linux:
```shell
run.sh
```

# Linux manual installation
```shell
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
cp .env-example .env
nano .env  # Here you must specify your API_ID and API_HASH, the rest is taken by default
python3 main.py
```

You can also use arguments for quick start, for example:
```shell
~/Rocky-Rabbit-Bot >>> python3 main.py --action (1/2)
# Or
~/Rocky-Rabbit-Bot >>> python3 main.py -a (1/2)

# 1 - Run clicker
# 2 - Creates a session
```

# Windows manual installation
```shell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env-example .env
# Here you must specify your API_ID and API_HASH, the rest is taken by default
python main.py
```

You can also use arguments for quick start, for example:
```shell
~/Rocky-Rabbit-Bot >>> python main.py --action (1/2)
# Or
~/Rocky-Rabbit-Bot >>> python main.py -a (1/2)

# 1 - Run clicker
# 2 - Creates a session
```
### Contacts

For support or questions, you can contact me [![Static Badge](https://img.shields.io/badge/Telegram-Channel-Link?style=for-the-badge&logo=Telegram&logoColor=white&logoSize=auto&color=blue)](https://t.me/airdrop_tool_vanh)
