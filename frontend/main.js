// Jarvis V2 — HUD Frontend
const orb = document.getElementById('orb');
const statusEl = document.getElementById('status');
const stateLabel = document.getElementById('state-label');
const talkBtn = document.getElementById('talk-btn');
const transcriptUser = document.getElementById('transcript-user');
const transcriptJarvis = document.getElementById('transcript-jarvis');
const timeDisplay = document.getElementById('time-display');
const connStatus = document.getElementById('connection-status');

let ws;
let audioQueue = [];
let isPlaying = false;
let audioUnlocked = false;
let mode = 'init';
let isListening = false;
let speechDetected = false;
let conversationMode = false;

// Live clock
function updateClock() {
    timeDisplay.textContent = new Date().toLocaleTimeString('de-DE');
}
updateClock();
setInterval(updateClock, 1000);

// Unlock audio context on first interaction
function unlockAudio() {
    if (!audioUnlocked) {
        const silent = new Audio('data:audio/mp3;base64,SUQzBAAAAAAAI1RTU0UAAAAPAAADTGF2ZjU4Ljc2LjEwMAAAAAAAAAAAAAAA//tQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAWGluZwAAAA8AAAACAAABhgC7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7//////////////////////////////////////////////////////////////////8AAAAATGF2YzU4LjEzAAAAAAAAAAAAAAAAJAAAAAAAAAAAAYZNIGPkAAAAAAAAAAAAAAAAAAAA//tQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAWGluZwAAAA8AAAACAAABhgC7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7//////////////////////////////////////////////////////////////////8AAAAATGF2YzU4LjEzAAAAAAAAAAAAAAAAJAAAAAAAAAAAAYZNIGPkAAAAAAAAAAAAAAAAAAAA');
        silent.play().then(() => { audioUnlocked = true; }).catch(() => {});
    }
}
document.addEventListener('click', unlockAudio, { once: false });
document.addEventListener('touchstart', unlockAudio, { once: false });
document.addEventListener('keydown', unlockAudio, { once: false });

// ── STATE MACHINE ──

function updateTalkBtn() {
    if (conversationMode) {
        talkBtn.textContent = '■ KONVERSATION BEENDEN';
        talkBtn.classList.add('conv-active');
    } else {
        talkBtn.textContent = '◈ JARVIS SPRECHEN';
        talkBtn.classList.remove('conv-active');
    }
}

function enterStandby() {
    if (isListening) {
        try { recognition.stop(); } catch(e) {}
        isListening = false;
    }
    // In Konversationsmodus: nach Antwort direkt wieder zuhören
    if (conversationMode && mode !== 'greeting') {
        mode = 'standby';
        setTimeout(() => { if (conversationMode) enterListening(); }, 400);
        return;
    }
    mode = 'standby';
    setOrbState('standby');
    setStateLabel('STANDBY');
    statusEl.textContent = '';
    updateTalkBtn();
    talkBtn.classList.remove('hidden');
}

function enterListening() {
    if (isPlaying) return;
    mode = 'listening';
    speechDetected = false;
    setOrbState('listening');
    setStateLabel('LISTENING');
    statusEl.textContent = 'Sprechen Sie...';
    updateTalkBtn();
    talkBtn.classList.remove('hidden');
    try {
        recognition.start();
        isListening = true;
    } catch(e) {
        enterStandby();
    }
}

// ── WEBSOCKET ──

function connect() {
    ws = new WebSocket(`ws://${location.host}/ws`);

    ws.onopen = () => {
        connStatus.textContent = '■ ONLINE';
        connStatus.style.color = '#00ff99';
        connStatus.style.textShadow = '0 0 8px #00ff99';
        mode = 'greeting';
        setOrbState('thinking');
        setStateLabel('INITIALIZING');
        statusEl.textContent = 'System online...';
        ws.send(JSON.stringify({ text: 'Jarvis activate' }));
    };

    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'response') {
            addMessage('jarvis', data.text);
            if (data.audio && data.audio.length > 0) {
                queueAudio(data.audio);
            } else {
                enterStandby();
            }
        } else if (data.type === 'status') {
            statusEl.textContent = data.text;
        }
    };

    ws.onclose = () => {
        connStatus.textContent = '■ OFFLINE';
        connStatus.style.color = '#ff4444';
        connStatus.style.textShadow = '0 0 8px #ff4444';
        statusEl.textContent = 'Verbindung verloren...';
        setOrbState('standby');
        talkBtn.classList.add('hidden');
        setTimeout(connect, 3000);
    };
}

// ── AUDIO QUEUE ──

function queueAudio(base64Audio) {
    audioQueue.push(base64Audio);
    if (!isPlaying) playNext();
}

function playNext() {
    if (audioQueue.length === 0) {
        isPlaying = false;
        setTimeout(enterStandby, 400);
        return;
    }
    isPlaying = true;
    setOrbState('speaking');
    setStateLabel('SPEAKING');
    statusEl.textContent = '';
    if (isListening) {
        try { recognition.stop(); } catch(e) {}
        isListening = false;
    }
    if (conversationMode) talkBtn.classList.remove('hidden');

    const b64 = audioQueue.shift();
    const bytes = Uint8Array.from(atob(b64), c => c.charCodeAt(0));
    const blob = new Blob([bytes], { type: 'audio/mpeg' });
    const url = URL.createObjectURL(blob);
    const audio = new Audio(url);
    audio.onended = () => { URL.revokeObjectURL(url); playNext(); };
    audio.onerror = () => { URL.revokeObjectURL(url); playNext(); };
    audio.play().catch(() => {
        statusEl.textContent = 'Klicken Sie irgendwo — Jarvis muss sprechen.';
        setOrbState('standby');
        document.addEventListener('click', function retry() {
            document.removeEventListener('click', retry);
            audio.play().then(() => {
                setOrbState('speaking');
                setStateLabel('SPEAKING');
                statusEl.textContent = '';
            }).catch(() => playNext());
        });
    });
}

// ── SPEECH RECOGNITION ──

const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
let recognition;

if (SpeechRecognition) {
    recognition = new SpeechRecognition();
    recognition.lang = 'de-DE';
    recognition.continuous = false;
    recognition.interimResults = false;

    recognition.onresult = (event) => {
        const last = event.results[event.results.length - 1];
        if (last.isFinal) {
            const text = last[0].transcript.trim();
            if (text) {
                speechDetected = true;
                addMessage('user', text);
                mode = 'thinking';
                setOrbState('thinking');
                setStateLabel('PROCESSING');
                statusEl.textContent = 'Jarvis denkt...';
                talkBtn.classList.add('hidden');
                ws.send(JSON.stringify({ text }));
            }
        }
    };

    recognition.onend = () => {
        isListening = false;
        if (mode === 'listening' && !speechDetected) {
            if (conversationMode) {
                // Kein Sprache erkannt → kurz warten, dann wieder zuhören
                setTimeout(() => {
                    if (conversationMode && mode === 'listening') {
                        try { recognition.start(); isListening = true; } catch(e) { enterStandby(); }
                    }
                }, 150);
            } else {
                enterStandby();
            }
        }
        speechDetected = false;
    };

    recognition.onerror = (event) => {
        isListening = false;
        if (event.error !== 'aborted') {
            enterStandby();
        }
    };
}

// ── TALK BUTTON ──

talkBtn.addEventListener('click', () => {
    unlockAudio();
    if (conversationMode) {
        conversationMode = false;
        updateTalkBtn();
        enterStandby();
    } else {
        conversationMode = true;
        enterListening();
    }
});

// ── HELPERS ──

function setOrbState(state) { orb.className = state; }

function setStateLabel(text) {
    if (stateLabel) stateLabel.textContent = text;
}

function addMessage(role, text) {
    const container = role === 'user' ? transcriptUser : transcriptJarvis;
    const bubble = document.createElement('div');
    bubble.className = `msg-bubble ${role}`;

    const label = document.createElement('div');
    label.className = 'msg-label';
    label.textContent = role === 'user' ? '◈ INPUT' : '◈ JARVIS';
    bubble.appendChild(label);

    const content = document.createElement('div');
    content.textContent = text;
    bubble.appendChild(content);

    container.appendChild(bubble);
    container.scrollTop = container.scrollHeight;
}

connect();
