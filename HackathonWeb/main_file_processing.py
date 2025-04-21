from pytubefix import YouTube
from pytubefix.cli import on_progress
import whisper
import time
from mistralai import Mistral
import re
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.lib import colors
import json
import os
from pydub import AudioSegment
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("MISTRAL_KEY")

# Константы
FONT_PATH = 'static\\bolds\\Arial.ttf'
PAGE_WIDTH, PAGE_HEIGHT = letter
LEFT_MARGIN = 2*cm
RIGHT_MARGIN = 2*cm
TOP_MARGIN = 2*cm
BOTTOM_MARGIN = 2*cm
PARAGRAPH_WIDTH = PAGE_WIDTH - LEFT_MARGIN - RIGHT_MARGIN
LINE_SPACING = 1.5
FIRST_LINE_INDENT = 1.25*cm

def clean_text(text):
    """Очищаем текст от ненужных префиксов и форматирования"""
    text = re.sub(r'\*+', '', text)
    text = ' '.join(text.split())
    return text.strip()

def register_fonts():
    """Регистрируем шрифт"""
    try:
        pdfmetrics.registerFont(TTFont('ArialCyr', FONT_PATH))
    except:
        print(f"Ошибка при загрузке шрифта. Убедитесь, что файл {FONT_PATH} существует")

def create_styles():
    """Создаем стиль для текста"""
    styles = getSampleStyleSheet()
    
    # Стиль для заголовка
    styles.add(ParagraphStyle(
        name='Header1',
        parent=styles['Heading1'],
        fontName='ArialCyr',
        fontSize=18,
        leading=18*LINE_SPACING,
        alignment=1, 
        spaceAfter=12
    ))
    
    # Стиль для обычного текста
    styles.add(ParagraphStyle(
        name='NormalJustified',
        parent=styles['Normal'],
        fontName='ArialCyr',
        fontSize=12,
        leading=12*LINE_SPACING,
        alignment=4,  
        firstLineIndent=FIRST_LINE_INDENT,
        spaceAfter=6
    ))
    
    return styles

def process_line_content(line, in_table_mode):
    """Обрабатываем строку текста"""
    line = line.strip()
    
    if not line:
        return {'level': None, 'text': None, 'table_marker': False}
    
    if '```json' in line:
        return {'level': None, 'text': None, 'table_marker': True}
    if '```' in line:
        return {'level': None, 'text': None, 'table_marker': True}
    
    if in_table_mode:
        return {'level': None, 'text': None, 'table_content': line, 'table_marker': False}
    
    if line.startswith("#"):
        level = 1
        text = clean_text(line[line.find(' ')+1:])
    elif line.startswith("---"):
        level = None
        text = clean_text(line[3:])
    else:
        level = 0
        text = clean_text(line)
    
    return {'level': level, 'text': text, 'table_marker': False}

def create_table_style():
    """Создаем стиль для таблицы с автоматическим переносом текста"""
    return TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.white),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTNAME', (0, 1), (-1, -1), 'ArialCyr'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('LEADING', (0, 0), (-1, -1), 10*LINE_SPACING),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('WORDWRAP', (0, 0), (-1, -1), True)  
    ])

def draw_table(canvas, table_data, y_pos, page_height):
    """Рисуем таблицу с автоматическим переносом текста"""
    # Создаем стиль для текста в ячейках
    cell_style = ParagraphStyle(
        name='TableCell',
        fontName='ArialCyr',
        fontSize=10,
        leading=10*LINE_SPACING,
        alignment=0,  # left
        spaceBefore=2,
        spaceAfter=2
    )
    
    # Преобразуем текст в ячейках в Paragraph для переноса
    formatted_data = []
    for row in table_data:
        formatted_row = []
        for cell in row:
            formatted_row.append(Paragraph(cell, cell_style))
        formatted_data.append(formatted_row)
    
    # Рассчитываем ширину столбцов (50% на каждый столбец)
    col_widths = [PARAGRAPH_WIDTH * 0.5, PARAGRAPH_WIDTH * 0.5]
    
    table = Table(formatted_data, colWidths=col_widths)
    table.setStyle(create_table_style())
    
    # Рассчитываем высоту таблицы
    table.wrapOn(canvas, PARAGRAPH_WIDTH, page_height)
    table_height = table._height
    
    # Проверяем, помещается ли таблица на текущей странице
    if y_pos - table_height < BOTTOM_MARGIN:
        canvas.showPage()
        y_pos = page_height - TOP_MARGIN
    
    # Делаем таблицу по центру 
    table_x = (PAGE_WIDTH - table._width) / 2
    table.drawOn(canvas, table_x, y_pos - table_height)
    return y_pos - table_height - 12

def draw_paragraph(canvas, text, style, y_pos, width, max_height):
    """Рисуем абзац с учетом переноса страниц"""
    p = Paragraph(text, style)
    available_height = y_pos - BOTTOM_MARGIN
    paragraph_height = p.wrap(width, available_height)[1]
    
    if paragraph_height > available_height:
        canvas.showPage()
        y_pos = max_height - TOP_MARGIN
        paragraph_height = p.wrap(width, y_pos - BOTTOM_MARGIN)[1]
    
    p.drawOn(canvas, LEFT_MARGIN, y_pos - paragraph_height)
    return y_pos - paragraph_height

def txt_to_pdf(txt_filepath, pdf_filepath):
    """Функция преобразования TXT в PDF"""
    try:
        register_fonts()
        styles = create_styles()
        
        with open(txt_filepath, 'r', encoding='utf-8') as txt_file:
            lines = txt_file.readlines()

        c = canvas.Canvas(pdf_filepath, pagesize=letter)
        y_position = PAGE_HEIGHT - TOP_MARGIN
        in_table_mode = False
        table_content = []

        for line in lines:
            line_data = process_line_content(line, in_table_mode)
            
            if line_data.get('table_marker'):
                if '```json' in line:
                    in_table_mode = True
                    table_content = []
                elif '```' in line:
                    in_table_mode = False
                    if table_content:
                        try:
                            table_data = json.loads('\n'.join(table_content))
                            y_position = draw_table(c, table_data, y_position, PAGE_HEIGHT)
                        except json.JSONDecodeError as e:
                            print(f"Ошибка декодирования JSON таблицы: {e}")
                continue
            
            if in_table_mode:
                table_content.append(line_data.get('table_content', ''))
                continue
            
            if line_data['text'] is None:
                y_position -= 14
                continue

            if line_data['level'] == 1:
                style = styles['Header1']
            else:
                style = styles['NormalJustified']

            y_position = draw_paragraph(c, line_data['text'], style, 
                                      y_position, PARAGRAPH_WIDTH, PAGE_HEIGHT)

        c.save()
        print(f"Файл '{txt_filepath}' успешно преобразован в '{pdf_filepath}'")

    except FileNotFoundError:
        print(f"Ошибка: Файл '{txt_filepath}' не найден.")
    except Exception as e:
        print(f"Произошла ошибка: {e}")


def resume(text):
    model = "mistral-small-latest"
    client = Mistral(api_key=api_key)

    prompt = f"""
    Ты опытный суммаризатор текста, специализирующийся на создании конспектов в стиле лекций. Твоя задача - создать краткую и информативную сводку текста, отформатированную как конспект.

    Инструкции:

    1.  **Заголовок и Подзаголовок:** Начни с четкого заголовка, отражающего основную тему текста (например, "Неразгаданная тайна Старой Рязани", но не используй этот пример по умолчанию).  Добавь подзаголовок, уточняющий аспект, если это уместно.

    2.  **План Занятия (если применимо):** Если текст структурирован, создай краткий "План занятия" в виде нумерованного списка основных тем.  По возможности, укажи примерное время, затраченное на каждую тему в оригинальном тексте (например, "1. Введение (0:00)").  Если временные метки отсутствуют, не добавляй их. Обязательно указывай таймкоды из оригинального текста.

    3.  **Разделы:** Раздели сводку на логические разделы, соответствующие основным темам текста (например, "История Старой Рязани", "Археологические находки", "Неразгаданные тайны", но не используй этот пример по умолчанию).  Каждый раздел должен начинаться с заголовка.

    4.  **Описание:** В каждом разделе предоставь краткое описание темы, используя 2-3 предложения.  Определи и упомяни ключевые фигуры, события или места, связанные с этой темой.  Старайся использовать терминологию, близкую к оригинальному тексту. Не начиать раздел со слов (Описание:), а выводить сразу текст. Где уместно добавляй термины (напимер Картошка-это...)

    5.  **Таблицы:** Если в тексте есть сравнительные данные или классификации, а также исторические даты, представь их в виде json [["Заголовок 1", "Заголовок 2"], ["Значение 1", "Значение 2"], ["Значение 3", "Значение 4"]] .

    6.  **Стиль:** Сохраняй информативный и нейтральный тон.  Избегай личных оценок или интерпретаций.  Стремись к краткости и ясности изложения.

    Текст:
    {text}

    Сводка (в стиле конспекта):
    """

    chat_response = client.chat.complete(
        model=model,
        messages=[
            {
                "role": "user",
                "content": prompt
            },
        ]
    )
    response = chat_response.choices[0].message.content
    return response


def yt_downloader(link):
    yt = YouTube(link, on_progress_callback=on_progress)
    a = r'(?:youtu\.be\/|watch\?v=)([a-zA-Z0-9_-]{11})'
    audio_track_hq = yt.streams.filter(type='audio').last()
    textfile_name = re.search(a, link).group(1)
    audio_track_filepath = audio_track_hq.download(f'uploads/{textfile_name}',filename=f'{textfile_name}.m4a')
    print(audio_track_filepath)
    return textfile_name, audio_track_filepath

def transcribing(audio_track_filepath):
    model = whisper.load_model('small')

    # Получаем длину аудиопотока
    audio = AudioSegment.from_file(audio_track_filepath)
    audio_length = len(audio) / 1000  # Длина в секундах
    duration_per_segment = 40  # Длина сегмента в секундах

    start_time = 0
    text_with_timestamp = ''

    while start_time < audio_length:
        end_time = min(start_time + duration_per_segment, audio_length)
        print(f"Обработка аудиосегмента с {start_time:.2f} до {end_time:.2f} секунд...")

        # Выделяем текущий сегмент
        audio_part = audio[start_time * 1000:end_time * 1000]  # Умножаем на 1000 для миллисекунд
        audio_part_track_filepath = f'temporary_segment_{start_time:.2f}.wav'
        audio_part.export(audio_part_track_filepath, format='wav')  # Сохраняем сегмент во временный файл

        # Транскрибируем текущий сегмент
        result = model.transcribe(audio_part_track_filepath,
                                  word_timestamps=True,
                                  fp16=False)

        for segment in result['segments']:
            # Переводим время в формат "X минута Y секунда"
            total_seconds = int(start_time+segment['start'])
            minutes = total_seconds // 60
            seconds = total_seconds % 60
            time_formatted = f"{minutes} минута {seconds} секунда"

            text_with_timestamp += f"{time_formatted} {segment['text']}\n"
            print(f"{time_formatted} {segment['text']}")  # Вывод текста сегмента в процессе


        os.remove(audio_part_track_filepath)
        start_time += duration_per_segment

    return text_with_timestamp

def main(link):
    if 'uploads' in link:
        textfile_name = link.split('/')[1]
        audio_track_filepath = link
    else:
        textfile_name, audio_track_filepath = yt_downloader(link)

    text_with_timestamp = transcribing(audio_track_filepath)
    # Сохранение полного текста в файл
    with open(f'uploads/{textfile_name}/{textfile_name}_text_video.txt', 'w', encoding='utf-8') as f:
        f.write(text_with_timestamp)

    # Создание резюме
    with open(f'uploads/{textfile_name}/{textfile_name}_text_resume.txt', 'w', encoding='utf-8') as f:
        summary = resume(text_with_timestamp)
        f.write(summary)

    # Преобразуем TXT в PDF
    txt_to_pdf(f'uploads/{textfile_name}/{textfile_name}_text_resume.txt', f"uploads/{textfile_name}/{textfile_name}.pdf")

