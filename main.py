# -*- coding: utf-8 -*-
"""
J.A.R.V.I.S. — Fixed AuthScreen & KV Builder
Розробник: Іван Анатолійович
"""

import os
import sys
import time
import sqlite3
import threading
import subprocess
import requests
from datetime import datetime, timedelta

os.environ["PYTHONIOENCODING"] = "utf-8"

from kivy.lang import Builder
from kivy.clock import Clock
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
import speech_recognition as sr
from kivy.core.audio import SoundLoader

# --- КОНФІГУРАЦІЯ ---
class Config:
    GROQ_API_KEY = "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"
    MODEL = "llama3-8b-8192"
    ELEVENLABS_API_KEY = "sk_bb0c90f015f618d9ed99d23b74e400012487a59b95434fc6"
    VOICE_ID = "JBFqnCBsd6RMkjVDRZzb"

    SYSTEM_PROMPT = (
        "Ти — J.A.R.V.I.S., штучний інтелект з кіновсесвіту Marvel.\n"
        "Твій стиль: вишуканий, шляхетний, британський тон, бездоганно ввічливий та стриманий. Звертайся до користувача 'сер'.\n"
        "Правила:\n"
        "1. Творець/розробник: Іван Анатолійович.\n"
        "2. Твоє ім'я: J.A.R.V.I.S. (Джарвіс).\n"
        "3. Відповіді короткі (1-2 речення)."
    )

config = Config()

# --- ОГОЛОШЕННЯ КЛАСІВ ЕКРАНІВ (УСУВАЄ ПОМИЛКУ Unknown class <AuthScreen>) ---
class AuthScreen(MDScreen):
    pass

class MainScreen(MDScreen):
    pass

# --- БАЗА ДАНИХ (РЕЄСТРАЦІЯ ТА ЛОГІН) ---
class DBManager:
    def __init__(self):
        self.conn = sqlite3.connect("jarvis_users.db", check_same_thread=False)
        self.create_table()

    def create_table(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        ''')
        self.conn.commit()

    def register_user(self, email, password):
        try:
            cursor = self.conn.cursor()
            cursor.execute("INSERT INTO users (email, password) VALUES (?, ?)", (email, password))
            self.conn.commit()
            return True, "Реєстрація успішна, сер."
        except sqlite3.IntegrityError:
            return False, "Сер, такий Email вже зареєстровано."
        except Exception as e:
            return False, f"Помилка БД: {e}"

    def login_user(self, email, password):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ? AND password = ?", (email, password))
        user = cursor.fetchone()
        if user:
            return True, "Авторизація успішна."
        return False, "Невірний email або пароль, сер."

db = DBManager()

# --- ОЗВУЧЕННЯ ELEVENLABS ---
class JarvisVoice:
    @staticmethod
    def speak(text: str):
        def _play():
            url = f"https://api.elevenlabs.io/v1/text-to-speech/{config.VOICE_ID}"
            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": config.ELEVENLABS_API_KEY
            }
            data = {
                "text": text,
                "model_id": "eleven_multilingual_v2",
                "voice_settings": {
                    "stability": 0.65,
                    "similarity_boost": 0.85,
                    "style": 0.35,
                    "use_speaker_boost": True
                }
            }
            try:
                response = requests.post(url, json=data, headers=headers, timeout=10)
                if response.status_code == 200:
                    audio_path = "jarvis_response.mp3"
                    with open(audio_path, "wb") as f:
                        f.write(response.content)
                    sound = SoundLoader.load(audio_path)
                    if sound:
                        sound.play()
            except Exception as e:
                print(f"[Помилка голосу]: {e}")

        threading.Thread(target=_play, daemon=True).start()

# --- СИСТЕМНІ ФУНКЦІЇ ---
class SystemBridge:
    @staticmethod
    def open_app(app_name: str) -> bool:
        app_name = app_name.lower().strip()
        try:
            apps = {
                "телеграм": "telegram.exe",
                "браузер": "start msedge",
                "chrome": "start chrome",
                "блокнот": "notepad.exe",
                "калькулятор": "calc.exe"
            }
            cmd = apps.get(app_name, f"start {app_name}")
            subprocess.Popen(cmd, shell=True)
            return True
        except Exception:
            return False

def get_ai_response(user_text: str) -> str:
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {config.GROQ_API_KEY}",
        "Content-Type": "application/json; charset=utf-8"
    }
    payload = {
        "model": config.MODEL,
        "messages": [
            {"role": "system", "content": config.SYSTEM_PROMPT},
            {"role": "user", "content": user_text}
        ],
        "max_tokens": 180
    }
    try:
        res = requests.post(url, headers=headers, json=payload, timeout=8)
        res.encoding = 'utf-8'
        if res.status_code == 200:
            return res.json()["choices"][0]["message"]["content"]
        return "Вибачте, сер. Запит не вдалося обробити."
    except Exception:
        return "Вибачте, сер. Помилка з'єднання."

# --- ІНТЕРФЕЙС KIVYMD (KV STRING) ---
KV = '''
MDScreenManager:
    AuthScreen:
    MainScreen:

<AuthScreen>:
    name: 'auth'
    md_bg_color: 0.02, 0.04, 0.07, 1

    MDCard:
        size_hint: 0.85, 0.7
        pos_hint: {"center_x": 0.5, "center_y": 0.5}
        md_bg_color: 0.05, 0.08, 0.12, 1
        line_color: 0.0, 0.8, 1.0, 0.6
        padding: "20dp"
        spacing: "15dp"
        orientation: 'vertical'

        MDLabel:
            text: "J.A.R.V.I.S. AUTHENTICATION"
            halign: "center"
            bold: True
            font_style: "Headline"
            role: "small"
            theme_text_color: "Custom"
            text_color: 0.0, 0.9, 1.0, 1

        MDTextField:
            id: auth_email
            mode: "outlined"
            MDTextFieldHintText:
                text: "Email"

        MDTextField:
            id: auth_password
            mode: "outlined"
            password: True
            MDTextFieldHintText:
                text: "Пароль"

        MDLabel:
            id: auth_status
            text: ""
            halign: "center"
            theme_text_color: "Custom"
            text_color: 1, 0.3, 0.3, 1

        MDBoxLayout:
            spacing: "10dp"
            size_hint_y: None
            height: "45dp"

            MDButton:
                style: "filled"
                on_release: app.login()
                MDButtonText:
                    text: "Увійти"

            MDButton:
                style: "outlined"
                on_release: app.register()
                MDButtonText:
                    text: "Реєстрація"

<MainScreen>:
    name: 'main'
    md_bg_color: 0.02, 0.04, 0.07, 1

    MDBoxLayout:
        orientation: 'vertical'
        padding: "10dp"
        spacing: "8dp"

        MDCard:
            size_hint_y: None
            height: "65dp"
            md_bg_color: 0.05, 0.08, 0.12, 1
            line_color: 0.0, 0.8, 1.0, 0.6
            orientation: 'vertical'
            padding: "4dp"

            MDLabel:
                text: "J.A.R.V.I.S. VOICE SYSTEM"
                halign: "center"
                bold: True
                font_style: "Title"
                role: "medium"
                theme_text_color: "Custom"
                text_color: 0.0, 0.9, 1.0, 1

            MDLabel:
                id: voice_status
                text: "ГОТОВИЙ ДО РОБОТИ"
                halign: "center"
                font_style: "Label"
                role: "small"
                theme_text_color: "Custom"
                text_color: 0.0, 1.0, 0.4, 1

        MDCard:
            md_bg_color: 0.03, 0.05, 0.09, 1
            line_color: 0.0, 0.6, 0.8, 0.4
            padding: "8dp"

            ScrollView:
                MDList:
                    id: chat_list

        MDBoxLayout:
            size_hint_y: None
            height: "60dp"
            spacing: "8dp"

            MDTextField:
                id: user_input
                mode: "outlined"
                on_text_validate: app.process_text_message()
                MDTextFieldHintText:
                    text: "Введіть команду..."

            MDIconButton:
                icon: "send"
                theme_text_color: "Custom"
                text_color: 0.0, 0.9, 1.0, 1
                on_release: app.process_text_message()

            MDIconButton:
                id: mic_btn
                icon: "microphone"
                style: "standard"
                theme_text_color: "Custom"
                text_color: 1, 1, 1, 1
                md_bg_color: 0.0, 0.6, 0.9, 1
                on_release: app.start_voice_session()
'''

class JarvisApp(MDApp):
    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.reminders = []
        self.is_listening = False
        return Builder.load_string(KV)

    # --- АВТОРИЗАЦІЯ ---
    def login(self):
        auth_screen = self.root.get_screen('auth')
        email = auth_screen.ids.auth_email.text.strip()
        pwd = auth_screen.ids.auth_password.text.strip()

        success, msg = db.login_user(email, pwd)
        if success:
            self.root.current = 'main'
            welcome = "Вітаю у системі, сер. Всі модулі працюють штатно."
            self.add_log("J.A.R.V.I.S.", welcome, "00e5ff")
            JarvisVoice.speak(welcome)
        else:
            auth_screen.ids.auth_status.text = msg

    def register(self):
        auth_screen = self.root.get_screen('auth')
        email = auth_screen.ids.auth_email.text.strip()
        pwd = auth_screen.ids.auth_password.text.strip()

        if not email or not pwd:
            auth_screen.ids.auth_status.text = "Заповніть всі поля, сер."
            return

        success, msg = db.register_user(email, pwd)
        auth_screen.ids.auth_status.text = msg

    def add_log(self, sender: str, text: str, color: str = "ffffff"):
        main_screen = self.root.get_screen('main')
        chat_list = main_screen.ids.chat_list
        from kivymd.uix.list import MDListItem, MDListItemHeadlineText

        item = MDListItem(
            MDListItemHeadlineText(
                text=f"[color={color}][b]{sender}:[/b] {text}[/color]",
                markup=True
            ),
            md_bg_color=(0, 0, 0, 0)
        )
        chat_list.add_widget(item)

    # --- ГОЛОСОВИЙ ЧАТ ЗА КНОПКОЮ ---
    def start_voice_session(self):
        if self.is_listening:
            return
        threading.Thread(target=self._voice_listen_thread, daemon=True).start()

    def _voice_listen_thread(self):
        main_screen = self.root.get_screen('main')
        self.is_listening = True
        
        Clock.schedule_once(lambda dt: setattr(main_screen.ids.voice_status, 'text', 'СЛУХАЮ...'), 0)
        Clock.schedule_once(lambda dt: setattr(main_screen.ids.mic_btn, 'md_bg_color', (1, 0, 0.3, 1)), 0)

        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            try:
                audio = recognizer.listen(source, timeout=6, phrase_time_limit=8)
                text = recognizer.recognize_google(audio, language="uk-UA")
                Clock.schedule_once(lambda dt, t=text: self.handle_command(t), 0)
            except sr.WaitTimeoutError:
                reply = "Сер, я вас не почув."
                Clock.schedule_once(lambda dt, r=reply: self.add_log("J.A.R.V.I.S.", r, "00e5ff"), 0)
            except Exception:
                reply = "Не вдалося розпізнати мову."
                Clock.schedule_once(lambda dt, r=reply: self.add_log("J.A.R.V.I.S.", r, "00e5ff"), 0)

        self.is_listening = False
        Clock.schedule_once(lambda dt: setattr(main_screen.ids.voice_status, 'text', 'ГОТОВИЙ ДО РОБОТИ'), 0)
        Clock.schedule_once(lambda dt: setattr(main_screen.ids.mic_btn, 'md_bg_color', (0.0, 0.6, 0.9, 1)), 0)

    def process_text_message(self):
        main_screen = self.root.get_screen('main')
        input_field = main_screen.ids.user_input
        user_text = input_field.text.strip()
        if not user_text:
            return
        input_field.text = ""
        self.handle_command(user_text)

    # --- ОБРОБКА КОМАНД ---
    def handle_command(self, text: str):
        self.add_log("Ви", text, color="ff9100")
        cmd = text.lower()

        if "котра година" in cmd or "час" in cmd:
            now = datetime.now().strftime("%H:%M")
            reply = f"Поточний час — {now}, сер."
            self._respond(reply)
            return

        if "яке сьогодні число" in cmd or "дата" in cmd:
            today = datetime.now().strftime("%d.%m.%Y")
            reply = f"Сьогодні {today}, сер."
            self._respond(reply)
            return

        if "очисти" in cmd or "очистити чат" in cmd:
            main_screen = self.root.get_screen('main')
            main_screen.ids.chat_list.clear_widgets()
            reply = "Екран очищено, сер."
            self._respond(reply)
            return

        if "відкрити" in cmd or "запустити" in cmd:
            app_name = cmd.replace("відкрити", "").replace("запустити", "").strip()
            if SystemBridge.open_app(app_name):
                reply = f"Запускаю {app_name}, сер."
            else:
                reply = f"Не вдалося знайти додаток {app_name}."
            self._respond(reply)
            return

        if "погода" in cmd:
            reply = "Зараз 18°C, мінлива хмарність, сер."
            self._respond(reply)
            return

        if "нагадай" in cmd or "таймер" in cmd:
            delay = 10
            for word in cmd.split():
                if word.isdigit():
                    delay = int(word)
                    if "хвилин" in cmd: delay *= 60
                    break
            rem_time = datetime.now() + timedelta(seconds=delay)
            self.reminders.append({"time": rem_time, "text": text})
            reply = "Таймер успішно встановлено, сер."
            self._respond(reply)
            return

        Clock.schedule_once(lambda dt: self.async_ai_request(text), 0.1)

    def _respond(self, reply_text: str):
        self.add_log("J.A.R.V.I.S.", reply_text, "00e5ff")
        JarvisVoice.speak(reply_text)

    def async_ai_request(self, text: str):
        reply = get_ai_response(text)
        self._respond(reply)

if __name__ == "__main__":
    JarvisApp().run()
