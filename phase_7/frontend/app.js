const API_BASE = window.location.origin;

/* ============================================================
   DOM References
   ============================================================ */
const els = {
    chatToggle: document.getElementById('chat-toggle'),
    chatPanel: document.getElementById('chat-panel'),
    chatClose: document.getElementById('chat-close'),
    chatOverlay: document.getElementById('chat-overlay'),
    messages: document.getElementById('chat-messages'),
    chips: document.getElementById('suggested-chips'),
    chipButtons: document.querySelectorAll('.chip'),
    quickChips: document.querySelectorAll('.quick-chip'),
    queryInput: document.getElementById('query-input'),
    sendBtn: document.getElementById('send-btn'),
    schemeSelect: document.getElementById('scheme-select'),
    charCount: document.getElementById('char-count'),
};

let isOpen = false;
let isLoading = false;
let currentQuery = '';
let currentAnswer = '';
let messageHistory = JSON.parse(sessionStorage.getItem('mfChatHistory') || '[]');
let abortController = null;

/* ============================================================
   Init
   ============================================================ */
document.addEventListener('DOMContentLoaded', () => {
    loadSchemes();
    renderWelcome();
    restoreHistory();
    bindEvents();
    updateCharCount();
});

function bindEvents() {
    els.chatToggle.addEventListener('click', toggleChat);
    els.chatClose.addEventListener('click', closeChat);
    els.chatOverlay?.addEventListener('click', closeChat);

    els.sendBtn.addEventListener('click', handleSend);
    els.queryInput.addEventListener('keydown', e => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    });
    els.queryInput.addEventListener('input', updateCharCount);

    // Chat widget suggested chips
    els.chipButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const q = btn.dataset.query;
            if (q) {
                els.queryInput.value = q;
                updateCharCount();
                handleSend();
            }
        });
    });

    // Dashboard quick-ask chips
    els.quickChips.forEach(btn => {
        btn.addEventListener('click', () => {
            const q = btn.dataset.query;
            if (q) {
                if (!isOpen) openChat();
                els.queryInput.value = q;
                updateCharCount();
                handleSend();
            }
        });
    });

    // Close on Escape
    document.addEventListener('keydown', e => {
        if (e.key === 'Escape' && isOpen) closeChat();
    });
}

/* ============================================================
   Chat Open / Close / Toggle
   ============================================================ */
function openChat() {
    if (isOpen) return;
    isOpen = true;
    els.chatToggle.classList.add('active');
    els.chatPanel.classList.remove('hidden');
    els.chatPanel.setAttribute('aria-hidden', 'false');
    els.chatOverlay?.classList.remove('hidden');
    document.body.style.overflow = 'hidden';
    els.queryInput.focus();
    scrollToBottom();
}

function closeChat() {
    if (!isOpen) return;
    isOpen = false;
    els.chatToggle.classList.remove('active');
    els.chatPanel.classList.add('hidden');
    els.chatPanel.setAttribute('aria-hidden', 'true');
    els.chatOverlay?.classList.add('hidden');
    document.body.style.overflow = '';
}

function toggleChat() {
    if (isOpen) closeChat(); else openChat();
}

/* ============================================================
   Welcome Message
   ============================================================ */
function renderWelcome() {
    // Only add welcome if messages area is empty
    if (els.messages.children.length > 0) return;
    addMessage('bot', `
        Hi! I'm your Groww Mutual Fund Assistant. Ask me anything about HDFC schemes — expense ratio, exit load, SIP, ELSS lock-in, riskometer, or how to download your statement.
        <br><br>
        <strong>Facts-only. No investment advice.</strong>
    `);
}

/* ============================================================
   Schemes
   ============================================================ */
async function loadSchemes() {
    try {
        const res = await fetch(`${API_BASE}/api/schemes`);
        if (!res.ok) throw new Error('Failed to load schemes');
        const data = await res.json();
        data.schemes.forEach(s => {
            const opt = document.createElement('option');
            opt.value = s.name;
            opt.textContent = s.name;
            els.schemeSelect.appendChild(opt);
        });
    } catch (e) {
        console.warn('Could not load schemes:', e);
    }
}

/* ============================================================
   Send / Receive
   ============================================================ */
async function handleSend() {
    const query = els.queryInput.value.trim();
    if (!query || isLoading) return;

    if (abortController) abortController.abort();
    abortController = new AbortController();

    currentQuery = query;
    hideSuggestions();

    addMessage('user', escapeHtml(query));
    els.queryInput.value = '';
    updateCharCount();
    scrollToBottom();

    setLoading(true);

    try {
        const res = await fetch(`${API_BASE}/api/query`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                query: query,
                scheme: els.schemeSelect.value || null
            }),
            signal: abortController.signal
        });

        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(err.detail || `Server error (${res.status})`);
        }

        const data = await res.json();
        currentAnswer = data.answer || '';
        renderBotResponse(data);
        saveToHistory(query, data);
    } catch (e) {
        if (e.name === 'AbortError') return;
        showError(e.message || 'Failed to get a response. Please try again.');
    } finally {
        setLoading(false);
        abortController = null;
    }
}

/* ============================================================
   Rendering
   ============================================================ */
function renderBotResponse(data) {
    const parts = [];

    parts.push(`<div>${escapeHtml(data.answer || 'No answer available.')}</div>`);

    if (data.source && data.source.trim()) {
        parts.push(
            `<div class="message-source">` +
            `<strong>Source:</strong> <a href="${escapeHtml(data.source)}" target="_blank" rel="noopener noreferrer">${escapeHtml(data.source)}</a>` +
            `</div>`
        );
    }

    const badges = [];
    if (data.route) {
        const rc = data.route === 'guardrail' ? 'guardrail' : 'retrieval';
        badges.push(`<span class="badge ${rc}">${escapeHtml(data.route)}</span>`);
    }
    if (typeof data.confidence === 'number') {
        const cc = data.confidence >= 0.7 ? 'confident' : 'uncertain';
        badges.push(`<span class="badge ${cc}">${data.confidence >= 0.7 ? 'High Confidence' : 'Low Confidence'}</span>`);
    }
    if (typeof data.include_url === 'boolean') {
        const uc = data.include_url ? 'include-url' : 'no-url';
        badges.push(`<span class="badge ${uc}">${data.include_url ? 'Source Included' : 'No Source'}</span>`);
    }
    if (badges.length) {
        parts.push(`<div class="message-meta">${badges.join('')}</div>`);
    }

    parts.push(renderFeedbackUI());

    addMessage('bot', parts.join(''));
    scrollToBottom();
}

function showError(msg) {
    const el = addMessage('bot', `
        <div style="display:flex;align-items:center;gap:8px;">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
            <span>${escapeHtml(msg)}</span>
        </div>
    `);
    el.classList.add('error-message');
    scrollToBottom();
}

/* ============================================================
   Messages
   ============================================================ */
function addMessage(role, htmlContent) {
    const msg = document.createElement('div');
    msg.className = `message ${role}-message`;
    msg.innerHTML = `<div class="message-bubble">${htmlContent}</div>`;
    els.messages.appendChild(msg);
    scrollToBottom();
    return msg;
}

function addTypingIndicator() {
    const msg = document.createElement('div');
    msg.className = 'message bot-message typing-message';
    msg.innerHTML = `
        <div class="message-bubble">
            <div class="typing-indicator"><span></span><span></span><span></span></div>
        </div>
    `;
    els.messages.appendChild(msg);
    scrollToBottom();
    return msg;
}

function removeTypingIndicator() {
    const el = els.messages.querySelector('.typing-message');
    if (el) el.remove();
}

function scrollToBottom() {
    requestAnimationFrame(() => {
        els.messages.scrollTop = els.messages.scrollHeight;
    });
}

/* ============================================================
   Loading State
   ============================================================ */
function setLoading(loading) {
    isLoading = loading;
    els.sendBtn.disabled = loading || !els.queryInput.value.trim();
    if (loading) {
        addTypingIndicator();
    } else {
        removeTypingIndicator();
    }
}

/* ============================================================
   Suggestions
   ============================================================ */
function hideSuggestions() {
    els.chips.classList.add('hidden');
}

/* ============================================================
   Input helpers
   ============================================================ */
function updateCharCount() {
    const len = els.queryInput.value.length;
    const max = els.queryInput.maxLength;
    els.sendBtn.disabled = !len || isLoading;
    if (!len) {
        els.charCount.textContent = '';
        return;
    }
    els.charCount.textContent = `${len}/${max}`;
    els.charCount.classList.toggle('warn', len > max * 0.9);
}

/* ============================================================
   Inline Feedback
   ============================================================ */
function renderFeedbackUI() {
    const id = 'fb-' + Date.now() + '-' + Math.random().toString(36).slice(2, 6);
    return `
        <div class="feedback-inline" id="${id}">
            <span>Was this helpful?</span>
            <button data-rating="1" onclick="submitFeedbackInline(this, 1, '${id}')">Yes</button>
            <button data-rating="0" onclick="submitFeedbackInline(this, 0, '${id}')">No</button>
        </div>
    `;
}

window.submitFeedbackInline = async function(btn, rating, id) {
    const container = document.getElementById(id);
    if (!container) return;
    container.querySelectorAll('button').forEach(b => b.classList.remove('selected'));
    btn.classList.add('selected');
    try {
        const res = await fetch(`${API_BASE}/api/feedback`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                query: currentQuery,
                answer: currentAnswer,
                rating: rating,
                comment: null
            })
        });
        if (res.ok) {
            container.innerHTML = '<span class="feedback-thanks">Thanks for your feedback!</span>';
        } else {
            throw new Error('Failed');
        }
    } catch (e) {
        console.warn('Feedback failed:', e);
    }
};

/* ============================================================
   History (sessionStorage)
   ============================================================ */
function saveToHistory(query, data) {
    messageHistory.push({ query, answer: data.answer, time: new Date().toISOString() });
    if (messageHistory.length > 50) messageHistory = messageHistory.slice(-50);
    sessionStorage.setItem('mfChatHistory', JSON.stringify(messageHistory));
}

function restoreHistory() {
    if (messageHistory.length === 0) return;
    const recent = messageHistory.slice(-20);
    recent.forEach(item => {
        addMessage('user', escapeHtml(item.query));
        addMessage('bot', escapeHtml(item.answer));
    });
    scrollToBottom();
}

/* ============================================================
   Utils
   ============================================================ */
function escapeHtml(text) {
    if (typeof text !== 'string') return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
