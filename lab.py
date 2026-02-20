import asyncio
import edge_tts
import random
import time
import pygame
from openai import OpenAI

client = OpenAI(api_key="KEY")
chat_history = [
    {"role": "system", "content": "Ти дворецький Айс. Відповідай ввічливо, чітко й по суті. Не відходь від ролі. Весь текст українською. Спілкування повинно бути живим, тому не використовуй того, що не було б сказано реальною людиною."}
]

audio_cache = {}

async def say_message_async(message):
    print(f"Айс: {message}")

    if message in audio_cache:
        file_name = audio_cache[message]
    else:
        file_name = f"voice_{int(time.time())}_{random.randint(0, 1000)}.mp3"
        tts = edge_tts.Communicate(text=message, voice="uk-UA-OstapNeural", rate="+5%")
        await tts.save(file_name)
        audio_cache[message] = file_name

    pygame.mixer.init()
    pygame.mixer.music.load(file_name)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        await asyncio.sleep(0.1)

def say_message(message):
    asyncio.run(say_message_async(message))

async def ask_gpt_async(user_message):
    chat_history.append({"role": "user", "content": user_message})
    notify_task = asyncio.create_task(asyncio.sleep(10))
    loop = asyncio.get_event_loop()
    reply_task = loop.run_in_executor(None, lambda: client.chat.completions.create(
        model="gpt-4o-mini",
        messages=chat_history[-10:]
    ).choices[0].message.content.strip())

    done, pending = await asyncio.wait(
        [reply_task, notify_task],
        return_when=asyncio.FIRST_COMPLETED
    )

    if notify_task in done:
        say_message("Секунду, сер, думаю над відповіддю...")

    reply = await reply_task
    chat_history.append({"role": "assistant", "content": reply})
    return reply

def ask_gpt(user_message):
    return asyncio.run(ask_gpt_async(user_message))

def listen_command():
    return input("Введіть команду або запит: ")

def do_this_command(message):
    msg = message.lower()

    if msg in ["привіт", "хай"]:
        say_message("Добридень, сер!")
    elif msg in ["як справи", "як ти", "як справи?"]:
        say_message("Дякую, що запитали! У мене все добре. Як можу Вам допомогти сьогодні?")
    elif msg in ["час", "тайм"]:
        current_time = time.strftime("%H:%M:%S", time.localtime())
        say_message(f"На годиннику {current_time}")
    elif msg in ["дата"]:
        current_date = time.strftime("%d.%m.%Y", time.localtime())
        say_message(f"Ви отримали відповідь {current_date}, тобто сьогодні.")
    elif msg in ["прощавай", "вихід"]:
        say_message("До зустрічі, сер!")
        exit()
    else:
        reply = ask_gpt(message)
        for part in reply.split("\n"):
            if part.strip():
                say_message(part.strip())

if __name__ == '__main__':
    print("Айс до ваших послуг.")
    print("Готові команди для вашої зручності й перевірки системи: Привіт, Як справи, Час, Дата, Вихід/Прощавай")
    print("Натомість готовий відповісти на будь-яке питання, сер.")
    while True:
        command = listen_command()
        do_this_command(command)