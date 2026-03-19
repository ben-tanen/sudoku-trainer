// Chat module
const Chat = (() => {
    let conversationHistory = [];
    let lastTechnique = null;  // last technique result from solver

    function init() {
        document.getElementById('hint-btn').addEventListener('click', requestHint);
        document.getElementById('chat-send').addEventListener('click', sendMessage);
        document.getElementById('chat-input').addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
    }

    function addMessage(text, role) {
        const container = document.getElementById('chat-messages');
        const div = document.createElement('div');
        div.className = `message ${role}`;
        div.innerHTML = `<p>${formatMessage(text)}</p>`;
        container.appendChild(div);
        container.scrollTop = container.scrollHeight;

        conversationHistory.push({ role, content: text });
    }

    function formatMessage(text) {
        // Basic markdown: bold, italic
        let html = text
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/R(\d)C(\d)/g, '<strong class="cell-ref" data-row="$1" data-col="$2">R$1C$2</strong>');

        // Replace technique names with hoverable tooltips
        const tooltips = Skills.getTechniqueTooltips();
        // Sort by label length descending so "Naked Triple" matches before "Naked"
        const names = Object.values(tooltips).sort((a, b) => b.label.length - a.label.length);
        for (const { label, desc, tier } of names) {
            // Match whole technique name (case-insensitive), but not inside HTML tags
            const regex = new RegExp(`(?<![<\\w/])\\b(${label.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})s?\\b`, 'gi');
            html = html.replace(regex, `<span class="technique-tooltip" data-tooltip="${desc} (${tier})">${label}</span>`);
        }

        return html;
    }

    function setLoading(loading) {
        const btn = document.getElementById('hint-btn');
        btn.disabled = loading;
        btn.textContent = loading ? 'Thinking...' : 'Get Hint';
    }

    async function requestHint() {
        const state = Grid.getState();
        const skills = Skills.getProfile();

        setLoading(true);
        try {
            const resp = await fetch('/api/hint', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ puzzle: state, skill_profile: skills })
            });

            if (!resp.ok) throw new Error(`API error: ${resp.status}`);
            const data = await resp.json();

            if (data.highlight_cells) {
                Grid.setTutorHighlight(data.highlight_cells);
            }
            if (data.technique) {
                lastTechnique = data.technique;
            }

            addMessage(data.message, 'tutor');
        } catch (err) {
            addMessage(`Error: ${err.message}`, 'tutor');
        } finally {
            setLoading(false);
        }
    }

    async function sendMessage() {
        const input = document.getElementById('chat-input');
        const text = input.value.trim();
        if (!text) return;

        input.value = '';
        addMessage(text, 'user');

        const state = Grid.getState();
        const skills = Skills.getProfile();

        setLoading(true);
        try {
            const resp = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message: text,
                    puzzle: state,
                    skill_profile: skills,
                    history: conversationHistory.slice(-20),
                    last_technique: lastTechnique
                })
            });

            if (!resp.ok) throw new Error(`API error: ${resp.status}`);
            const data = await resp.json();

            if (data.highlight_cells) {
                Grid.setTutorHighlight(data.highlight_cells);
            }

            addMessage(data.message, 'tutor');
        } catch (err) {
            addMessage(`Error: ${err.message}`, 'tutor');
        } finally {
            setLoading(false);
        }
    }

    return { init, addMessage };
})();
