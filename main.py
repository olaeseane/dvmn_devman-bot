import os
import time
from dotenv import load_dotenv
import requests
import telegram
import logging


DVMN_API_URL = 'https://dvmn.org/api/long_polling/'
MAX_CONNECTION_ERROR = 5
MSG_OK = '''У вас проверили работу "{}". 
К сожалению, в работе есть ошибки'''
MSG_ERRORS = '''У вас проверили работу "{}". 
Преподавателю все понравилось, можно приступать к следующему уроку'''


def send_notification(bot, my_chat_id, user_reviews):
    last_attempt = user_reviews['new_attempts'][0]
    if last_attempt['is_negative']:
        message = MSG_OK.format(last_attempt['lesson_title'])
    else:
        message = MSG_ERRORS.format(last_attempt['lesson_title'])
    bot.send_message(chat_id=my_chat_id, text=message)


def main():
    logging.basicConfig(
        level=logging.INFO, format='%(process)d - %(levelname)s - %(asctime)s - %(message)s')

    load_dotenv()
    api_dvmn_token = os.getenv('API_DVMN_TOKEN')
    headers = {
        'Authorization': f'Token {api_dvmn_token}'
    }
    params = {}

    bot_dvmn_token = os.getenv('BOT_DVMN_TOKEN')
    my_chat_id = os.getenv('MY_TELEGRAM_CHAT_ID')

    bot = telegram.Bot(token=bot_dvmn_token)

    connection_attempts = 0
    while True:
        logging.info('Бот запущен.')
        try:
            response = requests.get(
                DVMN_API_URL, headers=headers, params=params)
            response.raise_for_status()
        except requests.exceptions.HTTPError as http_err:
            print(f'HTTP error occurred - {http_err}')
        except requests.exceptions.ReadTimeout:
            pass
        except requests.exceptions.ConnectionError as conn_err:
            print(f'Connection error occurred - {conn_err}')
            connection_attempts += 1
            if connection_attempts > MAX_CONNECTION_ERROR:
                time.sleep(600)
        else:
            user_reviews = response.json()
            if user_reviews['status'] == 'timeout':
                params['timestamp'] = user_reviews['timestamp_to_request']
            elif user_reviews['status'] == 'found':
                send_notification(bot, my_chat_id, user_reviews)
                params['timestamp'] = user_reviews['last_attempt_timestamp']


if __name__ == '__main__':
    main()
