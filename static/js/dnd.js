// Получаем элемент области перетаскивания
const dropArea = document.getElementById('drop-area');

// Функция для предотвращения стандартного поведения браузера (например, открытие файла)
const preventDefault = (event) => {
    event.preventDefault();
    event.stopPropagation();
};

// Добавляем слушатели событий для перетаскивания
dropArea.addEventListener('dragover', (event) => {
    preventDefault(event);
    dropArea.classList.add('hover');
});

dropArea.addEventListener('dragleave', (event) => {
    preventDefault(event);
    dropArea.classList.remove('hover');
});

dropArea.addEventListener('drop', (event) => {
    preventDefault(event);
    dropArea.classList.remove('hover');

    const files = event.dataTransfer.files;
    if (files.length > 0) {
        uploadFile(files[0]);
    }
});

// Функция для отправки файла на сервер
const uploadFile = (file) => {
    const formData = new FormData();
    formData.append('file', file);

    fetch('/upload/', {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': getCookie('csrftoken')  // Нужно для защиты от CSRF атак в Django
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.message === 'Файл успешно загружен') {
            console.log('Файл загружен', data);
            // Обновляем название файла в dnd-secret-rectangle
            const secretRectangle = document.querySelector('.dnd-secret-rectangle');
            secretRectangle.textContent = `Ваше видео: ${file.name}`; // Устанавливаем имя файла
            secretRectangle.style.fontSize = '35px'
        }
    })
    .catch(error => {
        console.error('Ошибка загрузки файла', error);
    });
};

// Функция для получения CSRF токена из cookie
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}