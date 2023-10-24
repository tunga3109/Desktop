import os
import time
import atexit
from datetime import datetime
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from slack_sdk.socket_mode import SocketModeClient
from slack_sdk.socket_mode.request import SocketModeRequest
from dotenv import load_dotenv

# Константы
REACT_ADDED = "reaction_added"
WHITE_CHECK_MARK = "white_check_mark"

# Загрузка переменных окружения из файла .env
load_dotenv()

# Получение токенов из переменных окружения
USER_TOKEN = os.environ.get("USER_TOKEN")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
APP_TOKEN = os.environ.get("APP_TOKEN")

class SlackBot:
    def __init__(self):
        # Инициализация клиентов для работы с API Slack
        self.bot_client = WebClient(token=BOT_TOKEN)
        self.user_client = WebClient(token=USER_TOKEN)
        self.socket_mode_client = SocketModeClient(app_token=APP_TOKEN, web_client=self.bot_client)
               
        # Множества для хранения обработанных и удаленных сообщений
        self.deleted_messages = set()
        self.messages_under_review = set()

        # Регистрация обработчика выхода
        atexit.register(self.exit_handler)

    def get_current_time(self):
        """Возвращает текущее время и дату в формате 'дд/мм/гг чч:мм:сс.мс'"""
        return datetime.now().strftime('%d/%m/%y %H:%M:%S.%f')[:-3]

    def exit_handler(self):
        """Обработчик выхода, отправляет сообщение при завершении работы бота"""
        self.broadcast_message("А теперь не будет чисто")

    def get_channel_name(self, channel_id):
        """Возвращает имя канала по его ID"""
        try:
            response = self.bot_client.conversations_info(channel=channel_id)
            return response['channel']['name']
        except SlackApiError as e:
            print(f"[{self.get_current_time()}] Ошибка при получении имени канала: {e.response['error']}")
            return "unknown_channel"

    def get_channels(self):
        """Возвращает список ID каналов, в которых бот является участником"""
        channels = []
        try:
            response = self.bot_client.conversations_list(types="public_channel,private_channel")
            for channel in response['channels']:
                if channel['is_member']:
                    channels.append(channel['id'])
        except SlackApiError as e:
            print(f"[{self.get_current_time()}] Ошибка при получении списка каналов: {e.response['error']}")
        return channels

    def broadcast_message(self, message):
        """Отправляет сообщение во все каналы, в которых бот является участником"""
        channels = self.get_channels()
        for channel_id in channels:
            channel_name = self.get_channel_name(channel_id)
            try:
                self.bot_client.chat_postMessage(channel=channel_id, text=message)
                print(f"[{self.get_current_time()}] Сообщение '{message}' было отправлено в #{channel_name} ({channel_id}).")
            except SlackApiError as e:
                print(f"[{self.get_current_time()}] Ошибка при отправке сообщения в #{channel_name} ({channel_id}): {e.response['error']}")

    def check_white_check_mark_reaction(self, channel_id, message_ts):
        """Проверяет наличие реакции WHITE_CHECK_MARK на сообщение"""
        try:
            response = self.user_client.reactions_get(channel=channel_id, timestamp=message_ts)
            if "message" not in response:
                print(f"[{self.get_current_time()}] Сообщение с ID {message_ts} не найдено.")
                return False
            reactions = response["message"]["reactions"]
            return any(reaction["name"] == WHITE_CHECK_MARK for reaction in reactions)
        except SlackApiError as e:
            print(f"[{self.get_current_time()}] Ошибка при проверке реакций: {e.response['error']}")
            return False

    def get_user_info(self, user_id):
        """Возвращает реальное имя пользователя по его ID"""
        try:
            response = self.bot_client.users_info(user=user_id)
            if response["ok"]:
                return response["user"]["real_name"]
            else:
                return "Ошибка API: " + response["error"]
        except SlackApiError as e:
            return "Ошибка API: " + e.response["error"]

    def get_message_text(self, channel_id, message_ts):
        """Возвращает текст сообщения по его ID и ID канала"""
        try:
            response = self.user_client.conversations_history(channel=channel_id, latest=message_ts, inclusive=True, limit=1)
            messages = response["messages"]
            if messages:
                return messages[0].get("text", "Неизвестный текст")
            else:
                return "Неизвестный текст"
        except SlackApiError as e:
            print(f"[{self.get_current_time()}] Ошибка при получении текста сообщения: {e.response['error']}")
            return "Неизвестный текст"

    def handle_existing_reaction(self, channel_id, message):
        """Обрабатывает существующие сообщения с реакцией WHITE_CHECK_MARK"""
        message_id = message["ts"]
        message_author_id = message.get("user", "Неизвестный автор")
        message_author_name = self.get_user_info(message_author_id)

        if message_id in self.deleted_messages or message_id in self.messages_under_review:
            return

        message_text = message.get("text", "Неизвестный текст")
        print(f"[{self.get_current_time()}] Найдено сообщение с реакцией {WHITE_CHECK_MARK} в сообщении с ID {message_id}. Автор сообщения: {message_author_name}. Текст сообщения: '{message_text}'. Запуск таймера на 5 секунд.")
        self.messages_under_review.add(message_id)
        
        time.sleep(5)

        print(f"[{self.get_current_time()}] Проверка реакции на сообщение с ID {message_id} после задержки.")
        
        if not self.check_white_check_mark_reaction(channel_id, message_id):
            print(f"[{self.get_current_time()}] Реакция на сообщение с ID {message_id} не найдена после задержки, поэтому сообщение не удалено.")
            self.messages_under_review.remove(message_id)
            return

        try:
            response = self.user_client.chat_delete(channel=channel_id, ts=message_id)
            if response["ok"]:
                print(f"[{self.get_current_time()}] Сообщение с ID {message_id} удалено из-за реакции {WHITE_CHECK_MARK}.")
                self.deleted_messages.add(message_id)
            else:
                print(f"[{self.get_current_time()}] Не удалось удалить сообщение с ID {message_id} из-за реакции {WHITE_CHECK_MARK}. Ошибка: {response['error']}")
        except SlackApiError as e:
            print(f"[{self.get_current_time()}] Ошибка: {e.response['error']}")

        self.messages_under_review.remove(message_id)

    def handle_socket_mode_request(self, client: SocketModeClient, req: SocketModeRequest):
        """Обработчик событий, приходящих через Socket Mode"""
        event_data = req.payload.get("event", {})
        
        # Проверяем, что событие относится к добавлению реакции и что реакция является WHITE_CHECK_MARK
        if event_data.get("type") != REACT_ADDED or event_data.get("reaction") != WHITE_CHECK_MARK:
            req.ack()
            return

        channel_id = event_data["item"]["channel"]
        message_id = event_data["item"]["ts"]
        message_author_id = event_data.get("item_user", "Неизвестный автор")
        message_author_name = self.get_user_info(message_author_id)
        reaction_user_id = event_data["user"]
        reaction_user_name = self.get_user_info(reaction_user_id)

        if message_id in self.deleted_messages or message_id in self.messages_under_review:
            req.ack()
            return

        message_text = self.get_message_text(channel_id, message_id)
        print(f"[{self.get_current_time()}] Найдено сообщение с реакцией {WHITE_CHECK_MARK} в сообщении с ID {message_id}. Автор сообщения: {message_author_name}. Текст сообщения: '{message_text}'. Реакцию добавил: {reaction_user_name}. Запуск таймера на 5 секунд.")
        self.messages_under_review.add(message_id)
        
        time.sleep(5)

        print(f"[{self.get_current_time()}] Проверка реакции на сообщение с ID {message_id} после задержки.")
        
        if not self.check_white_check_mark_reaction(channel_id, message_id):
            print(f"[{self.get_current_time()}] Реакция на сообщение с ID {message_id} не найдена после задержки, поэтому сообщение не удалено.")
            self.messages_under_review.remove(message_id)
            req.ack()
            return

        try:
            response = self.user_client.chat_delete(channel=channel_id, ts=message_id)
            if response["ok"]:
                print(f"[{self.get_current_time()}] Сообщение с ID {message_id} удалено из-за реакции {WHITE_CHECK_MARK}.")
                self.deleted_messages.add(message_id)
            else:
                print(f"[{self.get_current_time()}] Не удалось удалить сообщение с ID {message_id} из-за реакции {WHITE_CHECK_MARK}. Ошибка: {response['error']}")
        except SlackApiError as e:
            print(f"[{self.get_current_time()}] Ошибка: {e.response['error']}")

        self.messages_under_review.remove(message_id)
        req.ack()

    def check_existing_reactions(self):
        """Проверяет существующие сообщения на наличие реакции WHITE_CHECK_MARK"""
        channels = self.get_channels()
        for channel_id in channels:
            try:
                response = self.user_client.conversations_history(channel=channel_id, limit=100)  # limit может быть увеличен, если необходимо
                messages = response["messages"]
                for message in messages:
                    if "reactions" in message:
                        for reaction in message["reactions"]:
                            if reaction["name"] == WHITE_CHECK_MARK:
                                self.handle_existing_reaction(channel_id, message)
            except SlackApiError as e:
                print(f"[{self.get_current_time()}] Ошибка при проверке истории сообщений в канале {channel_id}: {e.response['error']}")

    def run(self):
        """Запускает бота"""
        self.broadcast_message("Будет чисто")
        self.check_existing_reactions()  # проверяем существующие реакции
        self.socket_mode_client.socket_mode_request_listeners.append(self.handle_socket_mode_request)
        self.socket_mode_client.connect()

        while True:
            time.sleep(1)

if __name__ == "__main__":
    try:
        bot = SlackBot()
        bot.run()
    except KeyboardInterrupt as e:
        pass
