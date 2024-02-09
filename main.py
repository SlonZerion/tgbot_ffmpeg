import os, zipfile, shutil
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ContentType
from aiogram import Bot, Dispatcher, types
from aiogram.dispatcher import filters
from utils import *
from config import *

from loguru import logger
logger.add('log.log', format="{time} {level} {message}", level="INFO")


class FileProcessing(StatesGroup):
    waiting_for_files = State()
    waiting_for_number_of_copies = State()

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())


# Обработка фото
@dp.message_handler(content_types=types.ContentType.PHOTO, state=None)
async def handle_photo(message: types.Message, state: FSMContext):
    await state.update_data(photo_file_id=message.photo[-1].file_id)
    await FileProcessing.waiting_for_number_of_copies.set()
    await message.reply("Теперь отправьте мне число уникализированных экземпляров фото.")

# Обработка видео
@dp.message_handler(content_types=types.ContentType.VIDEO, state=None)
async def handle_video(message: types.Message, state: FSMContext):
    await state.update_data(video_file_id=message.video.file_id)
    await FileProcessing.waiting_for_number_of_copies.set()
    await message.reply("Теперь отправьте мне число уникализированных экземпляров видео.")

# Обработка zip-архива
@dp.message_handler(content_types=types.ContentType.DOCUMENT, state=None)
async def handle_document(message: types.Message, state: FSMContext):
    file_id = message.document.file_id
    file_name = message.document.file_name

    # Проверка на zip-архив
    if message.document.mime_type == "application/zip":
        await state.update_data(zip_file_id=file_id)
        await message.reply("Теперь отправьте мне число уникализированных экземпляров для каждого файла из архива.")

    # Проверка на документы .jpg или .mp4
    elif file_name.lower().endswith(('.png', '.jpg', '.jpeg', '.mp4')):
        # Сохранение ID файла в зависимости от его типа
        if file_name.endswith(('.png', '.jpg', '.jpeg')):
            await state.update_data(photo_file_id=file_id)            
            await message.reply("Теперь отправьте мне число уникализированных экземпляров фото.")
        elif file_name.lower().endswith('.mp4'):
            await state.update_data(video_file_id=file_id)
            await message.reply("Теперь отправьте мне число уникализированных экземпляров видео.")
    else:
        await message.answer("Пожалуйста, отправьте zip-архив, фото или видео.")
    await FileProcessing.waiting_for_number_of_copies.set()


# Обработка Яндекс Диска
YANDEX_DISK_REGEXP = r"https://disk\.yandex\.ru/d/[a-zA-Z0-9_-]+"
@dp.message_handler(filters.Regexp(YANDEX_DISK_REGEXP), state=None)
async def handle_yandex_disk_links(message: types.Message, state: FSMContext):
    await state.update_data(url_yandex_disk=message.text)
    await FileProcessing.waiting_for_number_of_copies.set()
    await message.reply("Теперь отправьте мне число уникализированных экземпляров файлов из Яндекс Диска.")

# Обработка Google Disk
GOOGLE_DISK_REGEXP = r"https://disk\.google\.ru/d/[a-zA-Z0-9_-]+"
@dp.message_handler(filters.Regexp(GOOGLE_DISK_REGEXP), state=None)
async def handle_google_disk_links(message: types.Message, state: FSMContext):
    await state.update_data(url_google_disk=message.text)
    await FileProcessing.waiting_for_number_of_copies.set()
    await message.reply("Google Disk в разработке.")

# обработка и отправка файлов после ввода числа копий
@dp.message_handler(lambda message: message.text.isdigit(), state=FileProcessing.waiting_for_number_of_copies)
async def handle_number(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    num_copies = int(message.text) # достаем введеное пользователем количество копий 
    random_name = random_string() # генерируем рандомную строку-маркер для конкретного пользователя
    TMP_DIR="TMP_DIR_" + random_name
    
    if not os.path.exists(TMP_DIR):
        os.makedirs(TMP_DIR)

    try:
        # обработка zip-архива
        if 'zip_file_id' in user_data:
            sent_message = await message.reply("Обработка архива началась. Пожалуйста, подождите...")

            file_id = user_data['zip_file_id']
            file_info = await bot.get_file(file_id)
            await file_info.download(destination_file=f"archive_{random_name}.zip")

            with zipfile.ZipFile(f"archive_{random_name}.zip", 'r') as zip_ref:
                zip_ref.extractall(f"{TMP_DIR}/")
                
            os.remove(f"archive_{random_name}.zip")
            
            archive_contents = os.listdir(f"{TMP_DIR}/")
            output_files = []
            for file in archive_contents:
                await bot.edit_message_text(chat_id=message.chat.id, message_id=sent_message.message_id, text=f"Обработка {archive_contents.index(file)+1}-го файла из архива...")
                input_file_name = os.path.join(TMP_DIR, file)
                for i in range(num_copies):
                    if input_file_name.endswith(('.mp4', '.MP4', '.mov')):
                        output_file_name = os.path.join(TMP_DIR, f"{i}_{file}")
                        unique_video(input_file_name, output_file_name) 
                        output_files.append(output_file_name)
                    elif input_file_name.endswith(('.jpg', '.png', '.jpeg')):
                        output_file_name = os.path.join(TMP_DIR, f"{i}_{file}")
                        unique_photo(input_file_name, output_file_name) 
                        output_files.append(output_file_name)
                    else:
                        await message.reply(f"Файл {file} из архива имеет неподдерживаемый формат и будет пропущен.")
        
        # обработка Яндекс Диска
        if 'url_yandex_disk' in user_data:
            await message.reply("Обработка файлов Яндекс Диска началась. Пожалуйста, подождите...")

            num_copies = int(message.text) # получаем количество копий
            url_yandex_disk = user_data['url_yandex_disk'] # достаем ссылку на яндекс диск из прошлого сообщения
            download_yandex_disk(url_yandex_disk, f"archive_{random_name}.zip") # скачиваем файлы из яндекс диска


            with zipfile.ZipFile(f"archive_{random_name}.zip", 'r', compression=zipfile.ZIP_DEFLATED) as zip_ref:
                zip_ref.extractall(f"{TMP_DIR}/")

            inner_folder_path = os.path.join(TMP_DIR, os.listdir(TMP_DIR)[0])
            for filename in os.listdir(inner_folder_path):
                os.rename(os.path.join(inner_folder_path, filename), os.path.join(TMP_DIR, filename))

            os.rmdir(inner_folder_path)
            os.remove(f"archive_{random_name}.zip")
            

            
            # archive_contents = os.listdir(f"{TMP_DIR}/")
            # output_files = []
            # for file in archive_contents:
            #     await message.reply(f"Обработка {archive_contents.index(file)+1}-го файла из Яндекс Диска...")
            #     file_path = os.path.join(TMP_DIR, file)
            #     print(file)
            #     print(file_path)
                
            #     for i in range(num_copies):
            #         if file_path.endswith(('.mp4', '.MP4', '.mov')):
            #             for i in ('.mp4', '.MP4', '.mov'):
            #                 file.replace(i,'')
            #             unique_name = os.path.join(TMP_DIR, f"{file}_{i}.mp4")
            #             command = [
            #                 'ffmpeg',
            #                 '-i', file_path,
            #                 '-vf', f'eq=brightness={random.uniform(-0.1, 0.1)}',
            #                 unique_name
            #             ]
            #             subprocess.run(command)
            #             output_files.append(unique_name)

            #         elif file_path.endswith(('.jpg', '.png', '.jpeg')):
            #             for i in ('.jpg', '.png', '.jpeg'):
            #                 file.replace(i,'')
            #             unique_name = os.path.join(TMP_DIR, f"{file}_{i}.png")
            #             command = [
            #                 'ffmpeg',
            #                 '-i', file_path,
            #                 '-vf', f'eq=brightness={random.uniform(-0.1, 0.1)}',
            #                 unique_name
            #             ]
            #             subprocess.run(command)
            #             output_files.append(unique_name)
            #         else:
            #             await message.reply(f"Файл {file} из архива имеет неподдерживаемый формат и будет пропущен.")
            # del user_states[user_id]


        # обработка видео
        elif 'video_file_id' in user_data:
            sent_message = await message.reply("Скачиваю видео. Пожалуйста, подождите...")
            input_file_name = os.path.join(TMP_DIR, f"{random_name}_original.mp4")
            file_id = await bot.get_file(user_data['video_file_id'])
            
            await bot.download_file(file_id.file_path, input_file_name)
            
            output_files = []
            for i in range(num_copies):
                await bot.edit_message_text(chat_id=message.chat.id, message_id=sent_message.message_id, text=f"Обработка {i+1}-го видео...")
                output_file_name = os.path.join(TMP_DIR, f"{random_name}_{i+1}.mp4")
                unique_video(input_file_name, output_file_name)
                output_files.append(output_file_name)


        # обработка фото
        elif 'photo_file_id' in user_data:
            sent_message = await message.answer("Скачиваю фото. Пожалуйста, подождите...")
            input_file_name = os.path.join(TMP_DIR, f"{random_name}_original{PHOTO_OUTPUT_FORMAT}")
            file = await bot.get_file(user_data['photo_file_id'])
            
            await bot.download_file(file.file_path, input_file_name)
            
            # Уникализировать фотографии
            output_files = []
            for i in range(num_copies):
                await bot.edit_message_text(chat_id=message.chat.id, message_id=sent_message.message_id, text=f"Обработка {i+1}-го фото...")
                output_file_name = os.path.join(TMP_DIR, f"{random_name}_{i+1}{PHOTO_OUTPUT_FORMAT}")
                unique_photo(input_file_name, output_file_name) 
                output_files.append(output_file_name)




        await bot.edit_message_text(chat_id=message.chat.id, message_id=sent_message.message_id, text=f"✅ Обработка завершена!")

        shutil.make_archive(random_name, 'zip', TMP_DIR)
        await message.answer(f"Отправляю файл...\n\nРазмер файла: {round(int(os.path.getsize(random_name+'.zip'))/1024/1024, 1)} Мбайт")
        
        # Отправить архив пользователю
        with open(random_name+'.zip', 'rb') as archive_file:
            await message.answer_document(archive_file)
    except Exception as ex:
        await message.answer(f"Ошибка {ex}")

    finally:
        try:
            # Очистить файлы
            for file in output_files:
                os.remove(file)
        except:
            pass
        try:
            await state.finish()
        except:
            pass
        # os.remove(user_states[user_id]['photo_file_id'])
        try:
            os.remove(random_name+'.zip')
        except:
            pass
        try:
            shutil.rmtree(TMP_DIR)
        except:
            pass



@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    await message.reply("Это бот для уникализации фото и видео.\nВы можете отправить:\n\n📷 Фото\n📼 Видео\n📄 Документы в формате .png .jpeg .jpg .mp4 \n🗄 Zip-Архив\n🔗 Ссылку на Яндекс диск\n🔗 Ссылку на Google Disk")



if __name__ == '__main__':
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)
