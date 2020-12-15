import os
import requests
import time
from dotenv import load_dotenv
from requests.exceptions import HTTPError
from requests.exceptions import ReadTimeout
from requests.exceptions import ConnectionError
import telegram


API_DVMN_API_URL = 'https://dvmn.org/api/long_polling/'
MAX_CONNECTION_ERROR = 5
LAST_ATTEMPT_INDEX = 0


def send_notification(bot, my_chat_id, user_reviews):
    last_attempt = user_reviews['new_attempts'][LAST_ATTEMPT_INDEX]
    if last_attempt['is_negative'] == True:
        message = f'У вас проверили работу \"{last_attempt["lesson_title"]}\".\nК сожалению, в работе есть ошибки'
    else:
        message = f'У вас проверили работу \"{last_attempt["lesson_title"]}\".\nПреподавателю все понравилось, можно приступать к следующему уроку'
    bot.send_message(
        chat_id=my_chat_id, text=message)


def main():
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
        try:
            response = requests.get(
                API_DVMN_API_URL, headers=headers, params=params)
            print('requests.getting...')
            response.raise_for_status()
        except HTTPError as http_err:
            print(f'HTTP error occurred - {http_err}')
        except ConnectionError as conn_err:
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
