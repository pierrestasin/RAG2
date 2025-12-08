// Configuration
const API_URL = window.location.hostname === 'localhost'
    ? 'http://localhost:8000'
    : 'https://rag2-vbo5.onrender.com';

// State
let documents = [];
let selectedFiles = [];
let chatHistory = [];
let availableModels = {};

// DOM Elements
const uploadZone = document.getElementById('uploadZone');
const fileInput = document.getElementById('fileInput');
const documentList = document.getElementById('documentList');
const emptyState = document.getElementById('emptyState');
const docsLoading = document.getElementById('docsLoading');
const selectAllContainer = document.getElementById('selectAllContainer');
const selectAllBtn = document.getElementById('selectAllBtn');
const modelSelect = document.getElementById('modelSelect');
const chatHistoryEl = document.getElementById('chatHistory');
const chatForm = document.getElementById('chatForm');
const questionInput = document.getElementById('questionInput');
const sendBtn = document.getElementById('sendBtn');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadModels();
    loadDocuments();
    setupEventListeners();
});

// Event Listeners
function setupEventListeners() {
    // Upload Zone
    uploadZone.addEventListener('click', () => fileInput.click());
    uploadZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadZone.style.borderColor = 'var(--primary-color)';
    });
    uploadZone.addEventListener('dragleave', () => {
        uploadZone.style.borderColor = 'var(--border)';
    });
    uploadZone.addEventListener('drop', handleDrop);
    fileInput.addEventListener('change', handleFileSelect);

    // Select All
    selectAllBtn.addEventListener('click', toggleSelectAll);

    // Chat Form
    chatForm.addEventListener('submit', handleSubmit);
}

// Model Management
async function loadModels() {
    try {
        const response = await fetch(`${API_URL}/models`);
        availableModels = await response.json();
        renderModelSelect();
    } catch (error) {
        console.error('Error loading models:', error);
        showNotification('Error loading models', 'error');
    }
}

function renderModelSelect() {
    if (!modelSelect) return;

    // Vide le select
    modelSelect.innerHTML = '';

    // Ajoute les modèles par provider
    Object.entries(availableModels).forEach(([provider, data]) => {
        const optgroup = document.createElement('optgroup');
        optgroup.label = data.provider;

        data.models.forEach(model => {
            const option = document.createElement('option');
            option.value = model.id;
            option.textContent = model.name;
            optgroup.appendChild(option);
        });

        modelSelect.appendChild(optgroup);
    });

    // Sélectionne un modèle par défaut (le premier Gemini disponible)
    const defaultModel = availableModels.google?.models[0]?.id ||
                        availableModels.anthropic?.models[0]?.id ||
                        availableModels.openai?.models[0]?.id;
    if (defaultModel) {
        modelSelect.value = defaultModel;
    }
}

// File Handling
async function handleDrop(e) {
    e.preventDefault();
    uploadZone.style.borderColor = 'var(--border)';

    const files = Array.from(e.dataTransfer.files).filter(f => f.name.endsWith('.pdf'));
    if (files.length > 0) {
        await uploadFiles(files);
    }
}

async function handleFileSelect(e) {
    const files = Array.from(e.target.files);
    if (files.length > 0) {
        await uploadFiles(files);
    }
    fileInput.value = ''; // Reset input
}

async function uploadFiles(files) {
    for (const file of files) {
        await uploadFile(file);
    }
    await loadDocuments();
}

async function uploadFile(file) {
    const formData = new FormData();
    formData.append('file', file);

    try {
        showNotification(`Uploading ${file.name}...`, 'info');

        const response = await fetch(`${API_URL}/upload`, {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (response.ok) {
            showNotification(`✓ ${file.name} uploaded successfully`, 'success');
        } else {
            showNotification(`✗ ${data.detail || 'Upload failed'}`, 'error');
        }
    } catch (error) {
        showNotification(`✗ Error uploading ${file.name}`, 'error');
        console.error('Upload error:', error);
    }
}

// Document Management
async function loadDocuments() {
    docsLoading.style.display = 'flex';
    emptyState.style.display = 'none';

    try {
        const response = await fetch(`${API_URL}/documents`);
        const data = await response.json();

        documents = data.documents || [];
        renderDocuments();
    } catch (error) {
        console.error('Error loading documents:', error);
        showNotification('Error loading documents', 'error');
    } finally {
        docsLoading.style.display = 'none';
    }
}

function renderDocuments() {
    if (documents.length === 0) {
        documentList.innerHTML = '<div class="empty-state"><p>No documents yet</p><p>Upload PDFs to get started</p></div>';
        selectAllContainer.style.display = 'none';
        questionInput.disabled = true;
        sendBtn.disabled = true;
        return;
    }

    documentList.innerHTML = documents.map(doc => `
        <div class="document-item ${selectedFiles.includes(doc.filename) ? 'selected' : ''}"
             data-filename="${doc.filename}">
            <input type="checkbox"
                   class="document-checkbox"
                   ${selectedFiles.includes(doc.filename) ? 'checked' : ''}
                   data-filename="${doc.filename}">
            <div class="document-info">
                <div class="document-name" title="${doc.filename}">${doc.filename}</div>
                <div class="document-meta">${doc.pages} pages • ${doc.chunks} chunks</div>
            </div>
            <button class="delete-btn" data-filename="${doc.filename}" title="Delete">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                    <polyline points="3 6 5 6 21 6"></polyline>
                    <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                </svg>
            </button>
        </div>
    `).join('');

    selectAllContainer.style.display = 'block';
    questionInput.disabled = false;
    sendBtn.disabled = false;

    // Add event listeners
    document.querySelectorAll('.document-item').forEach(item => {
        const checkbox = item.querySelector('.document-checkbox');
        const deleteBtn = item.querySelector('.delete-btn');

        item.addEventListener('click', (e) => {
            if (e.target === deleteBtn || e.target.closest('.delete-btn')) return;
            checkbox.checked = !checkbox.checked;
            toggleDocument(checkbox.dataset.filename);
        });

        checkbox.addEventListener('click', (e) => {
            e.stopPropagation();
            toggleDocument(e.target.dataset.filename);
        });

        deleteBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            deleteDocument(e.target.closest('.delete-btn').dataset.filename);
        });
    });
}

function toggleDocument(filename) {
    if (selectedFiles.includes(filename)) {
        selectedFiles = selectedFiles.filter(f => f !== filename);
    } else {
        selectedFiles.push(filename);
    }
    renderDocuments();
}

function toggleSelectAll() {
    if (selectedFiles.length === documents.length) {
        selectedFiles = [];
    } else {
        selectedFiles = documents.map(d => d.filename);
    }
    renderDocuments();
}

async function deleteDocument(filename) {
    if (!confirm(`Delete ${filename}?`)) return;

    try {
        const response = await fetch(`${API_URL}/documents/${encodeURIComponent(filename)}`, {
            method: 'DELETE'
        });

        if (response.ok) {
            showNotification(`✓ ${filename} deleted`, 'success');
            selectedFiles = selectedFiles.filter(f => f !== filename);
            await loadDocuments();
        } else {
            const data = await response.json();
            showNotification(`✗ ${data.detail || 'Delete failed'}`, 'error');
        }
    } catch (error) {
        showNotification('✗ Error deleting document', 'error');
        console.error('Delete error:', error);
    }
}

// Chat
async function handleSubmit(e) {
    e.preventDefault();

    const question = questionInput.value.trim();
    if (!question) return;

    // Vérification : au moins un document doit être sélectionné
    if (selectedFiles.length === 0) {
        addMessage('assistant', '⚠️ Please select at least one document before asking a question.\n\nUse the checkboxes on the left to select which documents you want to search.', null);
        return;
    }

    const model = modelSelect.value;

    // Add user message
    addMessage('user', question);
    questionInput.value = '';
    questionInput.disabled = true;
    sendBtn.disabled = true;

    // Show loading
    const loadingId = addLoadingMessage();

    try {
        const response = await fetch(`${API_URL}/query`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                question,
                model,
                selected_files: selectedFiles
            })
        });

        const data = await response.json();

        // Debug: log sources
        console.log('Response data:', data);
        console.log('Sources:', data.sources);

        // Remove loading
        removeMessage(loadingId);

        if (response.ok) {
            addMessage('assistant', data.answer, data.model_used, data.sources, data.tokens_used);
        } else {
            addMessage('assistant', `Error: ${data.detail || 'Query failed'}`, model);
        }
    } catch (error) {
        removeMessage(loadingId);
        addMessage('assistant', 'Error: Failed to connect to server', model);
        console.error('Query error:', error);
    } finally {
        questionInput.disabled = false;
        sendBtn.disabled = false;
        questionInput.focus();
    }
}

function addMessage(role, content, model = null, sources = [], tokens = null) {
    const messageId = Date.now();

    const welcomeMsg = chatHistoryEl.querySelector('.welcome-message');
    if (welcomeMsg) {
        welcomeMsg.remove();
    }

    const messageEl = document.createElement('div');
    messageEl.className = `message ${role}`;
    messageEl.dataset.id = messageId;

    let html = `
        <div class="message-avatar">${role === 'user' ? '👤' : '🤖'}</div>
        <div class="message-content">
            <div class="message-header">
                <span class="message-role">${role === 'user' ? 'You' : 'Assistant'}</span>
                ${model ? `<span class="message-model">(${model})</span>` : ''}
                ${tokens ? `<span class="message-model">• ${tokens} tokens</span>` : ''}
            </div>
            <div class="message-text">${escapeHtml(content)}</div>
    `;

    if (sources && sources.length > 0) {
        html += `
            <div class="message-sources">
                <h4>📚 Sources (${sources.length})</h4>
                ${sources.map(source => {
                    // Format les pages
                    const pagesDisplay = source.pages
                        ? (source.pages.length === 1
                            ? `Page ${source.pages[0]}`
                            : source.pages.length <= 3
                                ? `Pages ${source.pages.join(', ')}`
                                : `Pages ${source.pages.slice(0, 3).join(', ')}... (${source.pages.length} pages)`)
                        : 'Page inconnue';

                    return `
                        <div class="source-item">
                            <div class="source-header">
                                <span>${source.filename}</span>
                                <span class="source-score">${pagesDisplay}</span>
                            </div>
                        </div>
                    `;
                }).join('')}
            </div>
        `;
    }

    html += `</div></div>`;
    messageEl.innerHTML = html;

    chatHistoryEl.appendChild(messageEl);
    chatHistoryEl.scrollTop = chatHistoryEl.scrollHeight;

    return messageId;
}

function addLoadingMessage() {
    const messageId = Date.now();

    const messageEl = document.createElement('div');
    messageEl.className = 'message assistant';
    messageEl.dataset.id = messageId;
    messageEl.innerHTML = `
        <div class="message-avatar">🤖</div>
        <div class="message-content">
            <div class="message-header">
                <span class="message-role">Assistant</span>
            </div>
            <div class="message-text">
                <div class="loading">
                    <div class="spinner"></div>
                    <p>Thinking...</p>
                </div>
            </div>
        </div>
    `;

    chatHistoryEl.appendChild(messageEl);
    chatHistoryEl.scrollTop = chatHistoryEl.scrollHeight;

    return messageId;
}

function removeMessage(messageId) {
    const messageEl = chatHistoryEl.querySelector(`[data-id="${messageId}"]`);
    if (messageEl) {
        messageEl.remove();
    }
}

// Utilities
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function showNotification(message, type = 'info') {
    // Simple console notification for now
    console.log(`[${type.toUpperCase()}] ${message}`);

    // You could implement a toast notification here
}
