// Skill Profile module
const Skills = (() => {
    const TIERS = [
        {
            name: 'Beginner',
            techniques: [
                { id: 'naked_single', label: 'Naked Single', desc: 'Cell has only one possible candidate' },
                { id: 'hidden_single', label: 'Hidden Single', desc: 'Digit can only go in one cell in a row/col/box' }
            ]
        },
        {
            name: 'Intermediate',
            techniques: [
                { id: 'naked_pair', label: 'Naked Pair', desc: 'Two cells in a unit share the same two candidates' },
                { id: 'naked_triple', label: 'Naked Triple', desc: 'Three cells share three candidates' },
                { id: 'hidden_pair', label: 'Hidden Pair', desc: 'Two digits only appear in two cells in a unit' },
                { id: 'hidden_triple', label: 'Hidden Triple', desc: 'Three digits only appear in three cells in a unit' },
                { id: 'pointing_pair', label: 'Pointing Pair', desc: 'Candidates in a box restricted to one row/col' },
                { id: 'box_line_reduction', label: 'Box/Line Reduction', desc: 'Candidates in a row/col within one box' }
            ]
        },
        {
            name: 'Advanced',
            techniques: [
                { id: 'x_wing', label: 'X-Wing', desc: 'Digit in exactly two cells in two rows, same columns' },
                { id: 'swordfish', label: 'Swordfish', desc: 'Three-row/three-col fish pattern' },
                { id: 'xy_wing', label: 'XY-Wing', desc: 'Three bivalue cells forming pivot and wings' },
                { id: 'simple_coloring', label: 'Simple Coloring', desc: 'Chain-based coloring of a single digit' }
            ]
        },
        {
            name: 'Expert',
            techniques: [
                { id: 'jellyfish', label: 'Jellyfish', desc: 'Four-row/four-col fish pattern' },
                { id: 'unique_rectangle', label: 'Unique Rectangle', desc: 'Avoid deadly patterns with multiple solutions' },
                { id: 'xyz_wing', label: 'XYZ-Wing', desc: 'Extension of XY-Wing with three candidates in pivot' },
                { id: 'forcing_chain', label: 'Forcing Chain', desc: 'If-then chains leading to contradiction or confirmation' }
            ]
        }
    ];

    const STORAGE_KEY = 'sudoku-trainer-skills';

    let profile = {};

    function init() {
        loadProfile();
        renderModal();

        document.getElementById('skill-profile-btn').addEventListener('click', openModal);
        document.getElementById('skill-modal-close').addEventListener('click', closeModal);
        document.getElementById('skill-modal').addEventListener('click', (e) => {
            if (e.target.id === 'skill-modal') closeModal();
        });
    }

    function loadProfile() {
        const saved = localStorage.getItem(STORAGE_KEY);
        if (saved) {
            profile = JSON.parse(saved);
        } else {
            // Default: beginner techniques known
            profile = {};
            TIERS.forEach(tier => {
                tier.techniques.forEach(t => {
                    profile[t.id] = tier.name === 'Beginner';
                });
            });
            saveProfile();
        }
    }

    function saveProfile() {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(profile));
    }

    function renderModal() {
        const body = document.getElementById('skill-modal-body');
        body.innerHTML = '';

        TIERS.forEach(tier => {
            const section = document.createElement('div');
            section.className = 'skill-tier';

            const header = document.createElement('h3');
            header.textContent = tier.name + ' ';

            const selectAll = document.createElement('button');
            selectAll.className = 'tier-select-all';
            selectAll.textContent = '(toggle all)';
            selectAll.addEventListener('click', () => {
                const allChecked = tier.techniques.every(t => profile[t.id]);
                tier.techniques.forEach(t => { profile[t.id] = !allChecked; });
                saveProfile();
                renderModal();
            });
            header.appendChild(selectAll);
            section.appendChild(header);

            tier.techniques.forEach(t => {
                const label = document.createElement('label');
                const checkbox = document.createElement('input');
                checkbox.type = 'checkbox';
                checkbox.checked = !!profile[t.id];
                checkbox.addEventListener('change', () => {
                    profile[t.id] = checkbox.checked;
                    saveProfile();
                });
                label.appendChild(checkbox);
                label.appendChild(document.createTextNode(`${t.label} — ${t.desc}`));
                section.appendChild(label);
            });

            body.appendChild(section);
        });
    }

    function openModal() { document.getElementById('skill-modal').classList.remove('hidden'); }
    function closeModal() { document.getElementById('skill-modal').classList.add('hidden'); }

    function getProfile() {
        return { ...profile };
    }

    function getTiers() {
        return TIERS;
    }

    function getTechniqueTooltips() {
        // Build a map of technique label (and common variations) → tooltip description
        const tooltips = {};
        TIERS.forEach(tier => {
            tier.techniques.forEach(t => {
                tooltips[t.label.toLowerCase()] = { label: t.label, desc: t.desc, tier: tier.name };
            });
        });
        return tooltips;
    }

    return { init, getProfile, getTiers, getTechniqueTooltips };
})();
