// OCR module — import puzzle from image
const OCR = (() => {
    let modal, pasteZone, preview, previewImg, status;

    function init() {
        modal = document.getElementById('ocr-modal');
        pasteZone = document.getElementById('ocr-paste-zone');
        preview = document.getElementById('ocr-preview');
        previewImg = document.getElementById('ocr-preview-img');
        status = document.getElementById('ocr-status');

        document.getElementById('ocr-modal-close').addEventListener('click', closeModal);
        modal.addEventListener('click', (e) => {
            if (e.target === modal) closeModal();
        });

        // File upload
        document.getElementById('ocr-file-input').addEventListener('change', (e) => {
            if (e.target.files[0]) handleFile(e.target.files[0]);
        });

        // Camera capture
        document.getElementById('ocr-camera-input').addEventListener('change', (e) => {
            if (e.target.files[0]) handleFile(e.target.files[0]);
        });

        // Paste zone — click to focus, then listen for paste
        pasteZone.setAttribute('tabindex', '0');
        pasteZone.addEventListener('paste', handlePaste);
        pasteZone.addEventListener('click', () => pasteZone.focus());

        // Also handle paste anywhere when modal is open
        document.addEventListener('paste', (e) => {
            if (!modal.classList.contains('hidden')) handlePaste(e);
        });
    }

    function openModal() {
        modal.classList.remove('hidden');
        status.textContent = '';
        status.className = 'ocr-status';
        preview.classList.add('hidden');
        // Reset file inputs so the same file can be re-selected
        document.getElementById('ocr-file-input').value = '';
        document.getElementById('ocr-camera-input').value = '';
        // Auto-focus paste zone on desktop
        setTimeout(() => pasteZone.focus(), 100);
    }

    function closeModal() {
        modal.classList.add('hidden');
    }

    function handlePaste(e) {
        const items = e.clipboardData && e.clipboardData.items;
        if (!items) return;

        for (const item of items) {
            if (item.type.startsWith('image/')) {
                e.preventDefault();
                const blob = item.getAsFile();
                if (blob) handleFile(blob);
                return;
            }
        }
    }

    function handleFile(file) {
        if (!file.type.startsWith('image/')) {
            showError('Please select an image file.');
            return;
        }
        if (file.size > 10 * 1024 * 1024) {
            showError('Image too large (max 10MB).');
            return;
        }

        // Show preview
        const url = URL.createObjectURL(file);
        previewImg.src = url;
        preview.classList.remove('hidden');

        sendToOCR(file);
    }

    async function sendToOCR(file) {
        showLoading(true);
        try {
            const formData = new FormData();
            formData.append('file', file);

            const resp = await fetch('/api/ocr', {
                method: 'POST',
                body: formData,
            });

            if (!resp.ok) throw new Error(`Server error: ${resp.status}`);
            const data = await resp.json();

            if (data.error) {
                showError(data.error);
                return;
            }

            Grid.loadPuzzle(data.grid);
            Chat.addMessage('Puzzle loaded from image. Switched to Solved mode — start solving!', 'tutor');
            closeModal();
        } catch (err) {
            showError(`Failed to scan puzzle: ${err.message}`);
        } finally {
            showLoading(false);
        }
    }

    function showError(msg) {
        status.textContent = msg;
        status.className = 'ocr-status ocr-error';
    }

    function showLoading(loading) {
        if (loading) {
            status.textContent = 'Scanning puzzle...';
            status.className = 'ocr-status ocr-loading';
        } else {
            if (status.classList.contains('ocr-loading')) {
                status.textContent = '';
                status.className = 'ocr-status';
            }
        }
    }

    return { init, openModal };
})();
