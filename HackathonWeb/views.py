from django.http import FileResponse, Http404, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from django.core.cache import cache
from django.conf import settings
from . import main_file_processing
from .models import UploadedFile
import re
import os

def index(request):
    return render(request, 'index.html')

def yt_menu(request):
    if request.method == 'POST':
            cache.clear()
            link = request.POST['youtube_link']
            print(link)
    return render(request, 'yt_menu.html')

def yt_menu_download(request):
    data = {'title': 'Пустой запрос?'}
    if request.method == 'POST':
        try:
            cache.clear()
            link = request.POST['youtube_link']
            main_file_processing.main(link)
            a = r'(?:youtu\.be\/|watch\?v=)([a-zA-Z0-9_-]{11})'
            title = re.search(a, link).group(1)
            data = {
                'title' : title
            }
        except Exception as e:
            print(e)
        return render(request, 'yt_menu_download.html', data)

def drag_n_drop_menu_download(request):
    data = {'title': 'Пустой запрос?'}
    try:
        cache.clear()
        filepath = request.session.get('filepath')
        link = filepath
        title = filepath.split('/')[1]
        main_file_processing.main(link)
        data = {
            'title': title
        }
    except Exception as e:
        print(e)
    return render(request, 'drag_n_drop_menu_download.html', data)

def drag_n_drop_menu(request):
    return render(request, 'drag_n_drop_menu.html')

def yt_downloader(request):
    return render(request, 'yt_menu_download.html')

def download_file(request, file_name):
    file_path = os.path.join(settings.BASE_DIR, f'uploads/{file_name}/{file_name}.pdf')
    # Проверяем, существует ли файл
    if os.path.exists(file_path):
        # Отправляем файл
        return FileResponse(open(file_path, 'rb'), as_attachment=True, filename=f'{file_name}.pdf')
    else:
        raise Http404("Файл не найден")

@csrf_exempt
def upload_file(request):
    if request.method == 'POST' and request.FILES.get('file'):
        uploaded_file = request.FILES['file']

        # Сохраняем файл
        file_instance = UploadedFile(file=uploaded_file)
        file_instance.save()
        filepath = file_instance.get_filepath()
        request.session['filepath'] = filepath
        # Возвращаем успешный ответ
        return JsonResponse({'message': 'Файл успешно загружен', 'file_url': file_instance.file.url}, status=200)

    return JsonResponse({'message': 'Ошибка загрузки файла'}, status=400)