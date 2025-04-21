document.addEventListener('mousemove', (e) => {
  const trail = document.createElement('div');
  trail.className = 'trail';
  document.body.appendChild(trail);

  trail.style.left = `${e.pageX}px`;  // Позиция по оси X
  trail.style.top = `${e.pageY}px`;   // Позиция по оси Y
  // trail.style.transform = 'translate(-50%, -50%)'; // Центрирование

  // Удаляем след после завершения анимации
  setTimeout(() => {
    trail.remove();
  }, 1000); // Время должно совпадать с длительностью анимации
});

// Кастомный курсор
document.addEventListener('mousemove', (e) => {
  const cursor = document.getElementById('cursor');
  // Обновляем позицию кастомного курсора
  cursor.style.left = `${e.pageX}px`;
  cursor.style.top = `${e.pageY}px`;
  // cursor.style.transform = 'translate(-50%, -50%)'; // Центрируем курсор
});
