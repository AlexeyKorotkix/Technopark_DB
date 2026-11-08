/* =====================================================================
   main.js — интерактивность для приложения "СУБД Технопарка"
   Обработчики подтверждений удаления, возврата оборудования и т.д.
   ===================================================================== */

// Ждём полной загрузки DOM
document.addEventListener('DOMContentLoaded', function () {

    // ---------- Подтверждение удаления ----------
    // Все формы с классом .delete-form требуют подтверждения перед отправкой
    document.querySelectorAll('.delete-form').forEach(function (form) {
        form.addEventListener('submit', function (event) {
            // Проверяем, было ли уже подтверждение (чтобы не спрашивать дважды)
            if (!form.dataset.confirmed) {
                event.preventDefault();
                if (confirm('Вы уверены, что хотите удалить эту запись?\nЭто действие нельзя отменить.')) {
                    form.dataset.confirmed = 'true';
                    form.submit();
                }
            }
        });
    });

    // ---------- Подтверждение возврата оборудования ----------
    document.querySelectorAll('.return-form').forEach(function (form) {
        form.addEventListener('submit', function (event) {
            if (!form.dataset.confirmed) {
                event.preventDefault();
                if (confirm('Подтвердить возврат оборудования?\nСтатус будет изменён на «Доступно».')) {
                    form.dataset.confirmed = 'true';
                    form.submit();
                }
            }
        });
    });

    // ---------- Автоматическое скрытие flash-сообщений через 5 секунд ----------
    document.querySelectorAll('.alert-dismissible').forEach(function (alert) {
        setTimeout(function () {
            // Плавное исчезновение через Bootstrap-классы
            var bsAlert = new bootstrap.Alert(alert);
            // Используем CSS-анимацию через fade
            alert.style.transition = 'opacity 0.5s ease';
            alert.style.opacity = '0';
            setTimeout(function () {
                bsAlert.close();
            }, 500);
        }, 5000);
    });

    // ---------- Подсказки (tooltips) Bootstrap ----------
    // Инициализируем все элементы с атрибутом title как tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[title]'));
    tooltipTriggerList.forEach(function (el) {
        new bootstrap.Tooltip(el);
    });

    // ---------- Установка текущей даты в формах, если поле пустое ----------
    var startDatetimeField = document.getElementById('start_datetime');
    if (startDatetimeField && !startDatetimeField.value) {
        // Формат для input[type=datetime-local]: YYYY-MM-DDTHH:MM
        var now = new Date();
        now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
        startDatetimeField.value = now.toISOString().slice(0, 16);
    }

    // ---------- Валидация: дата окончания не раньше даты начала ----------
    var startField = document.getElementById('start_datetime');
    var endField = document.getElementById('end_datetime');
    if (startField && endField) {
        endField.addEventListener('change', function () {
            if (startField.value && endField.value && endField.value < startField.value) {
                alert('Дата окончания не может быть раньше даты начала');
                endField.value = '';
            }
        });
    }

    // ---------- Вывод в консоль для отладки ----------
    console.log('%c ТехноПарк DB ', 'background: #0d6efd; color: white; font-size: 14px; padding: 4px 8px; border-radius: 4px;');
    console.log('Приложение загружено. Версия: 1.0');
});