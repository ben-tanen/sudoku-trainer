// Sudoku Grid module
const Grid = (() => {
    let grid = Array.from({ length: 9 }, () =>
        Array.from({ length: 9 }, () => ({
            value: 0,
            source: null,     // 'given' | 'pen' | null
            pencil: new Set() // manual pencil marks
        }))
    );

    let selectedRow = -1;
    let selectedCol = -1;
    let currentMode = 'given'; // 'given' | 'pen' | 'pencil'
    let highlightedDigit = 0;
    let tutorHighlightCells = [];
    let autoCandidates = false;
    let errorCells = [];  // cells with validation errors

    const STORAGE_KEY = 'sudoku-trainer-puzzle';

    function saveToStorage() {
        const data = grid.map(row => row.map(cell => ({
            value: cell.value,
            source: cell.source,
            pencil: [...cell.pencil],
        })));
        localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
    }

    function loadFromStorage() {
        const saved = localStorage.getItem(STORAGE_KEY);
        if (!saved) return;
        try {
            const data = JSON.parse(saved);
            for (let r = 0; r < 9; r++) {
                for (let c = 0; c < 9; c++) {
                    grid[r][c].value = data[r][c].value;
                    grid[r][c].source = data[r][c].source;
                    grid[r][c].pencil = new Set(data[r][c].pencil || []);
                }
            }
        } catch (e) {
            // corrupted data, ignore
        }
    }

    function init() {
        const table = document.getElementById('sudoku-grid');
        table.innerHTML = '';

        for (let r = 0; r < 9; r++) {
            const tr = document.createElement('tr');
            for (let c = 0; c < 9; c++) {
                const td = document.createElement('td');
                td.dataset.row = r;
                td.dataset.col = c;
                td.addEventListener('click', () => selectCell(r, c));
                tr.appendChild(td);
            }
            table.appendChild(tr);
        }

        document.addEventListener('keydown', handleKeyDown);
        initModeToggle();
        initClearButton();
        loadFromStorage();
        renderAll();
    }

    function initModeToggle() {
        document.querySelectorAll('.mode-btn').forEach(btn => {
            btn.addEventListener('click', () => setMode(btn.dataset.mode));
        });
    }

    function initClearButton() {
        document.getElementById('clear-grid-btn').addEventListener('click', () => {
            if (confirm('Clear the entire grid?')) {
                clearGrid();
            }
        });
    }

    function setMode(mode) {
        currentMode = mode;
        document.querySelectorAll('.mode-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.mode === mode);
        });
        const labels = { given: 'Given', pen: 'Solved', pencil: 'Pencil' };
        document.getElementById('mode-indicator').textContent = `Mode: ${labels[mode]}`;
    }

    function selectCell(r, c) {
        selectedRow = r;
        selectedCol = c;

        // Toggle digit highlighting: click a filled cell to highlight, click again or empty cell to clear
        const cell = grid[r][c];
        if (cell.value > 0) {
            highlightedDigit = (highlightedDigit === cell.value) ? 0 : cell.value;
        } else {
            highlightedDigit = 0;
        }

        updateCellIndicator();
        renderAll();
    }

    function updateCellIndicator() {
        const el = document.getElementById('cell-indicator');
        if (selectedRow < 0) {
            el.textContent = '-';
        } else {
            el.textContent = `R${selectedRow + 1}C${selectedCol + 1}`;
        }
    }

    const MODES = ['given', 'pen', 'pencil'];

    function cycleMode(direction) {
        const idx = MODES.indexOf(currentMode);
        const next = (idx + direction + MODES.length) % MODES.length;
        setMode(MODES[next]);
    }

    function handleKeyDown(e) {
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;

        // Shift+Tab cycles mode (works even without a selected cell)
        if (e.key === 'Tab' && e.shiftKey) {
            e.preventDefault();
            cycleMode(1);
            return;
        }

        if (selectedRow < 0) return;

        // Direct mode shortcuts
        if (e.key === 'g' || e.key === 'G') { setMode('given'); return; }
        if (e.key === 's' || e.key === 'S') { setMode('pen'); return; }
        if (e.key === 'p' || e.key === 'P') { setMode('pencil'); return; }

        // Arrow navigation
        if (e.key === 'ArrowUp') { e.preventDefault(); selectCell(Math.max(0, selectedRow - 1), selectedCol); return; }
        if (e.key === 'ArrowDown') { e.preventDefault(); selectCell(Math.min(8, selectedRow + 1), selectedCol); return; }
        if (e.key === 'ArrowLeft') { e.preventDefault(); selectCell(selectedRow, Math.max(0, selectedCol - 1)); return; }
        if (e.key === 'ArrowRight') { e.preventDefault(); selectCell(selectedRow, Math.min(8, selectedCol + 1)); return; }

        // Tab to advance cell (wrapping)
        if (e.key === 'Tab') {
            e.preventDefault();
            let nextCol = selectedCol + 1;
            let nextRow = selectedRow;
            if (nextCol > 8) { nextCol = 0; nextRow = (nextRow + 1) % 9; }
            selectCell(nextRow, nextCol);
            return;
        }

        // Digit entry
        const digit = parseInt(e.key);
        if (digit >= 1 && digit <= 9) {
            enterDigit(digit);
            return;
        }

        // Delete/Backspace
        if (e.key === 'Delete' || e.key === 'Backspace') {
            clearCell(selectedRow, selectedCol);
            return;
        }
    }

    function enterDigit(digit) {
        errorCells = [];  // clear validation errors on any edit
        const cell = grid[selectedRow][selectedCol];

        if (currentMode === 'pencil') {
            // Toggle pencil mark
            if (cell.value > 0) return; // can't pencil a filled cell
            if (cell.pencil.has(digit)) {
                cell.pencil.delete(digit);
            } else {
                cell.pencil.add(digit);
            }
        } else {
            // Given or Pen mode
            cell.value = (cell.value === digit) ? 0 : digit; // toggle
            cell.source = cell.value > 0 ? currentMode : null;
            cell.pencil.clear();
        }

        saveToStorage();
        renderAll();
    }

    function clearCell(r, c) {
        grid[r][c].value = 0;
        grid[r][c].source = null;
        grid[r][c].pencil.clear();
        saveToStorage();
        renderAll();
    }

    function clearGrid() {
        for (let r = 0; r < 9; r++) {
            for (let c = 0; c < 9; c++) {
                grid[r][c].value = 0;
                grid[r][c].source = null;
                grid[r][c].pencil.clear();
            }
        }
        highlightedDigit = 0;
        tutorHighlightCells = [];
        saveToStorage();
        renderAll();
    }

    function getAutoCandidate(r, c) {
        if (grid[r][c].value > 0) return new Set();
        const used = new Set();

        // Row
        for (let cc = 0; cc < 9; cc++) if (grid[r][cc].value) used.add(grid[r][cc].value);
        // Col
        for (let rr = 0; rr < 9; rr++) if (grid[rr][c].value) used.add(grid[rr][c].value);
        // Box
        const br = Math.floor(r / 3) * 3, bc = Math.floor(c / 3) * 3;
        for (let rr = br; rr < br + 3; rr++)
            for (let cc = bc; cc < bc + 3; cc++)
                if (grid[rr][cc].value) used.add(grid[rr][cc].value);

        const candidates = new Set();
        for (let d = 1; d <= 9; d++) if (!used.has(d)) candidates.add(d);
        return candidates;
    }

    function renderAll() {
        const table = document.getElementById('sudoku-grid');
        const selectedBox = selectedRow >= 0
            ? [Math.floor(selectedRow / 3) * 3, Math.floor(selectedCol / 3) * 3]
            : null;

        for (let r = 0; r < 9; r++) {
            for (let c = 0; c < 9; c++) {
                const td = table.rows[r].cells[c];
                const cell = grid[r][c];

                // CSS classes
                td.className = '';
                if (cell.source === 'given') td.classList.add('given-cell');
                if (r === selectedRow && c === selectedCol) td.classList.add('selected');

                // Related row/col/box
                if (selectedRow >= 0) {
                    if (r === selectedRow || c === selectedCol) td.classList.add('related');
                    if (selectedBox &&
                        r >= selectedBox[0] && r < selectedBox[0] + 3 &&
                        c >= selectedBox[1] && c < selectedBox[1] + 3) {
                        td.classList.add('related');
                    }
                }

                // Highlights
                if (highlightedDigit > 0 && cell.value === highlightedDigit) {
                    td.classList.add('highlight-manual');
                }
                if (tutorHighlightCells.some(([hr, hc]) => hr === r && hc === c)) {
                    td.classList.add('highlight-tutor');
                }
                if (errorCells.some(([er, ec]) => er === r && ec === c)) {
                    td.classList.add('error');
                }

                // Content
                td.innerHTML = '';

                if (cell.value > 0) {
                    const span = document.createElement('span');
                    span.className = `cell-value ${cell.source || ''}`;
                    span.textContent = cell.value;
                    td.appendChild(span);
                } else {
                    // Show pencil marks (manual or auto)
                    const manualMarks = cell.pencil;
                    const autoMarks = autoCandidates ? getAutoCandidate(r, c) : new Set();
                    const hasMarks = manualMarks.size > 0 || autoMarks.size > 0;

                    if (hasMarks) {
                        const container = document.createElement('div');
                        container.className = 'pencil-marks';

                        for (let d = 1; d <= 9; d++) {
                            const mark = document.createElement('span');
                            mark.className = 'pencil-mark';

                            if (manualMarks.has(d)) {
                                mark.textContent = d;
                            } else if (autoMarks.has(d)) {
                                mark.textContent = d;
                                mark.classList.add('auto');
                            }

                            container.appendChild(mark);
                        }

                        td.appendChild(container);
                    }
                }
            }
        }
    }

    function validate() {
        errorCells = [];
        const errors = new Set();

        // Check each unit (row, col, box) for duplicate digits among filled cells
        const units = [];
        for (let i = 0; i < 9; i++) {
            // Rows
            units.push(Array.from({ length: 9 }, (_, c) => [i, c]));
            // Columns
            units.push(Array.from({ length: 9 }, (_, r) => [r, i]));
            // Boxes
            const br = Math.floor(i / 3) * 3, bc = (i % 3) * 3;
            const box = [];
            for (let dr = 0; dr < 3; dr++)
                for (let dc = 0; dc < 3; dc++)
                    box.push([br + dr, bc + dc]);
            units.push(box);
        }

        for (const unit of units) {
            const seen = {};
            for (const [r, c] of unit) {
                const val = grid[r][c].value;
                if (val === 0) continue;
                if (seen[val] !== undefined) {
                    errors.add(`${r},${c}`);
                    errors.add(seen[val]);
                } else {
                    seen[val] = `${r},${c}`;
                }
            }
        }

        errorCells = [...errors].map(s => s.split(',').map(Number));
        renderAll();
        return errorCells.length === 0;
    }

    function setAutoCandidates(enabled) {
        autoCandidates = enabled;
        renderAll();
    }

    function setTutorHighlight(cells) {
        tutorHighlightCells = cells || [];
        renderAll();
    }

    function getState() {
        const values = [];
        const given = [];
        const candidates = {};

        for (let r = 0; r < 9; r++) {
            const rowVals = [];
            const rowGiven = [];
            for (let c = 0; c < 9; c++) {
                const cell = grid[r][c];
                rowVals.push(cell.value);
                rowGiven.push(cell.source === 'given' ? 1 : 0);
                if (cell.pencil.size > 0) {
                    candidates[`r${r + 1}c${c + 1}`] = [...cell.pencil].sort();
                }
            }
            values.push(rowVals);
            given.push(rowGiven);
        }

        return { grid: values, given, candidates };
    }

    function getMode() {
        return currentMode;
    }

    return { init, setMode, setAutoCandidates, setTutorHighlight, validate, getState, getMode, renderAll };
})();
