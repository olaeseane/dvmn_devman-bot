import os
import time
import requests
import telegram
import logging


DVMN_API_URL = 'https://dvmn.org/api/long_polling/'
MAX_CONNECTION_ERROR = 5
MSG_OK = '''У вас проверили работу "{}". 
К сожалению, в работе есть ошибки'''
MSG_ERRORS = '''У вас проверили работу "{}". 
Преподавателю все понравилось, можно приступать к следующему уроку'''


class BotLogsHandler(logging.Handler):
    def __init__(self, bot, chat_id):
        self.bot = telegram.Bot(token=os.getenv('BOT_LOGGER_TOKEN'))
        self.my_chat_id = chat_id
        super().__init__()

    def emit(self, record):
        log_entry = self.format(record)
        self.bot.send_message(chat_id=self.my_chat_id, text=log_entry)


def send_notification(bot, my_chat_id, user_reviews):
    last_attempt = user_reviews['new_attempts'][0]
    if last_attempt['is_negative']:
        message = MSG_OK.format(last_attempt['lesson_title'])
    else:
        message = MSG_ERRORS.format(last_attempt['lesson_title'])
    bot.send_message(chat_id=my_chat_id, text=message)


def main():
    api_dvmn_token = os.getenv('API_DVMN_TOKEN')
    headers = {
        'Authorization': f'Token {api_dvmn_token}'
    }
    params = {}

    my_chat_id = os.getenv('MY_TELEGRAM_CHAT_ID')

    bot = telegram.Bot(token=os.getenv('BOT_MAIN_TOKEN'))

    logger = logging.getLogger('bot-logger')
    logger.basicConfig(
        level=logging.INFO, format='%(process)d - %(levelname)s - %(asctime)s - %(message)s')
    logger.setLevel(logging.INFO)
    logger.addHandler(BotLogsHandler(my_chat_id))
    logger.info('Bot has started')

    connection_attempts = 0
    while True:
        try:
            response = requests.get(
                DVMN_API_URL, headers=headers, params=params)
            response.raise_for_status()
            user_reviews = response.json()
            0/0
            if user_reviews['status'] == 'timeout':
                params['timestamp'] = user_reviews['timestamp_to_request']
            elif user_reviews['status'] == 'found':
                send_notification(bot, my_chat_id, user_reviews)
                params['timestamp'] = user_reviews['last_attempt_timestamp']
        except requests.exceptions.ReadTimeout:
            pass
        except requests.exceptions.HTTPError as http_err:
            logger.error(f'HTTP error occurred - {http_err}')
        except requests.exceptions.ConnectionError as conn_err:
            logger.error(f'Connection error occurred - {conn_err}')
            connection_attempts += 1
            if connection_attempts > MAX_CONNECTION_ERROR:
                time.sleep(600)
        except Exception:
            logger.error('Other error occured')
            logger.exception()


if __name__ == '__main__':
    main()
