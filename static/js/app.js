// App initialization
document.addEventListener('DOMContentLoaded', () => {
    Grid.init();
    Chat.init();
    Skills.init();

    // Check Solved button
    document.getElementById('validate-btn').addEventListener('click', () => {
        const valid = Grid.validate();
        const btn = document.getElementById('validate-btn');
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
            btn.textContent = 'Check Solved';
            btn.classList.remove('valid', 'invalid');
        }, 2500);
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
});
