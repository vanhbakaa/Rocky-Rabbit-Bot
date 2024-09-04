import asyncio
import traceback
from time import time
from datetime import datetime, timedelta
from urllib.parse import unquote, quote

import aiohttp
from aiocfscrape import CloudflareScraper
from aiohttp_proxy import ProxyConnector
from better_proxy import Proxy
from pyrogram import Client
from pyrogram.errors import Unauthorized, UserDeactivated, AuthKeyUnregistered, FloodWait
from pyrogram.raw import functions
from pyrogram.raw.functions.messages import RequestWebView
from bot.core.agents import generate_random_user_agent
from bot.config import settings
import requests

from bot.utils import logger
from bot.exceptions import InvalidSession
from .headers import headers
from random import randint, uniform
import uuid

api_auth = "https://api.rockyrabbit.io/api/v1/account/start"
api_tap = "https://api.rockyrabbit.io/api/v1/clicker/tap"
api_boost = "https://api.rockyrabbit.io/api/v1/boosts"
api_boost_info = 'https://api.rockyrabbit.io/api/v1/boosts/list'
api_task_list = 'https://api.rockyrabbit.io/api/v1/task/list'
api_do_task = 'https://api.rockyrabbit.io/api/v1/task/upgrade'
api_sponsor = 'https://api.rockyrabbit.io/api/v1/account/sponsor'
api_daily = 'https://api.rockyrabbit.io/api/v1/mine/sync/daily'
api_play_combo = 'https://api.rockyrabbit.io/api/v1/mine/combo'
api_play_enigma = 'https://api.rockyrabbit.io/api/v1/mine/enigma'
api_play_easter = 'https://api.rockyrabbit.io/api/v1/mine/easter-eggs'
api_data = 'https://api.rockyrabbit.io/api/v1/config'
api_sync = 'https://api.rockyrabbit.io/api/v1/mine/sync'
api_ref = 'https://api.rockyrabbit.io/api/v1/account/referrals'
api_level = 'https://api.rockyrabbit.io/api/v1/account/level_current'
api_upgrade_card = 'https://api.rockyrabbit.io/api/v1/mine/upgrade'
api_init = "https://api.rockyrabbit.io/api/v1/account/init"


class Tapper:
    def __init__(self, tg_client: Client):
        self.tg_client = tg_client
        self.session_name = tg_client.name
        self.first_name = ''
        self.last_name = ''
        self.user_id = ''
        self.auth_token = ""
        self.available_taps = 100000000000000000000
        self.max_tap = 1000000000000000000000
        self.multi = 0
        self.boost_energy_lvl = 1
        self.boost_turbo_lvl = 1
        self.cool_down = 0
        self.cool_down_turbo = 0
        self.balance = 0
        self.boosts = None
        self.black_list = ['full-available-taps', 'turbo']
        self.superset = None
        self.enigma = None
        self.easter = None
        self.easter_expire = None
        self.superset_expire = None
        self.enigma_expire = None
        self.task_list = None
        self.daily_data = None
        self.cardsInfo = None
        self.mineCards = {}
        self.ref = 0
        self.user_level = 0
        self.new_account = False

    def get_user_level(self, auth_token):
        try:
            headers['Authorization'] = f'tma {auth_token}'
            # print(headers)
            response = requests.post(api_level, headers=headers)
            if response.status_code == 200:
                response_data = response.json()
                self.user_level = response_data['characters'][-1]['level']
            else:
                self.user_level = 0
        except Exception as e:
            traceback.print_exc()
            logger.error(f"{self.session_name} | <red>Unknown error while trying to get level info ...: {e}</red>")
    def get_ref(self, auth_token):
        try:
            headers['Authorization'] = f'tma {auth_token}'
            # print(headers)
            response = requests.post(api_ref, headers=headers)
            if response.status_code == 200:
                response_data = response.json()
                self.ref = response_data['totalReferrals']
            else:
                self.ref = 0
        except Exception as e:
            traceback.print_exc()
            logger.error(f"{self.session_name} | <red>Unknown error while trying to get referrals info ...: {e}</red>")
    def get_user_data(self, auth_token):
        try:
            headers['Authorization'] = f'tma {auth_token}'
            # print(headers)
            response = requests.post(api_auth, headers=headers)
            if response.status_code == 200:
                response_data = response.json()
                self.balance = response_data['clicker']['balance']

                logger.info(
                    f"{self.session_name} | <green>Logged in</green> - Balance: <yellow>{response_data['clicker']['balance']}</yellow> - Profit per hour: <yellow>{response_data['clicker']['earnPassivePerHour']}</yellow> - Total earned: <yellow>{response_data['clicker']['totalBalance']}</yellow>")

            else:
                print(response)
                logger.info(f"{self.session_name} | login failed... Response code: {response.status_code}")
        except Exception as e:
            traceback.print_exc()
            logger.error(f"{self.session_name} | <red>Unknown error while trying to get user data...: {e}</red>")

    async def get_tg_web_data(self, proxy: str | None) -> str:
        start_param = settings.REF_LINK.split("=")[1]
        # print(start_param)
        if proxy:
            proxy = Proxy.from_str(proxy)
            proxy_dict = dict(
                scheme=proxy.protocol,
                hostname=proxy.host,
                port=proxy.port,
                username=proxy.login,
                password=proxy.password
            )
        else:
            proxy_dict = None

        self.tg_client.proxy = proxy_dict

        try:
            if not self.tg_client.is_connected:
                try:
                    await self.tg_client.connect()
                    start_command_found = False
                    async for message in self.tg_client.get_chat_history('rocky_rabbit_bot'):
                        if (message.text and message.text.startswith('/start')) or (
                                message.caption and message.caption.startswith('/start')):
                            start_command_found = True
                            break
                    if not start_command_found:
                        self.new_account = True
                        peer = await self.tg_client.resolve_peer('rocky_rabbit_bot')
                        await self.tg_client.invoke(
                            functions.messages.StartBot(
                                bot=peer,
                                peer=peer,
                                start_param=start_param,
                                random_id=randint(1, 9999999)
                            )
                        )
                except (Unauthorized, UserDeactivated, AuthKeyUnregistered):
                    raise InvalidSession(self.session_name)

            while True:
                try:
                    peer = await self.tg_client.resolve_peer('rocky_rabbit_bot')
                    break
                except FloodWait as fl:
                    fls = fl.value

                    logger.warning(f"<light-yellow>{self.session_name}</light-yellow> | FloodWait {fl}")
                    logger.info(f"<light-yellow>{self.session_name}</light-yellow> | Sleep {fls}s")

                    await asyncio.sleep(fls + 3)

            web_view = await self.tg_client.invoke(RequestWebView(
                peer=peer,
                bot=peer,
                platform='android',
                from_bot_menu=False,
                url="https://play.rockyrabbit.io/",
            ))

            auth_url = web_view.url
            # print(auth_url)
            tg_web_data = unquote(
                string=unquote(string=auth_url.split('tgWebAppData=')[1].split('&tgWebAppVersion')[0]))
            query_id = tg_web_data.split('query_id=')[1].split('&user=')[0]
            user = quote(tg_web_data.split("&user=")[1].split('&auth_date=')[0])
            auth_date = tg_web_data.split('&auth_date=')[1].split('&hash=')[0]
            hash_ = tg_web_data.split('&hash=')[1]

            self.user_id = tg_web_data.split('"id":')[1].split(',"first_name"')[0]
            self.first_name = tg_web_data.split('"first_name":"')[1].split('","last_name"')[0]
            self.last_name = tg_web_data.split('"last_name":"')[1].split('","username"')[0]
            if self.tg_client.is_connected:
                await self.tg_client.disconnect()
            return f"query_id={query_id}&user={user}&auth_date={auth_date}&hash={hash_}"

        except InvalidSession as error:
            raise error

        except Exception as error:
            logger.error(f"<light-yellow>{self.session_name}</light-yellow> | Unknown error during Authorization: "
                         f"{error}")
            await asyncio.sleep(delay=3)


    async def check_proxy(self, http_client: aiohttp.ClientSession, proxy: Proxy) -> None:
        try:
            response = await http_client.get(url='https://httpbin.org/ip', timeout=aiohttp.ClientTimeout(5))
            ip = (await response.json()).get('origin')
            logger.info(f"{self.session_name} | Proxy IP: {ip}")
        except Exception as error:
            logger.error(f"{self.session_name} | Proxy: {proxy} | Error: {error}")

    def acount_init(self, auth_token):
        try:
            data = {"lang": "en", "sex": "male"}

            headers['Authorization'] = f'tma {auth_token}'
            # print(headers)
            response = requests.post(api_init, headers=headers, json=data)
            if response.status_code == 200:
                logger.info(
                    f"{self.session_name} | <green>Successfully set up account</green>")
                self.new_account = False
            else:
                print(response.json())
                logger.info(f"{self.session_name} | Set up account failed... Response code: {response.status_code}")
        except Exception as e:
            traceback.print_exc()
            logger.error(f"{self.session_name} | <red>Unknown error while trying to set up ...: {e}</red>")
    async def join_channel(self):
        try:
            logger.info(f"{self.session_name} | Joining TG channel...")
            if not self.tg_client.is_connected:
                try:
                    await self.tg_client.connect()
                except (Unauthorized, UserDeactivated, AuthKeyUnregistered):
                    raise InvalidSession(self.session_name)
            try:
                await self.tg_client.join_chat("rockyrabbitio")
                logger.success(f"{self.session_name} | <green>Joined channel successfully</green>")
            except Exception as e:
                logger.error(f"{self.session_name} | <red>Join TG channel failed - Error: {e}</red>")

        except Exception as error:
            logger.error(f"<light-yellow>{self.session_name}</light-yellow> | Unknown error during Authorization: "
                         f"{error}")
            await asyncio.sleep(delay=3)

    def auto_tap(self, auth_token, tapcount: int):
        try:
            payload = {
                "count": int(tapcount)
            }

            headers['Authorization'] = f'tma {auth_token}'
            # print(headers)
            response = requests.post(api_tap, headers=headers, json=payload)
            if response.status_code == 200:
                response_data = response.json()
                self.available_taps = response_data['clicker']['availableTaps']
                self.max_tap = response_data['clicker']['maxTaps']
                self.multi = response_data['clicker']['earnPerTap']
                logger.info(
                    f"{self.session_name} | <green>Successfully tapped {tapcount} times</green> - Balance: <yellow>{response_data['clicker']['balance']}</yellow> - Available energy: <yellow>{response_data['clicker']['availableTaps']}/{self.max_tap}</yellow> - Earned: <yellow>{response_data['clicker']['balance'] - self.balance}</yellow>")
                self.balance = response_data['clicker']['balance']
            else:
                # print(response)
                logger.info(f"{self.session_name} | Tap failed... Response code: {response.status_code}")
        except Exception as e:
            traceback.print_exc()
            logger.error(f"{self.session_name} | <red>Unknown error while trying to Tap ...: {e}</red>")

    def boost_energy(self, auth_token):
        try:
            payload = {
                "boostId": "full-available-taps",
                "timezone": "Asia/Bangkok"
            }

            headers['Authorization'] = f'tma {auth_token}'
            # print(headers)
            response = requests.post(api_boost, headers=headers, json=payload)
            if response.status_code == 200:
                response_data = response.json()
                self.available_taps = response_data['clicker']['availableTaps']
                self.boost_energy_lvl = response_data['boost']['level']
                self.cool_down = response_data['boost']['lastUpgradeAt']
                logger.info(
                    f"{self.session_name} | <green>Successfully boost full energy...</green>")
            else:
                if response.status_code == 422:
                    self.cool_down = time()
                logger.info(f"{self.session_name} | Boost failed... Response code: {response.status_code}")
        except Exception as e:
            traceback.print_exc()
            logger.error(f"{self.session_name} | <red>Unknown error while trying to boost ...: {e}</red>")


    def boost_turbo(self, auth_token):
        try:
            payload = {
                "boostId": "turbo",
                "timezone": "Asia/Bangkok"
            }

            headers['Authorization'] = f'tma {auth_token}'
            # print(headers)
            response = requests.post(api_boost, headers=headers, json=payload)
            if response.status_code == 200:
                response_data = response.json()
                self.boost_turbo_lvl = response_data['boost']['level']
                logger.info(
                    f"{self.session_name} | <green>Successfully boost turbo...</green>")
                return True
            else:
                logger.info(f"{self.session_name} | Boost failed... Response code: {response.status_code}")
                return False
        except Exception as e:
            traceback.print_exc()

            logger.error(f"{self.session_name} | <red>Unknown error while trying to boost ...: {e}</red>")
            return False


    def get_boost_info(self, auth_token):
        try:
            headers['Authorization'] = f'tma {auth_token}'
            # print(headers)
            response = requests.post(api_boost_info, headers=headers)
            if response.status_code == 200:
                response_data = response.json()
                self.boost_turbo_lvl = response_data['boostsList'][4]['level']
                self.boost_energy_lvl = response_data['boostsList'][1]['level']
                self.cool_down = response_data['boostsList'][1]['lastUpgradeAt']
                self.boosts = response_data['boostsList']
            else:
                logger.info(f"{self.session_name} | Get boost info failed... Response code: {response.status_code}")
        except Exception as e:
            traceback.print_exc()
            logger.error(f"{self.session_name} | <red>Unknown error while trying to get boost info ...: {e}</red>")


    def upgrade_boost(self, auth_token, boostId):
        try:
            if boostId == "earn-per-tap":
                txt = "Multi-tap"
            elif boostId == "max-taps":
                txt = "Energy Limit"
            else:
                txt = "Hourly income limit"
            payload = {
                "boostId": boostId,
                "timezone": "Asia/Bangkok"
            }

            headers['Authorization'] = f'tma {auth_token}'
            # print(headers)
            response = requests.post(api_boost, headers=headers, json=payload)
            if response.status_code == 200:
                response_data = response.json()
                self.balance = response_data['clicker']['balance']
                logger.info(
                    f"{self.session_name} | <green>Successfully upgraded {txt} to lvl: {response_data['boostNewLevel']['level']}</green>")
            else:
                logger.info(f"{self.session_name} | Upgrade {txt} failed.. Response code: {response.status_code}")
        except Exception as e:
            traceback.print_exc()
            logger.error(f"{self.session_name} | <red>Unknown error while trying to upgrade {txt} ...: {e}</red>")


    def get_task_list(self, auth_token):
        try:
            headers['Authorization'] = f'tma {auth_token}'
            # print(headers)
            response = requests.post(api_task_list, headers=headers)
            if response.status_code == 200:
                response_data = response.json()
                self.task_list = response_data['tasks']
            else:
                logger.info(f"{self.session_name} | Get tasks failed... Response code: {response.status_code}")
        except Exception as e:
            traceback.print_exc()
            logger.error(f"{self.session_name} | <red>Unknown error while trying to get task list ...: {e}</red>")

    async def do_task(self, auth_token, taskId):
        try:
            payload = {
                "taskId": taskId,
                "timezone": "Asia/Bangkok"
            }

            headers['Authorization'] = f'tma {auth_token}'
            # print(headers)
            response = requests.post(api_do_task, headers=headers, json=payload)
            if response.status_code == 200:
                response_data = response.json()
                self.balance = response_data['clicker']['balance']
                logger.success(
                    f"{self.session_name} | <green>Successfully claimed {taskId} - Reward: <yellow>{response_data['task']['rewardCoins']}</yellow></green>")
            else:
                if response.status_code == 422:
                    response_data = response.json()
                    if response_data['message'] == "you_are_not_subscribe_to_channel":
                        await self.join_channel()
                logger.info(f"{self.session_name} | failed to do task: {taskId} - Response code: {response.status_code}")
        except Exception as e:
            traceback.print_exc()
            logger.error(f"{self.session_name} | <red>Unknown error while trying to do task: {taskId} - Error: {e}</red>")


    def choose_sponsor(self, auth_token):
        try:
            payload = {
                "sponsor": "okx"
            }

            headers['Authorization'] = f'tma {auth_token}'
            # print(headers)
            response = requests.post(api_sponsor, headers=headers, json=payload)
            if response.status_code == 200:
                logger.success(f"{self.session_name} | Successfully chosen sponsor...")
            else:
                logger.info(f"{self.session_name} | Failed to choose sponsor - Response code: {response.status_code}")
        except Exception as e:
            traceback.print_exc()
            logger.error(f"{self.session_name} | <red>Unknown error while trying to choose sponsor - Error: {e}</red>")

    def get_daily_combo(self):
        response = requests.get("https://freddywhest.github.io/rocky-rabbit-combos/data.json")
        if response.status_code == 200:
            response_data = response.json()
            self.enigma = response_data['enigma']
            self.easter = response_data['easter']
            self.superset = response_data['cards']
            self.easter_expire = response_data['expireAtForEaster']
            self.superset_expire = response_data['expireAtForCards']
        else:
            logger.info(f"{self.session_name} | Get combo data failed.. Response code: {response.status_code}")


    def get_daily_data(self, auth_token):
        try:

            headers['Authorization'] = f'tma {auth_token}'
            # print(headers)
            response = requests.post(api_daily, headers=headers)
            if response.status_code == 200:
                response_data = response.json()
                self.daily_data = response_data
            else:
                logger.info(
                    f"{self.session_name} | failed to do get daily info - Response code: {response.status_code}")
        except Exception as e:
            traceback.print_exc()
            logger.error(
                f"{self.session_name} | <red>Unknown error while trying get daily info - Error: {e}</red>")

    def play_enigma(self, auth_token, enigmaId, passphase):
        try:
            codei = ",".join(passphase)
            payload = {
                "enigmaId": enigmaId,
                "passphrase": codei
            }

            headers['Authorization'] = f'tma {auth_token}'
            # print(headers)
            response = requests.post(api_play_enigma, headers=headers, json=payload)
            if response.status_code == 200:
                response_data = response.json()
                self.balance = response_data['clicker']['balance']
                logger.success(f"{self.session_name} | <green>Successfully claimed enigma</green> | Balance: <yellow>{response_data['clicker']['balance']}</yellow> | Total balance: <yellow>{response_data['clicker']['totalBalance']}</yellow>")
            else:
                logger.info(f"{self.session_name} | Failed to claim enigma - Response code: {response.status_code}")
        except Exception as e:
            traceback.print_exc()
            logger.error(f"{self.session_name} | <red>Unknown error while trying to claim enigma - Error: {e}</red>")

    def play_superset(self, auth_token, comboId, cards):
        try:
            codei = ",".join(cards)
            payload = {
                "comboId": comboId,
                "combos": codei
            }

            headers['Authorization'] = f'tma {auth_token}'
            # print(headers)
            response = requests.post(api_play_combo, headers=headers, json=payload)
            if response.status_code == 200:
                response_data = response.json()
                self.balance = response_data['clicker']['balance']
                logger.success(f"{self.session_name} | <green>Successfully claimed superset</green> | Balance: <yellow>{response_data['clicker']['balance']}</yellow> | Total balance: <yellow>{response_data['clicker']['totalBalance']}</yellow>")
            else:
                logger.info(f"{self.session_name} | Failed to claim superset - Response code: {response.status_code}")
        except Exception as e:
            traceback.print_exc()
            logger.error(f"{self.session_name} | <red>Unknown error while trying to claim superset - Error: {e}</red>")

    def play_easter(self, auth_token, easter, easterEggsId):
        try:
            payload = {
                "easter": easter,
                "easterEggsId": easterEggsId
            }
            print(payload)
            headers['Authorization'] = f'tma {auth_token}'
            # print(headers)
            response = requests.post(api_play_easter, headers=headers, json=payload)
            if response.status_code == 200:
                response_data = response.json()
                self.balance = response_data['clicker']['balance']
                logger.success(f"{self.session_name} | <green>Successfully claimed easter egg</green> | Balance: <yellow>{response_data['clicker']['balance']}</yellow> | Total balance: <yellow>{response_data['clicker']['totalBalance']}</yellow>")
            else:
                if response.status_code == 422:
                    response_data = response.json()
                    print(response_data)
                logger.info(f"{self.session_name} | Failed to claim easter egg - Response code: {response.status_code}")
        except Exception as e:
            traceback.print_exc()
            logger.error(f"{self.session_name} | <red>Unknown error while trying to claim easter egg - Error: {e}</red>")

    def get_cards_info(self, auth_token):
        try:
            headers['Authorization'] = f'tma {auth_token}'
            # print(headers)
            response = requests.post(api_data, headers=headers)
            if response.status_code == 200:
                response_data = response.json()
                #print(response_data)
                self.cardsInfo = response_data['config']['upgrade']
            else:
                logger.info(f"{self.session_name} | Failed to get cards info - Response code: {response.status_code}")
        except Exception as e:
            traceback.print_exc()
            logger.error(f"{self.session_name} | <red>Unknown error while trying to get cards info - Error: {e}</red>")

    def get_user_cards(self, auth_token):
        try:
            headers['Authorization'] = f'tma {auth_token}'
            # print(headers)
            response = requests.post(api_sync, headers=headers)
            if response.status_code == 200:
                response_data = response.json()
                for card in response_data:
                    self.mineCards.update({
                        card['upgradeId']: card
                    })
            else:
                logger.info(f"{self.session_name} | Failed to get user's cards info - Response code: {response.status_code}")
        except Exception as e:
            traceback.print_exc()
            logger.error(f"{self.session_name} | <red>Unknown error while trying to get user's cards info - Error: {e}</red>")

    def check_condition(self, card):
        # print(card['condition'])
        # print(self.mineCards[card['upgradeId']])
        if self.balance < self.mineCards[card['upgradeId']]['price']:
            # logger.info(f"cant upgrade {card['upgradeId']} because of low balance")
            return False
        elif self.mineCards[card['upgradeId']]['type'] == "daily" and self.mineCards[card['upgradeId']]['lastUpgradeAt'] != 0:
            return False
        elif self.mineCards[card['upgradeId']]['level'] > self.user_level:
            # logger.info(f"cant upgrade {card['upgradeId']} because card level larger than user level")
            return False
        elif len(card['condition']) == 0:
            return True
        else:
            for condition in card['condition']:
                if condition['levelUpID'] == "" and condition['type'] == "limit-time":
                    start_time = datetime.strptime(f"{condition['startHour']}:00:01", "%H:%M:%S").time()
                    end_time = datetime.strptime(f"{condition['endHour']}:00:00", "%H:%M:%S").time()
                    curr_time = datetime.now().time()
                    if start_time <= curr_time <= end_time:
                        pass
                    else:
                        #logger.info(f"cant upgrade {card['upgradeId']} because time condition")
                        return False
                elif condition['type'] == "by-upgrade-user" or condition['type'] == "by-upgrade":
                    if (self.mineCards[condition['levelUpID']]['level'] - 1) >= (condition['level'] + 1):
                        pass
                    else:
                        #logger.info(f"cant upgrade {card['upgradeId']} because card conditiono not met")
                        return False

                elif condition['type'] == "invite-friend":
                    if self.ref >= condition['level']:
                        pass
                    else:
                        #logger.info(f"cant upgrade {card['upgradeId']} because ref")
                        return False
                elif condition['type'] == 'by-level':
                    if self.user_level < condition['level']:
                        #logger.info(f"cant upgrade {card['upgradeId']} because user level too low")
                        return False
            return True

    def upgrade_card(self, auth_token, cardId, cost):
        try:
            payload = {
                "upgradeId": cardId,
            }

            headers['Authorization'] = f'tma {auth_token}'
            # print(headers)
            response = requests.post(api_upgrade_card, headers=headers, json=payload)
            if response.status_code == 200:
                response_data = response.json()
                if self.balance > response_data['clicker']['balance']:
                    logger.success(
                        f"{self.session_name} | <green>Successfully upgraded {response_data['upgradesTask']['upgradeId']}</green> | Cost: <yellow>{cost}</yellow> | Balance: <yellow>{response_data['clicker']['balance']}</yellow>")
                else:
                    logger.success(
                        f"{self.session_name} | <green>Successfully claimed {response_data['upgradesTask']['upgradeId']}</green> | Earned: <yellow>{cost}</yellow> | Balance: <yellow>{response_data['clicker']['balance']}</yellow>")

                self.balance = response_data['clicker']['balance']
            else:
                if response.status_code == 422:
                    response_data = response.json()
                    print(response_data)
                logger.info(f"{self.session_name} | Failed to upgrade {cardId} - Response code: {response.status_code}")
        except Exception as e:
            traceback.print_exc()
            logger.error(
                f"{self.session_name} | <red>Unknown error while trying to upgrade {cardId} - Error: {e}</red>")

    async def run(self, proxy: str | None) -> None:
        access_token_created_time = 0
        proxy_conn = ProxyConnector().from_url(proxy) if proxy else None

        headers["User-Agent"] = generate_random_user_agent(device_type='android', browser_type='chrome')
        http_client = CloudflareScraper(headers=headers, connector=proxy_conn)

        if proxy:
            await self.check_proxy(http_client=http_client, proxy=proxy)

        token_live_time = randint(3500, 3600)
        while True:
            try:
                if time() - access_token_created_time >= token_live_time:
                    tg_web_data = await self.get_tg_web_data(proxy)
                    self.auth_token = tg_web_data

                    # print(tg_web_data)
                    access_token_created_time = time()
                    token_live_time = randint(3500, 3600)



                self.get_user_data(self.auth_token)

                if self.new_account:
                    self.acount_init(self.auth_token)

                self.get_user_level(self.auth_token)
                self.get_ref(self.auth_token)

                if settings.AUTO_TASK:
                    self.get_task_list(self.auth_token)

                    for task in self.task_list:
                        if task['id'] == "streak_days_reward" and task['lastUpgradeAt'] != 0:
                            timestamp = task['lastUpgradeAt']
                            timestamp_date = datetime.fromtimestamp(timestamp)
                            today = datetime.now().date()
                            yesterday = today - timedelta(days=1)
                            if timestamp_date.date() == yesterday:
                                await self.do_task(self.auth_token, task['id'])
                            else:
                                continue
                        elif task['id'] == "invite_friends" or task['id'] == "invite_friends_10x":
                            continue
                        elif task['id'] == "RRBOOST":
                            continue
                        elif task['id'] == "select_sponsor" and task['isCompleted'] is False:
                            self.choose_sponsor(self.auth_token)
                            await self.do_task(self.auth_token, task['id'])
                            await asyncio.sleep(randint(2, 5))
                        elif task['isCompleted'] is False:
                            await self.do_task(self.auth_token, task['id'])
                        else:
                            continue

                if settings.AUTO_ENIGMA:
                    self.get_daily_data(self.auth_token)
                    self.get_daily_combo()

                    if self.daily_data['enigma']['completedAt'] == 0:
                        logger.info(f"{self.session_name} | Attempt to play enigma...")
                        self.play_enigma(self.auth_token, self.daily_data['enigma']['enigmaId'], self.enigma)
                    else:
                        logger.info(f"{self.session_name} | Enigma already completed, skipping...")
                    await asyncio.sleep(randint(3,5))

                if settings.AUTO_SUPERSET:
                    self.get_daily_data(self.auth_token)
                    self.get_daily_combo()

                    if self.daily_data['superSet']['completedAt'] == 0:
                        time_to_compare = datetime.strptime(self.superset_expire, "%Y-%m-%dT%H:%M:%S.%fZ")
                        current_time = datetime.utcnow()
                        logger.info(f"{self.session_name} | Attempt to play superset...")
                        if current_time < time_to_compare:
                            self.play_superset(self.auth_token, self.daily_data['superSet']['comboId'], self.superset)
                        else:
                            logger.info(f"{self.session_name} |Wait to find cards combo...")
                    else:
                        logger.info(f"{self.session_name} | Superset already completed, skipping...")
                    await asyncio.sleep(randint(3, 5))

                if settings.AUTO_EASTER:
                    self.get_daily_data(self.auth_token)
                    self.get_daily_combo()
                    if self.daily_data['easterEggs']['completedAt'] == 0:
                        time_to_compare = datetime.strptime(self.easter_expire, "%Y-%m-%dT%H:%M:%S.%fZ")
                        current_time = datetime.utcnow()
                        logger.info(f"{self.session_name} | Attempt to play easter egg...")
                        if current_time < time_to_compare:
                            self.play_easter(self.auth_token, self.easter, self.daily_data['easterEggs']['easterEggsId'])
                        else:
                            logger.info(f"{self.session_name} | Wait to find easter...")
                    else:
                        logger.info(f"{self.session_name} | Easter egg already completed, skipping...")
                    await asyncio.sleep(randint(3, 5))

                i = 10
                if settings.AUTO_TAP:
                    if settings.AUTO_BOOST:
                        self.get_boost_info(self.auth_token)
                    while i > 0:
                        try:
                            tapCount = randint(settings.TAP_COUNT[0], settings.TAP_COUNT[1])
                            if self.available_taps > tapCount*self.multi:
                                if settings.AUTO_BOOST:
                                    if self.boost_turbo_lvl <= 3:
                                        if self.boost_turbo(self.auth_token):
                                            logger.info(f"{self.session_name} | turbo boosted tap faster...")
                                            self.auto_tap(self.auth_token, tapCount)
                                            await asyncio.sleep(randint(3, 5))
                                            self.auto_tap(self.auth_token, tapCount)
                                            await asyncio.sleep(randint(3, 5))

                                self.auto_tap(self.auth_token, tapCount)
                                sleep_ = randint(settings.DELAY_BETWEEN_TAPS[0], settings.DELAY_BETWEEN_TAPS[1])
                                await asyncio.sleep(sleep_)
                            else:
                                if settings.AUTO_BOOST:
                                    if self.boost_energy_lvl <= 5:
                                        current_time = time()
                                        if abs(current_time - self.cool_down) > 3600:
                                            self.boost_energy(self.auth_token)
                                        else:
                                            logger.info(f"{self.session_name} | Cant use boost at this time...")
                                sleep_ = randint(settings.DELAY_BETWEEN_TAPS[0]+120, settings.DELAY_BETWEEN_TAPS[1]+120)
                                logger.info(f"{self.session_name} | Out of energy... -  wait {sleep_} seconds")
                                await asyncio.sleep(sleep_)
                        except:
                            logger.error(f"{self.session_name} | Check your TAP_COUNT setting...")
                        i -= 1

                if settings.AUTO_UPGRADE_CARDS:
                    self.get_cards_info(self.auth_token)
                    self.get_user_cards(self.auth_token)

                    #print(self.mineCards)
                    for card in self.cardsInfo:
                        # print(self.mineCards[card])
                        #print(card)
                        if self.check_condition(card):
                            logger.info(f"{self.session_name} | Attemp to upgrade {card['upgradeId']}...")
                            self.upgrade_card(self.auth_token, card['upgradeId'], self.mineCards[card['upgradeId']]['price'])
                            await asyncio.sleep(randint(2,4))

                if settings.AUTO_UPGRADE_BOOST:
                    if self.boosts is None:
                        self.get_boost_info(self.auth_token)
                    for boost in self.boosts:
                        if boost['boostId'] in self.black_list:
                            continue
                        elif boost['price'] > self.balance:
                            logger.info(f"{self.session_name} | Balance too low to buy {boost['boostId']}.")
                            continue
                        elif boost['boostId'] == "earn-per-tap" and boost['level'] > settings.MULTI_TAP_LVL:
                            continue
                        elif boost['boostId'] == "max-taps" and boost['level'] > settings.MAX_ENERGY_LVL:
                            continue
                        elif boost['boostId'] == "hourly-income-limit" and boost['level'] > settings.PASSIVE_INCOME_LVL:
                            continue
                        else:
                            self.upgrade_boost(self.auth_token, boost['boostId'])

                Sleep = randint(200,300)
                logger.info(f"Sleep {Sleep} seconds...")
                await asyncio.sleep(Sleep)
            except InvalidSession as error:
                raise error

            except Exception as error:
                traceback.print_exc()
                logger.error(f"{self.session_name} | Unknown error: {error}")
                await asyncio.sleep(delay=randint(60, 120))

async def run_tapper(tg_client: Client, proxy: str | None):
    try:
        await Tapper(tg_client=tg_client).run(proxy=proxy)
    except InvalidSession:
        logger.error(f"{tg_client.name} | Invalid Session")
