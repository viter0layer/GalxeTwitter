import asyncio
import copy
import json
import sys
import time
from time import sleep
from random import randint, uniform
from uuid import uuid4

import aiohttp
from web3 import Web3
from fake_useragent import UserAgent
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from termcolor import cprint
from data.config import config
from loguru import logger
from eth_account.messages import encode_defunct
import random
from datetime import datetime, timedelta
from requests_html import AsyncHTMLSession

from data.consts import TASK_ID_TO_TASK_STRING


class AlreadyFollowingException(Exception):
    pass

class ElementClickInterceptedException(Exception):
    pass


class Profile:
    DOLPHIN_API_ROOT = "http://localhost:3001/v1.0/browser_profiles/"
    ADS_POWER_API_ROOT = 'http://local.adspower.com:50325'
    rpcs = {'bsc': 'https://bscrpc.com',
            'polygon': 'https://polygon-rpc.com',
            'core': 'https://rpc.coredao.org',
            'opbnb': 'https://opbnb-testnet-rpc.bnbchain.org',
            'eth': 'https://rpc.ankr.com/eth'}
    DEFAULT_CHAIN = 'eth'

    def __init__(self, private_key, _id='0', twitter_handle=None, proxy=None, proxy_pool=None, tasks_for_claim=None, task=None):
        self.task = task
        self.tasks_for_claim = tasks_for_claim
        self.verified_on_galxe = None
        self.proxy_pool = proxy_pool
        self.tweet_posted = False
        self.user_gid = None
        self.username_was_updated = False
        self.session = None
        self.private_key = private_key
        self._id = _id
        self.twitter_handle = twitter_handle
        self.profile_was_running = False
        self.driver = None
        self.action = None
        if self.task == 'claim_points':
            self.address = private_key
        else:
            self.w3 = Web3(Web3.HTTPProvider(self.rpcs['eth']))
            self.account = self.w3.eth.account.from_key(self.private_key)
            self.address = self.account.address

        if config['anti_detect_browser'] == 'Dolphin':
            self.open_url = self.DOLPHIN_API_ROOT + self._id + f"/start?automation=1"
            self.close_url = self.DOLPHIN_API_ROOT + self._id + "/stop"
        else:
            self.open_url = self.ADS_POWER_API_ROOT + '/api/v1/browser/start'
            self.close_url = self.ADS_POWER_API_ROOT + '/api/v1/browser/stop' + f'?user_id={self._id}'
        if proxy:
            self.proxy = f'http://{proxy}'
        else:
            self.proxy = None

    @staticmethod
    def random_sleep():
        logger.info(f"sleeping")
        sleep(randint(config["sleep_between_actions_from"], config["sleep_between_actions_to"]))

    async def sleeping(self):
        x = random.randint(config["sleep_between_actions_from"], config["sleep_between_actions_to"])
        logger.info(f'жду {x} секунд...')
        await asyncio.sleep(x)

    def human_click(self, click_object, action_context=None):
        size = click_object.size

        if action_context is not None and action_context == 'click_on_tweet':
            height_deviation = config['max_height_deviation_tweet_find']
            width_deviation = config['max_width_deviation_tweet_find']
        else:
            height_deviation = config['max_height_deviation']
            width_deviation = config['max_width_deviation']

        width_deviation_pixels = randint(1, int(size["width"] * width_deviation))
        height_deviation_pixels = randint(1, int(size["height"] * height_deviation))

        positive_width_deviation = randint(0, 1)
        positive_height_deviation = randint(0, 1)

        x = width_deviation_pixels if positive_width_deviation else -width_deviation_pixels
        y = height_deviation_pixels if positive_height_deviation else -height_deviation_pixels

        self.action.move_to_element_with_offset(click_object, x, y).click().perform()

    def human_type(self, text: str):
        for char in text:
            sleep(uniform(config["min_typing_pause_seconds"], config["max_typing_pause_seconds"]))
            self.driver.switch_to.active_element.send_keys(char)

    def init_webdriver(self, chrome_driver, debugger_address):
        try:

            chrome_options = Options()
            chrome_options.add_experimental_option("debuggerAddress", debugger_address)

            # !!! если у вас ошибки с chromedriver то вам надо изменить путь chrome_driver !!!
            # If you have issues with chrome driver, change this path
            # executable_path = 'chromedriver_win32_110/chromedriver.exe'
            executable_path = chrome_driver
            service = Service(executable_path=executable_path)
            driver = webdriver.Chrome(service=service, options=chrome_options)

            driver.set_window_position(700, 0)
            driver.set_window_size(900, 1000)
            driver.switch_to.new_window()
            self.driver = driver
            self.action = ActionChains(driver)

        except Exception as e:
            logger.error(f'{self.address} - profile opening error | {e}')
            requests.get(self.close_url)
            sys.exit(0)

    def open_ads_power_profile(self):
        url = self.ADS_POWER_API_ROOT + '/api/v1/browser/start'
        params = {
            "user_id": self._id,
            "open_tabs": "1",
            "ip_tab": "0",
        }

        response = requests.get(url, params=params).json()
        if response["code"] != 0:
            raise Exception('Failed to open profile')

        self.init_webdriver(response["data"]["webdriver"], response["data"]["ws"]["selenium"])

    def open_dolphin_profile(self):
        try:
            # Отправка запроса на открытие профиля
            resp = requests.get(self.open_url).json()
            sleep(.5)
        except requests.exceptions.ConnectionError:
            cprint(f'Dolphin is not running.', 'red')
            sys.exit(0)
        except requests.exceptions.JSONDecodeError:
            cprint(f'Проверьте ваше подключение. Отключите VPN/Proxy используемые напрямую.', 'red')
            sys.exit(0)
        except Exception as e:
            logger.error(f'error occured while opening dolphin profile | {e}')
            sys.exit(0)

        port = str(resp["automation"]["port"])
        debuggerAddress = "127.0.0.1:" + port
        logger.info(f"will start session on {debuggerAddress}")
        self.init_webdriver(port, debuggerAddress)

    def close_profile(self):
        self.driver.quit()
        requests.get(self.close_url)

    def post_tweet(self, tweet_text: str):
        self.driver.implicitly_wait(30)
        self.driver.get(f'https://twitter.com/{self.twitter_handle}')

        self.random_sleep()
        self.driver.find_element(By.CSS_SELECTOR, '[href="/compose/tweet"]').click()
        self.random_sleep()
        try:
            self.driver.find_element(By.CSS_SELECTOR, '[data-testid="HoverCard"]')
            self.driver.execute_script('el = document.elementFromPoint(0, 0); el.click();')
            self.random_sleep()
        except Exception as e:
            pass

        self.driver.switch_to.active_element.send_keys(tweet_text + ' ')

        self.random_sleep()
        final_tweet_button = self.driver.find_element(By.CSS_SELECTOR, '[data-testid="tweetButton"]')
        if self.driver.find_element(By.CSS_SELECTOR, f'[aria-label="Choose audience"]').text == 'Twitter Circle':
            raise Exception('flow went wrong - clicked on twitter circle')
        try:
            self.human_click(final_tweet_button)
        except:
            final_tweet_button.click()

        self.random_sleep()

    async def _login(self):
        ua = UserAgent()
        ua = ua.random
        headers = {
            'accept': '*/*',
            'accept-language': 'pl-PL,pl;q=0.9,en-US;q=0.8,en;q=0.7',
            'content-type': 'application/json',
            'origin': 'https://galxe.com',
            'user-agent': ua,
        }

        nonce = self.random_string(17)
        issued_at = datetime.utcnow().isoformat() + 'Z'
        expired_at = (datetime.now() + timedelta(days=1)).isoformat() + 'Z'

        msg = f'galxe.com wants you to sign in with your Ethereum account:\n{self.address}\n\nSign in with Ethereum to the app.\n\nURI: https://galxe.com\nVersion: 1\nChain ID: 1\nNonce: {nonce}\nIssued At: {issued_at}\nExpiration Time: {expired_at}'
        message_object = encode_defunct(text=msg)
        sign = self.w3.eth.account.sign_message(message_object, private_key=self.private_key)
        signature = self.w3.to_hex(sign.signature)
        sign_in_query = {
            "operationName": "SignIn",
            "variables": {"input": {"address": self.address, "message": msg, "signature": signature}},
            "query": "mutation SignIn($input: Auth) {\n  signin(input: $input)\n}\n"
        }

        retries = 0
        while retries < config['max_retries']:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post('https://graphigo.prd.galaxy.eco/query',
                                            json=sign_in_query, headers=headers, proxy=self.proxy) as response:
                        if response.status == 200:
                            logger.success(f"{self.address} | successfully authorized with galxe")
                            msg = json.loads(await response.text())
                            token = msg['data']['signin']
                            headers['authorization'] = token
                            return headers
                        else:
                            raise Exception(f"{self.address} | got non 200 response from Galxe | {response.status}")
            except Exception as e:
                retries += 1
                proxy = random.choice(self.proxy_pool)
                self.proxy = f'http://{proxy}'
                self.session = None
                logger.error(f"{self.address} | error occured while trying to login | {e} | try again {retries}/{config['max_retries']}")
        raise Exception(f"{self.address} | failed to login after all retries")

    def verify_on_galaxy(self):
        if self.session is None:
            loop = asyncio.get_event_loop()
            coroutine = self._login()
            headers = loop.run_until_complete(coroutine)
            self.session = requests.Session()
            self.session.headers.update(headers)
            self.random_sleep()
            if not self.session:
                raise Exception('failed establishing connection with Galxe')
        if not self.username_was_updated:
            self.update_username()
            self.random_sleep()

        if self.user_gid is None:
            user_gid = self.get_user_gid()
            if user_gid:
                self.user_gid = user_gid
            else:
                raise Exception("failed getting user Galxe ID")
            self.random_sleep()

        tweet_text = f"Verifying my Twitter account for my #GalxeID gid:{self.user_gid}\n @Galxe"
        if not self.tweet_posted:
            self.post_tweet(tweet_text)
            self.tweet_posted = True

        self.driver.implicitly_wait(30)
        self.driver.get(f'https://twitter.com/{self.twitter_handle}')
        self.random_sleep()
        self.driver.execute_script("window.scrollTo(0,100)")

        tweet = self.driver.find_element(By.XPATH, '//div[@data-testid="tweetText"]')
        try:
            self.human_click(tweet, 'click_on_tweet')
        except Exception as e:
            tweet.click()

        self.random_sleep()
        tweet_url = self.driver.current_url
        if self.twitter_handle in tweet_url:
            logger.info(f"{self.address} | successfully retrieved tweet url: {tweet_url}")
            self.verify_twitter(tweet_url)
            self.random_sleep()
            self.verified_on_galxe = True
        else:
            raise Exception(f'{self.address} | failed to retrieve tweet url, tweet url retrieved is: {tweet_url}')

    async def complete_galxe_social_tasks(self):
        self.random_sleep()
        res = {'Address': self.address, 'AKey': self.private_key}
        if self.session is None:
            logger.info(f'{self.address} | trying to log in to galxe')
            try:
                await self._login()
            except Exception as e:
                logger.error(e)
                res['status'] = 'failed on login'
                return res

        self.random_sleep()
        retries = 0
        cloned_task_ids = copy.deepcopy(config['galxe_social_tasks_ids'])
        max_retries = config['max_retries']

        for task_id in list(cloned_task_ids):
            task_name = TASK_ID_TO_TASK_STRING[task_id]
            logger.info(f'{self.address} | {task_name} | trying to verify captcha')
            captcha_data = await self.verify_captcha()
            logger.success(f'{self.address} | {task_name} | captcha verified successfully')
            complete_galxe_social_tasks_query = {
                "operationName": "AddTypedCredentialItems",
                "query": "mutation AddTypedCredentialItems($input: MutateTypedCredItemInput!) {\n  typedCredentialItems(input: $input) {\n    id\n    __typename\n  }\n}\n",
                "variables": {
                    "input": {
                        "captcha": {
                            'lotNumber': captcha_data['lot_number'],
                            'captchaOutput': captcha_data['seccode']['captcha_output'],
                            'passToken': captcha_data['seccode']['pass_token'],
                            'genTime': captcha_data['seccode']['gen_time'],
                        },
                        "credId": task_id,
                        "items": [self.address],
                        "operation": "APPEND",
                    }
                },
            }
            while True:
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.post('https://graphigo.prd.galaxy.eco/query',
                                                json=complete_galxe_social_tasks_query, proxy=self.proxy) as response:
                            if response.status == 200:
                                msg = json.loads(await response.text())
                                if 'errors' in msg:
                                    raise Exception(f'got error from Galxe {msg["errors"]}')
                                res[task_name] = 'success'
                                logger.success(
                                    f"{self.address} | {task_name} | successfully completed task on Galxe")
                                cloned_task_ids.remove(task_id)
                                self.random_sleep()
                                break
                            else:
                                raise Exception(f'got status code {response.status}')
                except Exception as e:
                    proxy = random.choice(self.proxy_pool)
                    self.proxy = f'http://{proxy}'
                    if retries >= max_retries:
                        res[task_name] = 'failure'
                        logger.error(f'{self.address} | failed on task {task_name} after 3 retries, continue')
                        retries = 0
                        break
                    retries += 1
                    logger.error(f'{self.address} | {e}, doing retry: {retries}/{max_retries}')
                    self.random_sleep()

        return res

    async def verify_captcha(self):
        logger.info(f'{self.address} | verifying captcha')
        call = int(time.time() * 1e3)
        params = {
            'captcha_id': '244bcb8b9846215df5af4c624a750db4',
            'challenge': uuid4(),
            'client_type': 'web',
            'lang': 'et',
            'callback': 'geetest_{}'.format(call),
        }

        resp = requests.get('https://gcaptcha4.geetest.com/load', params=params)
        js_data = json.loads(resp.text.strip('geetest_{}('.format(call)).strip(')'))['data']

        params = {
            'captcha_id': '244bcb8b9846215df5af4c624a750db4',
            'client_type': 'web',
            'lot_number': js_data['lot_number'],
            'payload': js_data['payload'],
            'process_token': js_data['process_token'],
            'payload_protocol': '1',
            'pt': '1',
            'w': config["W"],
            'callback': 'geetest_{}'.format(call),
        }

        resp_complete = requests.get('https://gcaptcha4.geetest.com/verify', params=params)
        return json.loads(resp_complete.text.strip('geetest_{}('.format(call)).strip(')'))['data']

    def verify_twitter(self, tweet_url):
        verify_tweeter_query = {
            "operationName": "VerifyTwitterAccount",
            "query": 'mutation VerifyTwitterAccount($input: VerifyTwitterAccountInput!) {\n  verifyTwitterAccount(input: $input) {\n    address\n    twitterUserID\n    twitterUserName\n    __typename\n  }\n}\n',
            "variables": {
                "input": {
                    "address": self.address,
                    "tweetURL": tweet_url
                }
            },
        }
        try:
            response = self.session.post('https://graphigo.prd.galaxy.eco/query', json=verify_tweeter_query,
                                         proxies={"proxies":{'https' : self.proxy, 'http' : self.proxy}})
            if response.status_code == 200:
                json_response = json.loads(response.text)
                logger.info(
                    f"{self.address} | successfully verified tweeter account | twitter username is {json_response['data']['verifyTwitterAccount']['twitterUserName']}")

        except Exception as e:
            proxy = random.choice(self.proxy_pool)
            self.proxy = f'http://{proxy}'
            self.session = None
            raise Exception(e)

    def get_user_gid(self):
        get_address_info_query = {
            "operationName": "RecentParticipation",
            "variables": {
                "address": self.address,
                'participationInput': {
                    "first": 30,
                    "onlyGasless": False,
                    "onlyVerified": False
                }
            },
            "query": "query RecentParticipation($address: String!, $participationInput: ListParticipationInput!) {\n  addressInfo(address: $address) {\n    id\n    recentParticipation(input: $participationInput) {\n      list {\n        id\n        chain\n        tx\n        campaign {\n          id\n          name\n          dao {\n            id\n            alias\n            __typename\n          }\n          __typename\n        }\n        status\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n}\n"
        }
        try:
            response = self.session.post('https://graphigo.prd.galaxy.eco/query', json=get_address_info_query,
                                         proxies={"proxies":{'https' : self.proxy, 'http' : self.proxy}})
            if response.status_code == 200:
                json_response = json.loads(response.text)
                user_gid = json_response['data']['addressInfo']['id']
                logger.info(
                    f"{self.address} | successfully got user info | Galxe ID for this user is {user_gid}")
                return user_gid

        except Exception as e:
            proxy = random.choice(self.proxy_pool)
            self.proxy = f'http://{proxy}'
            self.session = None
            raise Exception(f'{self.address} | error occured while trying to get user info | {e}')

    def update_username(self):
        username = self.random_string(25)
        update_profile_query = {
            "operationName": "UpdateProfile",
            "variables": {"input": {"address": self.address, "avatar": f'https://source.boringavatars.com/marble/120/{self.address}',
                                    "displayNamePref": "USERNAME", 'username': username}},
            "query": "mutation UpdateProfile($input: UpdateProfileInput!) {\n  updateProfile(input: $input) {\n    code\n    message\n    __typename\n  }\n}\n"
        }
        try:
            response = self.session.post('https://graphigo.prd.galaxy.eco/query', json=update_profile_query, proxies={"proxies":{'https' : self.proxy, 'http' : self.proxy}})
            if response.status_code == 200:
                self.username_was_updated = True
                logger.info(f"{self.address} | successfully changed username with galxe | generated galxe username: {username}")
        except Exception as e:
            proxy = random.choice(self.proxy_pool)
            self.proxy = f'http://{proxy}'
            self.session = None
            raise Exception(f'error occured while trying to change username | {e}')

    def random_string(self,length):
        characters = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        return ''.join(random.choice(characters) for _ in range(length))

    async def claim(self):
        res = {'Address': self.address, 'AKey': self.private_key}
        for task_id in self.tasks_for_claim:
            if len(task_id) > 10:
                task_id = task_id.split('/')[-1]

            information_by_id = await self.get_info(task_id)
            if information_by_id is None:
                await self.sleeping()
                continue
            campaign_name = information_by_id[3]
            if information_by_id[0] == 'Active':
                try:
                    claimed = await self._claim(campaign_name, task_id, information_by_id[-1])
                    status = 'successfully claimed'
                    if claimed:
                        logger.success(f"{self.address} | {campaign_name} | successfully claimed points")
                    else:
                        status = 'not allowed to claim'
                        logger.warning(f"{self.address} | {campaign_name} | not allowed to claim points")
                    res[campaign_name] = status
                except Exception as e:
                    logger.error(f"{self.address} | {campaign_name} | {e}")
                    res[campaign_name] = str(e)

                await self.sleeping()
            else:
                res[campaign_name] = 'campaign not active'
        return res

    async def _claim(self, campaign_name, campaign_id, chain='MATIC'):
        ua = UserAgent()
        ua = ua.random
        max_retries = config['max_retries']

        captcha_data = await self.verify_captcha()

        json_data = {
            'operationName': 'PrepareParticipate',
            'variables': {
                'input': {
                    'signature': '',
                    'campaignID': campaign_id,
                    'address': self.address,
                    'mintCount': 1,
                    'chain': chain,
                    'captcha': {
                        'lotNumber': captcha_data['lot_number'],
                        'captchaOutput': captcha_data['seccode']['captcha_output'],
                        'passToken': captcha_data['seccode']['pass_token'],
                        'genTime': captcha_data['seccode']['gen_time'],
                    },
                },
            },
            'query': 'mutation PrepareParticipate($input: PrepareParticipateInput!) {\n  prepareParticipate(input: $input) {\n    allow\n    disallowReason\n    signature\n    nonce\n    mintFuncInfo {\n      funcName\n      nftCoreAddress\n      verifyIDs\n      powahs\n      cap\n      __typename\n    }\n    extLinkResp {\n      success\n      data\n      error\n      __typename\n    }\n    metaTxResp {\n      metaSig2\n      autoTaskUrl\n      metaSpaceAddr\n      forwarderAddr\n      metaTxHash\n      reqQueueing\n      __typename\n    }\n    solanaTxResp {\n      mint\n      updateAuthority\n      explorerUrl\n      signedTx\n      verifyID\n      __typename\n    }\n    aptosTxResp {\n      signatureExpiredAt\n      tokenName\n      __typename\n    }\n    __typename\n  }\n}\n',
        }
        headers = {
            'authority': 'graphigo.prd.galaxy.eco',
            'accept': '*/*',
            'user-agent': ua,
            'content-type': 'application/json',
        }
        retries = 0
        while retries < max_retries:
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.post('https://graphigo.prd.galaxy.eco/query', headers=headers,
                                            data=json.dumps(json_data), proxy=self.proxy) as r:
                        if r.status != 200:
                            raise Exception(f'{campaign_name} got non 200 response from galaxe')
                        res = await r.text()
                        json_res = json.loads(res)
                        allowed = json_res['data']['prepareParticipate']['allow']
                        if allowed:
                            return True
                        return False
                except Exception as e:
                    proxy = random.choice(self.proxy_pool)
                    self.proxy = f'http://{proxy}'
                    logger.error(
                        f'{campaign_name} | {e} | trying again with new proxy - {retries}/{max_retries}')
                    retries += 1
                    self.random_sleep()
                    continue

        raise Exception(f'{campaign_name} | failed to get 200 response from galxe after all retries')

    async def get_info(self, task_id):
        info = await self.get_info_by_id(task_id)
        try:
            data = info['data']['campaign']
            status, gas_type, number_id, name, chain = data['status'], \
                data['gasType'], \
                data['numberID'], \
                data['name'], \
                data['chain']
        except Exception as e:
            logger.error(f"unexpected output from galxe {info}")
            return None

        return status, gas_type, number_id, name, chain

    async def get_info_by_id(self, task_id):
        ua = UserAgent()
        ua = ua.random
        HEADERS = {
            'user-agent': ua
        }

        json_data = {
            'operationName': 'CampaignInfo',
            'variables': {
                'address': '',
                'id': task_id,
            },
            'query': 'query CampaignInfo($id: ID!, $address: String!) {\n  campaign(id: $id) {\n    ...CampaignDetailFrag\n    space {\n      ...SpaceDetail\n      isAdmin(address: $address)\n      __typename\n    }\n    isBookmarked(address: $address)\n    childrenCampaigns {\n      ...CampaignDetailFrag\n      parentCampaign {\n        id\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n}\n\nfragment CampaignDetailFrag on Campaign {\n  id\n  ...CampaignMedia\n  name\n  numberID\n  type\n  cap\n  info\n  useCred\n  formula\n  status\n  creator\n  numNFTMinted\n  thumbnail\n  gasType\n  isPrivate\n  createdAt\n  requirementInfo\n  description\n  enableWhitelist\n  chain\n  startTime\n  endTime\n  requireEmail\n  requireUsername\n  blacklistCountryCodes\n  whitelistRegions\n  participants {\n    participantsCount\n    bountyWinnersCount\n    __typename\n  }\n  rewardType\n  distributionType\n  rewardName\n  spaceStation {\n    id\n    address\n    chain\n    __typename\n  }\n  ...WhitelistInfoFrag\n  ...WhitelistSubgraphFrag\n  gamification {\n    ...GamificationDetailFrag\n    __typename\n  }\n  creds {\n    ...CredForAddress\n    __typename\n  }\n  dao {\n    ...DaoSnap\n    nftCores {\n      list {\n        capable\n        marketLink\n        contractAddress\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment DaoSnap on DAO {\n  id\n  name\n  logo\n  alias\n  isVerified\n  __typename\n}\n\nfragment CampaignMedia on Campaign {\n  thumbnail\n  rewardName\n  type\n  gamification {\n    id\n    type\n    __typename\n  }\n  __typename\n}\n\nfragment CredForAddress on Cred {\n  id\n  name\n  type\n  credType\n  credSource\n  referenceLink\n  description\n  lastUpdate\n  credContractNFTHolder {\n    timestamp\n    __typename\n  }\n  chain\n  eligible(address: $address)\n  subgraph {\n    endpoint\n    query\n    expression\n    __typename\n  }\n  __typename\n}\n\nfragment WhitelistInfoFrag on Campaign {\n  id\n  whitelistInfo(address: $address) {\n    address\n    maxCount\n    usedCount\n    __typename\n  }\n  __typename\n}\n\nfragment WhitelistSubgraphFrag on Campaign {\n  id\n  whitelistSubgraph {\n    query\n    endpoint\n    expression\n    variable\n    __typename\n  }\n  __typename\n}\n\nfragment GamificationDetailFrag on Gamification {\n  id\n  type\n  nfts {\n    nft {\n      id\n      animationURL\n      category\n      powah\n      image\n      name\n      treasureBack\n      nftCore {\n        ...NftCoreInfoFrag\n        __typename\n      }\n      traits {\n        name\n        value\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n  airdrop {\n    name\n    contractAddress\n    token {\n      address\n      icon\n      symbol\n      __typename\n    }\n    merkleTreeUrl\n    addressInfo(address: $address) {\n      index\n      amount {\n        amount\n        ether\n        __typename\n      }\n      proofs\n      __typename\n    }\n    __typename\n  }\n  forgeConfig {\n    minNFTCount\n    maxNFTCount\n    requiredNFTs {\n      nft {\n        category\n        powah\n        image\n        name\n        nftCore {\n          capable\n          contractAddress\n          __typename\n        }\n        __typename\n      }\n      count\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment NftCoreInfoFrag on NFTCore {\n  id\n  capable\n  chain\n  contractAddress\n  name\n  symbol\n  dao {\n    id\n    name\n    logo\n    alias\n    __typename\n  }\n  __typename\n}\n\nfragment SpaceDetail on Space {\n  id\n  name\n  info\n  thumbnail\n  alias\n  links\n  isVerified\n  __typename\n}\n',
        }

        retries = 0
        while retries < config['max_retries']:
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.post('https://graphigo.prd.galaxy.eco/query', headers=HEADERS,
                                            json=json_data, proxy=self.proxy) as response:
                        if response.status != 200:
                            raise Exception(f'{self.address} got non 200 response from galaxe')
                        json_res = await response.json()
                        if json_res is None:
                            raise Exception(f'{self.address} got None from Galxe')
                        if "error" in json_res:
                            raise Exception(f'{self.address} got errors - {json_res["errors"]}')
                        return json_res
                except Exception as e:
                    proxy = random.choice(self.proxy_pool)
                    self.proxy = f'http://{proxy}'
                    logger.error(
                        f'{self.address} | {e} | trying again with new proxy - {retries}/{3}')
                    retries += 1
                    self.random_sleep()
                    continue

    async def __validation_captcha(self):
        session = AsyncHTMLSession()

        call = int(time.time() * 1e3)
        params = {
            'captcha_id': '244bcb8b9846215df5af4c624a750db4',
            'challenge': uuid4(),
            'client_type': 'web',
            'lang': 'et',
            'callback': 'geetest_{}'.format(call),
        }

        resp = await session.get('https://gcaptcha4.geetest.com/load', params=params)
        js_data = json.loads(resp.text.strip('geetest_{}('.format(call)).strip(')'))['data']

        params = {
            'captcha_id': '244bcb8b9846215df5af4c624a750db4',
            'client_type': 'web',
            'lot_number': js_data['lot_number'],
            'payload': js_data['payload'],
            'process_token': js_data['process_token'],
            'payload_protocol': '1',
            'pt': '1',
            'w': config['W'],
            'callback': 'geetest_{}'.format(call),
        }

        resp_complete = await session.get('https://gcaptcha4.geetest.com/verify', params=params)
        VALIDATION = json.loads((resp_complete.text).strip('geetest_{}('.format(call)).strip(')'))['status']
        return VALIDATION

    async def validation_config_w(self):
        try:
            data = await self.__validation_captcha()
            if data == 'success':
                logger.success('VALIDATION CAPTCHA | SUCCESS')
                return True

            if data == 'error':
                logger.error('VALIDATION CAPTCHA | FALSE ')
                return False

            logger.error('VALIDATION CAPTCHA | FALSE | UNKNOWN PARAMETERS | {}'.format(data))
            return False
        except Exception as e:
            logger.error('VALIDATION CAPTCHA ERROR | FALSE | {}'.format(e))
            return False
