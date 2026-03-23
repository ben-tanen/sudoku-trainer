// App initialization
document.addEventListener('DOMContentLoaded', () => {
    Grid.init();
    Chat.init();
    Skills.init();
    OCR.init();

    // Check Solved — shared logic for desktop + mobile buttons
    function flashValidateBtn(btn, originalText) {
        const valid = Grid.validate();
        if (valid) {
            btn.textContent = 'All good!';
            btn.classList.add('valid');
            btn.classList.remove('invalid');
        } else {
            btn.textContent = 'Conflicts found';
            btn.classList.add('invalid');
            btn.classList.remove('valid');
        }
        setTimeout(() => {
            btn.textContent = originalText;
            btn.classList.remove('valid', 'invalid');
        }, 2500);
    }

    document.getElementById('validate-btn').addEventListener('click', () => {
        flashValidateBtn(document.getElementById('validate-btn'), 'Check Solved');
    });

    // Auto-candidates toggle
    const acBtn = document.getElementById('auto-candidates-btn');
    let acEnabled = false;
    acBtn.addEventListener('click', () => {
        acEnabled = !acEnabled;
        acBtn.textContent = `Auto-Candidates: ${acEnabled ? 'ON' : 'OFF'}`;
        acBtn.classList.toggle('active', acEnabled);
        Grid.setAutoCandidates(acEnabled);
    });

    // Check LLM provider status
    fetch('/api/provider')
        .then(r => r.json())
        .then(info => {
            const indicator = document.getElementById('provider-status');
            if (info.available) {
                indicator.textContent = `LLM: ${info.provider} (${info.model})`;
                indicator.classList.add('connected');
            } else {
                indicator.textContent = 'LLM: not configured (template hints)';
                indicator.classList.add('disconnected');
            }
        })
        .catch(() => {});

    // --- Mobile: Number pad ---
    document.querySelectorAll('.numpad-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const sel = Grid.getSelected();
            if (sel.row < 0) return;
            const digit = parseInt(btn.dataset.digit);
            if (digit === 0) {
                Grid.clearCell(sel.row, sel.col);
            } else {
                Grid.enterDigit(digit);
            }
        });
    });

    // --- Import buttons ---
    document.getElementById('import-btn').addEventListener('click', () => OCR.openModal());
    document.getElementById('mobile-import-btn').addEventListener('click', () => OCR.openModal());

    // --- Mobile: Gear button opens skill modal ---
    document.getElementById('mobile-gear-btn').addEventListener('click', () => {
        document.getElementById('skill-modal').classList.remove('hidden');
    });

    // --- Mobile: Tool buttons ---
    document.getElementById('mobile-validate-btn').addEventListener('click', () => {
        flashValidateBtn(document.getElementById('mobile-validate-btn'), 'Check');
    });

    document.getElementById('mobile-auto-candidates-btn').addEventListener('click', () => {
        acBtn.click();
        const mobileAcBtn = document.getElementById('mobile-auto-candidates-btn');
        mobileAcBtn.classList.toggle('active', acBtn.classList.contains('active'));
        mobileAcBtn.textContent = acEnabled ? 'AutoCand: ON' : 'AutoCand';
    });

    document.getElementById('mobile-clear-grid-btn').addEventListener('click', () => {
        document.getElementById('clear-grid-btn').click();
    });

    // --- Mobile: Bottom sheet ---
    const chatContainer = document.querySelector('.chat-container');
    const handle = document.querySelector('.bottom-sheet-handle');
    let sheetExpanded = false;

    const footer = document.querySelector('.footer');

    function toggleSheet() {
        sheetExpanded = !sheetExpanded;
        chatContainer.classList.toggle('expanded', sheetExpanded);
        if (footer) footer.style.display = sheetExpanded ? 'none' : '';
    }

    function openSheet() {
        if (!sheetExpanded) toggleSheet();
    }

    function closeSheet() {
        if (sheetExpanded) toggleSheet();
    }

    // Mobile tutor button toggles the sheet
    document.getElementById('mobile-tutor-btn').addEventListener('click', toggleSheet);

    // Tap handle to collapse (when expanded)
    handle.addEventListener('click', (e) => {
        if (e.target.closest('.handle-hint-btn')) return;
        closeSheet();
    });

    // Mobile hint button in handle
    document.getElementById('mobile-hint-btn').addEventListener('click', () => {
        if (!sheetExpanded) openSheet();
        document.getElementById('hint-btn').click();
    });

    // Drag to expand/collapse
    let dragStartY = 0;
    let dragStartTranslate = 0;
    let isDragging = false;

    handle.addEventListener('touchstart', (e) => {
        if (e.target.closest('.handle-hint-btn')) return;
        isDragging = true;
        dragStartY = e.touches[0].clientY;
        const sheetHeight = chatContainer.offsetHeight;
        dragStartTranslate = sheetExpanded ? 0 : sheetHeight;
        chatContainer.style.transition = 'none';
    }, { passive: true });

    handle.addEventListener('touchmove', (e) => {
        if (!isDragging) return;
        const dy = e.touches[0].clientY - dragStartY;
        const sheetHeight = chatContainer.offsetHeight;
        const newTranslate = Math.max(0, Math.min(sheetHeight, dragStartTranslate + dy));
        chatContainer.style.transform = `translateY(${newTranslate}px)`;
    }, { passive: true });

    handle.addEventListener('touchend', (e) => {
        if (!isDragging) return;
        isDragging = false;
        chatContainer.style.transition = '';
        chatContainer.style.transform = '';

        const dy = e.changedTouches[0].clientY - dragStartY;
        const threshold = 60;

        if (sheetExpanded && dy > threshold) {
            sheetExpanded = false;
        } else if (!sheetExpanded && dy < -threshold) {
            sheetExpanded = true;
        }
        chatContainer.classList.toggle('expanded', sheetExpanded);
    }, { passive: true });
});
