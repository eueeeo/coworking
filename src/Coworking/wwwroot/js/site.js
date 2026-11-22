(function () {
    function getStoredTheme() {
        try {
            return localStorage.getItem('coworking_theme');
        } catch (e) {
            return null;
        }
    }

    function applyTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        try {
            localStorage.setItem('coworking_theme', theme);
        } catch (e) {}
        updateToggleButtons(theme);
    }

    function updateToggleButtons(theme) {
        var buttons = document.querySelectorAll('.js-theme-toggle');
        var isDark = (theme === 'dark');
        buttons.forEach(function (btn) {
            var textSpan = btn.querySelector('.theme-toggle-text');
            if (textSpan) {
                textSpan.textContent = isDark ? 'Светлая тема' : 'Тёмная тема';
            }
            btn.setAttribute('aria-pressed', isDark ? 'true' : 'false');
            btn.setAttribute('title', isDark ? 'Переключить на светлую тему' : 'Переключить на тёмную тему');
        });
    }

    window.toggleTheme = function () {
        var current = document.documentElement.getAttribute('data-theme') || 'light';
        var next = (current === 'dark') ? 'light' : 'dark';
        applyTheme(next);
    };

    document.addEventListener('DOMContentLoaded', function () {
        var currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
        updateToggleButtons(currentTheme);

        var buttons = document.querySelectorAll('.js-theme-toggle');
        buttons.forEach(function (btn) {
            btn.addEventListener('click', function (e) {
                e.preventDefault();
                window.toggleTheme();
            });
        });
    });
})();

window.openWorkspaceModal = function (cardEl) {
    var dataEl = cardEl.querySelector('.workspace-modal-data');
    if (!dataEl) return;

    var backdrop = document.getElementById('workspaceModalBackdrop');
    if (!backdrop) return;

    var id = dataEl.getAttribute('data-id');
    var number = dataEl.getAttribute('data-number');
    var type = dataEl.getAttribute('data-type');
    var price = dataEl.getAttribute('data-price');
    var location = dataEl.getAttribute('data-location');
    var active = dataEl.getAttribute('data-active') === '1';
    var desc = dataEl.getAttribute('data-desc');
    var amenitiesRaw = dataEl.getAttribute('data-amenities') || '[]';

    var modalNum = document.getElementById('modalSpaceNumber');
    if (modalNum) modalNum.textContent = number;

    var modalType = document.getElementById('modalSpaceType');
    if (modalType) modalType.textContent = type;

    var modalPrice = document.getElementById('modalSpacePrice');
    if (modalPrice) modalPrice.textContent = price;

    var modalLoc = document.getElementById('modalSpaceLocation');
    if (modalLoc) modalLoc.textContent = location;

    var modalDesc = document.getElementById('modalSpaceDesc');
    if (modalDesc) modalDesc.textContent = desc;

    var statusEl = document.getElementById('modalSpaceStatus');
    if (statusEl) {
        if (active) {
            statusEl.className = 'card-status-badge badge-available';
            statusEl.textContent = 'Свободно';
        } else {
            statusEl.className = 'card-status-badge badge-unavailable';
            statusEl.textContent = 'Занято';
        }
    }

    var listEl = document.getElementById('modalAmenitiesList');
    if (listEl) {
        listEl.innerHTML = '';
        try {
            var amenities = JSON.parse(amenitiesRaw);
            if (amenities && amenities.length > 0) {
                amenities.forEach(function (item) {
                    var li = document.createElement('li');
                    li.innerHTML = '<span class="modal-amenity-check">&bull;</span><span>' + item + '</span>';
                    listEl.appendChild(li);
                });
            } else {
                var li = document.createElement('li');
                li.textContent = 'Базовое оснащение рабочего места';
                listEl.appendChild(li);
            }
        } catch (err) {
            listEl.innerHTML = '<li>Базовое оснащение</li>';
        }
    }

    var notice = document.getElementById('modalUnavailableNotice');
    var bookingBtn = document.getElementById('modalBookingBtn');
    if (bookingBtn) {
        if (active) {
            bookingBtn.href = '/Bookings/Create?workspaceId=' + encodeURIComponent(id);
            bookingBtn.style.display = 'inline-flex';
            bookingBtn.textContent = 'Забронировать это место';
            if (notice) notice.style.display = 'none';
        } else {
            bookingBtn.style.display = 'none';
            if (notice) notice.style.display = 'block';
        }
    }

    backdrop.classList.add('active');
    document.body.style.overflow = 'hidden';
};

window.closeWorkspaceModal = function (e) {
    if (e && e.target && e.target.id !== 'workspaceModalBackdrop' && !e.target.classList.contains('modal-close-btn')) {
        return;
    }
    var backdrop = document.getElementById('workspaceModalBackdrop');
    if (backdrop) {
        backdrop.classList.remove('active');
        document.body.style.overflow = '';
    }
};

window.toggleAdminPanel = function (btn, panelId) {
    var panel = document.getElementById(panelId);
    if (!panel) return;
    var isHidden = (panel.style.display === 'none' || getComputedStyle(panel).display === 'none');
    if (isHidden) {
        panel.style.display = 'block';
        if (btn) btn.textContent = 'Скрыть форму';
    } else {
        panel.style.display = 'none';
        if (btn) btn.textContent = '+ Добавить';
    }
};

document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') {
        window.closeWorkspaceModal();
    }
});