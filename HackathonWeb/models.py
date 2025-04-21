from django.db import models
from django.utils.text import slugify
import string
import random
import os

def generate_unique_filename(filename):
    # Извлекаем название файла без расширения
    base_name, ext = os.path.splitext(filename)
    # Генерируем случайный суффикс, чтобы избежать совпадений
    random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
    unique_name = f"{slugify(base_name)}_{random_suffix}{ext}"  # Формируем уникальное имя файла
    return unique_name.split('.')

def file_upload_path(instance, filename):
    # Генерируем путь с учетом имени файла
    os.makedirs('uploads', exist_ok=True)
    generated_filename = generate_unique_filename(filename=filename)
    while generated_filename[0] in os.listdir('uploads'):
        generated_filename = generate_unique_filename(filename=filename)

    folder_name = f"{generated_filename[0]}"  # Название папки будет основано на имени файла без расширения
    filename = generated_filename[0] + '.' + generated_filename[1]
    return os.path.join('uploads', folder_name, filename)

class UploadedFile(models.Model):
    file = models.FileField(upload_to=file_upload_path)  # Используем динамический путь
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'HackathonWeb'

    def get_filepath(self):
        return str(self.file)

    def __str__(self):
        return self.file.name