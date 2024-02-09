import os
import string, random
import subprocess
import zipfile
import requests
from urllib.parse import urlencode
from PIL import Image


from loguru import logger
logger.add('log.log', format="{time} {level} {message}", level="INFO")




def random_string(length=10):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choices(characters, k=length))


def download_yandex_disk(url, random_name):
    base_url = 'https://cloud-api.yandex.net/v1/disk/public/resources/download?'
    final_url = base_url + urlencode(dict(public_key=url))
    response = requests.get(final_url)
    download_url = response.json()['href']
    download_response = requests.get(download_url)
    with open(random_name, 'wb') as f:
        f.write(download_response.content)


def random_between_and_round(a, b, round_value=6):
    if round_value == 0:
        return round(random.uniform(a, b))
    return round(random.uniform(a, b), round_value)


def unique_video(input_file, output_file):
    hue_value = random_between_and_round(-4, 4, round_value=1)
    noise_value = random_between_and_round(20, 40, round_value=1)
    brightness_value = random_between_and_round(-0.05, 0.05)
    rotation_value = random_between_and_round(-0.0849, 0.0849)
    crop_value = random_between_and_round(10, 20, round_value=0)
    speed_factor = random_between_and_round(0.9, 1.1)
    audio_volume = random_between_and_round(0.8, 1.2, 2)
    audio_pitch = random_between_and_round(0.9, 1.05, 2)
    # video_bitrate = random_between_and_round(500, 800, 2)
    # audio_bitrate = random_between_and_round(96, 192, 2)
    # blur_x = random.randint(0, 200 - 100)
    # blur_y = random.randint(0, 200 - 100)
    # command = (  # 
    #     f"ffmpeg -i {input_file} -filter_complex "
    #     f'"[0:v]setpts={round(1/speed_factor)}*PTS,eq=brightness={brightness_value},hue=h={hue_value},rotate={rotation_value},crop=in_w-{crop_value}:in_h-{crop_value},noise=alls={noise_value}:allf=t+u[v],split=2[base][blur];'
    #     f'[blur]crop=100:100:{blur_x}:{blur_y},gblur=sigma=20[blurred];[base][blurred]overlay={blur_x}:{blur_y}[v];[0:a]atempo={speed_factor},volume={audio_volume},asetrate={44100*audio_pitch}[a]" '
    #     '-map "[v]" -map "[a]" '
    #     f"-b:v {video_bitrate}k "
    #     f"-b:a {audio_bitrate}k "
    #     f"-map_metadata -1 "
    #     f"{output_file}"
    #     # "-map_metadata -1",
    # )

    command = (  
        f"ffmpeg -i {input_file} -filter_complex "
        
        f'"[0:v]setpts={round(1/speed_factor)}*PTS,eq=brightness={brightness_value},hue=h={hue_value},rotate={rotation_value},crop=in_w-{crop_value}:in_h-{crop_value},noise=alls={noise_value}:allf=t+u[v];[0:a]atempo={speed_factor},volume={audio_volume},asetrate={44100*audio_pitch}[a]" '
        '-map "[v]" -map "[a]" '
        f"-map_metadata -1 "
        f"{output_file}"
        # "-map_metadata -1",
    )

    logger.info(command)
    subprocess.run(command, shell=True, check=True)


def get_image_size(image_path):
    with Image.open(image_path) as img:
        return img.size  # Возвращает кортеж (ширина, высота)
    
def unique_photo(input_file, output_file):
    # Получение размера изображения
    width, height = get_image_size(input_file)
    print(width, height)
    # Генерация случайных координат для блюра
    height_blur = random.randint(100,200)
    weight_blur = random.randint(100,200)
    max_x = max(0, width - 100)
    max_y = max(0, height - 100)
    blur_x = random.randint(0, max_x)
    blur_y = random.randint(0, max_y)
    hue_value = random_between_and_round(-4, 4, round_value=1)
    noise_value = random_between_and_round(20, 40, round_value=1)
    brightness_value = random_between_and_round(-0.05, 0.05)
    rotation_value = random_between_and_round(-0.0349, 0.0349)
    colortemperature_value = random_between_and_round(5000, 8500, round_value=1)
    crop_value = random_between_and_round(10, 20, round_value=0)

    command = (
        f'ffmpeg -y -i {input_file} '
        f'-filter_complex "[0:v]split=2[base][blur];[blur]gblur=sigma=10,crop={height_blur}:{weight_blur}:{blur_x}:{blur_y}[blurred];[base][blurred]overlay={blur_x}:{blur_y},'
        f'colortemperature={colortemperature_value}:pl=1,noise=alls={noise_value}:allf=t+u,'
        f'eq=brightness={brightness_value},hue=h={hue_value},rotate={rotation_value},crop=in_w-{crop_value}:in_h-{crop_value}" '
        f'-map_metadata -1 '
        f'{output_file}'
    )
    logger.info(command)

    subprocess.run(command, shell=True, check=True)


if __name__ == '__main__':
    unique_photo('input.jpg', 'ffmpeg.jpg')

