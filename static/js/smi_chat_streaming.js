// Streaming-capable SMI chat UI script
// - Sends POST with FormData
// - Reads response stream (chunked) and appends partial assistant output
// - Abortable via stop button
// - Falls back to JSON/text responses when streaming not available
// - Defensive: tolerates missing elements/variables

(function () {
  'use strict';

  // Helpers
  const $ = id => document.getElementById(id);
  const safe = (el, fn) => { try { if (el) fn(el); } catch (e) { console.error('UI handler error', e); } };

  // Server-injected variables (guarded)
  const _csrfToken = (typeof csrfToken !== 'undefined') ? csrfToken : null;
  const _streamUrl = (typeof streamUrl !== 'undefined') ? streamUrl : null;
  const _conversationsUrl = (typeof conversationsUrl !== 'undefined') ? conversationsUrl : null;

  // Elements
  const form = $('chat-form'), messages = $('messages');
  const sendBtn = $('send'), stopBtn = $('stop-button'), statusEl = $('status');
  const messageInput = $('message'), imageInput = $('image-input'), mediaInput = $('media-input');
  const plusBtn = $('plus-button'), attachmentMenu = $('attachment-menu');
  const historyList = $('history-list'), historyStatus = $('history-status');
  const menuCodeBtn = $('menu-code'), menuSpeakBtn = $('menu-speak');
  const previewImage = $('image-preview'), previewImg = $('preview-img'), previewName = $('preview-name'), removeImageBtn = $('remove-image');
  const previewMedia = $('media-preview'), previewMediaName = $('media-name'), removeMediaBtn = $('remove-media');

  // State
  let conversationId = null;
  let selectedImage = null;
  let selectedAttachment = null;
  let readAloud = true;
  let codeMode = false;
  let abortController = null;

  // Resize textarea
  safe(messageInput, el => el.addEventListener('input', function () {
    this.style.height = 'auto';
    this.style.height = (this.scrollHeight) + 'px';
    if (this.value === '') this.style.height = 'auto';
  }));

  // Attachment menu toggle
  safe(plusBtn, btn => btn.addEventListener('click', (e) => {
    e.stopPropagation();
    if (attachmentMenu) attachmentMenu.classList.toggle('show');
  }));
  document.addEventListener('click', (e) => {
    if (attachmentMenu && !attachmentMenu.contains(e.target) && e.target !== plusBtn) {
      attachmentMenu.classList.remove('show');
    }
  });

  // Menu items
  safe($('menu-image'), btn => btn.addEventListener('click', () => { if (imageInput) imageInput.click(); if (attachmentMenu) attachmentMenu.classList.remove('show'); }));
  safe($('menu-file'), btn => btn.addEventListener('click', () => { if (mediaInput) mediaInput.click(); if (attachmentMenu) attachmentMenu.classList.remove('show'); }));

  // Toggle Code Mode
  safe(menuCodeBtn, btn => btn.addEventListener('click', () => {
    codeMode = !codeMode;
    btn.classList.toggle('active', codeMode);
    if (messageInput) {
      messageInput.placeholder = codeMode
        ? "Write your code proposal..."
        : "Type your recommendation request, or attach images/videos/PDFs/audio/QR codes...";
    }
  }));

  // Toggle Read Aloud
  safe(menuSpeakBtn, btn => btn.addEventListener('click', () => {
    readAloud = !readAloud;
    btn.classList.toggle('active', readAloud);
  }));

  // Image preview
  safe(imageInput, input => input.addEventListener('change', (ev) => {
    try {
      const f = ev.target.files && ev.target.files[0];
      if (!f) return;
      selectedImage = f;
      if (previewImage && previewImg && previewName) {
        previewImg.src = URL.createObjectURL(f);
        previewImg.onload = () => URL.revokeObjectURL(previewImg.src);
        previewName.textContent = f.name;
        previewImage.classList.add('show');
      }
    } catch (e) { console.error('image handler', e); }
  }));

  // Media preview
  safe(mediaInput, input => input.addEventListener('change', (ev) => {
    try {
      const f = ev.target.files && ev.target.files[0];
      if (!f) return;
      selectedAttachment = f;
      if (previewMedia && previewMediaName) {
        previewMediaName.textContent = f.name;
        previewMedia.classList.add('show');
      }
    } catch (e) { console.error('media handler', e); }
  }));

  // Remove previews
  safe(removeImageBtn, btn => btn.addEventListener('click', () => {
    selectedImage = null;
    if (previewImage) previewImage.classList.remove('show');
    if (imageInput) imageInput.value = '';
  }));
  safe(removeMediaBtn, btn => btn.addEventListener('click', () => {
    selectedAttachment = null;
    if (previewMedia) previewMedia.classList.remove('show');
    if (mediaInput) mediaInput.value = '';
  }));

  // New chat button (clear)
  safe($('new-chat'), btn => btn.addEventListener('click', () => {
    conversationId = null;
    if (messages) messages.innerHTML = '<div class="msg assistant">Sovereign Megaverse Intelligence is ready. Ask about OAP architecture, code, infrastructure, products, or strategy.</div>';
  }));

  // History loader (safe)
  async function loadHistory() {
    if (!_conversationsUrl || !historyList) {
      safe(historyStatus, s => s.textContent = 'Conversation history not available.');
      return;
    }
    try {
      historyStatus && (historyStatus.textContent = 'Loading signed-session history…');
      const res = await fetch(_conversationsUrl, { credentials: 'same-origin' });
      if (!res.ok) {
        historyStatus && (historyStatus.textContent = 'No history found.');
        return;
      }
      const data = await res.json().catch(() => null);
      if (!data || !Array.isArray(data)) {
        historyStatus && (historyStatus.textContent = 'No history.');
        return;
      }
      historyList.innerHTML = '';
      data.forEach((item) => {
        const div = document.createElement('div');
        div.className = 'history-item';
        const btn = document.createElement('button');
        btn.className = 'history-open';
        btn.innerHTML = `<span class="history-title">${item.title || 'Conversation'}</span><span class="history-preview">${item.preview || ''}</span>`;
        btn.addEventListener('click', () => {
          conversationId = item.id || null;
          if (messages) messages.innerHTML = `<div class="msg assistant">Loaded conversation: ${item.title || 'Conversation'}</div>`;
        });
        const del = document.createElement('button');
        del.className = 'history-delete';
        del.innerHTML = '✕';
        del.title = 'Delete';
        del.addEventListener('click', () => alert('Delete conversation not implemented in this UI.'));
        div.appendChild(btn);
        div.appendChild(del);
        historyList.appendChild(div);
      });
      historyStatus && (historyStatus.textContent = '');
    } catch (e) {
      console.error('loadHistory error', e);
      historyStatus && (historyStatus.textContent = 'Failed to load history.');
    }
  }

  // Append message helper
  function appendMessageNode(role, initialText = '') {
    if (!messages) return null;
    const d = document.createElement('div');
    d.className = `msg ${role === 'user' ? 'user' : role === 'assistant' ? 'assistant' : 'system'}`;
    const inner = document.createElement('div');
    inner.className = 'msg-text';
    inner.textContent = initialText;
    d.appendChild(inner);
    messages.appendChild(d);
    messages.scrollTop = messages.scrollHeight;
    return inner; // return the inner element so we can update it
  }

  // Stop (abort)
  safe(stopBtn, btn => btn.addEventListener('click', () => {
    try {
      if (abortController) abortController.abort();
      btn.style.display = 'none';
    } catch (e) { console.error('stop handler', e); }
  }));

  // Streaming parser helpers
  function decodeStream(reader, onChunk, onDone, onError, signal) {
    const utf8Decoder = new TextDecoder('utf-8');
    let buffer = '';
    function pump() {
      return reader.read().then(({ done, value }) => {
        if (done) {
          if (buffer.length) {
            // final flush
            onChunk(buffer);
            buffer = '';
          }
          onDone();
          return;
        }
        if (value) {
          buffer += utf8Decoder.decode(value, { stream: true });
          // heuristics:
          // 1) try to split on double-newline blocks (SSE/data style) and handle lines beginning with "data:"
          // 2) otherwise yield whatever is present
          let idx;
          while ((idx = buffer.indexOf('\n\n')) !== -1) {
            const block = buffer.slice(0, idx);
            buffer = buffer.slice(idx + 2);
            // handle SSE-like "data: ..." lines
            if (block.startsWith('data:')) {
              const dataLines = block.split('\n').map(l => l.replace(/^data:\s?/, '')).join('\n');
              onChunk(dataLines);
            } else {
              onChunk(block);
            }
          }
          // if buffer grows very large without separators, flush a safe chunk
          if (buffer.length > 8192) {
            onChunk(buffer);
            buffer = '';
          }
        }
        if (signal && signal.aborted) {
          reader.cancel().catch(() => {});
          onError && onError(new DOMException('Aborted', 'AbortError'));
          return;
        }
        return pump();
      }).catch(err => {
        onError && onError(err);
      });
    }
    pump();
  }

  // Submit handler: uses streaming when possible
  safe(form, frm => frm.addEventListener('submit', async (e) => {
    e.preventDefault();
    try {
      const text = messageInput ? messageInput.value.trim() : '';
      if (!text && !selectedImage && !selectedAttachment) return;

      // append user message
      appendMessageNode('user', text || (selectedImage ? ('Image: ' + selectedImage.name) : ('File: ' + (selectedAttachment && selectedAttachment.name))));

      // abort any previous request
      if (abortController) abortController.abort();
      abortController = new AbortController();
      safe(stopBtn, b => b.style.display = 'inline-flex');

      // prepare form data
      const fd = new FormData();
      if (text) fd.append('message', text);
      if (selectedImage) fd.append('image', selectedImage, selectedImage.name);
      if (selectedAttachment) fd.append('attachment', selectedAttachment, selectedAttachment.name);
      if (conversationId) fd.append('conversation_id', conversationId);
      fd.append('code_mode', codeMode ? '1' : '0');

      const headers = {};
      if (_csrfToken) headers['X-CSRF-Token'] = _csrfToken;

      // choose endpoint: prefer streamUrl if provided, otherwise conversationsUrl, otherwise form action or current URL
      const endpoint = _streamUrl || _conversationsUrl || (frm.getAttribute('action') || window.location.href);

      // Start fetch
      const res = await fetch(endpoint, {
        method: 'POST',
        headers,
        body: fd,
        signal: abortController.signal,
        credentials: 'same-origin'
      });

      if (!res.ok) {
        const textErr = await res.text().catch(() => 'Server error');
        appendMessageNode('assistant', 'Request failed: ' + (res.status + ' ' + res.statusText));
        console.error('Send failed', res.status, res.statusText, textErr);
        safe(stopBtn, b => b.style.display = 'none');
        return;
      }

      // If response has no body or body is not readable, fallback to text/json
      if (!res.body || !res.body.getReader) {
        // non-streaming fallback
        let replyText = '';
        try {
          const j = await res.json().catch(() => null);
          replyText = (j && j.reply) ? j.reply : (j ? JSON.stringify(j) : '');
        } catch (_) {
          replyText = await res.text().catch(() => '');
        }
        appendMessageNode('assistant', replyText || '(no response)');
        safe(stopBtn, b => b.style.display = 'none');
        return;
      }

      // Streaming path: create assistant node then read stream
      const assistantNode = appendMessageNode('assistant', '');
      const reader = res.body.getReader();
      let finished = false;
      let accumulated = '';

      // Provide a function to process each incoming chunk
      const onChunk = (chunkText) => {
        // Attempt to parse JSON chunks if they look like JSON objects or lines with JSON
        let textChunk = String(chunkText);
        // Some servers send SSE "data: {...}\n\n" or newline-separated JSON lines.
        // Try to extract JSON if chunk starts with "{" or "[".
        const trimmed = textChunk.trim();
        if (trimmed.startsWith('{') || trimmed.startsWith('[')) {
          try {
            const parsed = JSON.parse(trimmed);
            // If parsed contains reply text, use it; otherwise stringify
            const reply = parsed.reply || parsed.data || parsed.text || parsed.content || JSON.stringify(parsed);
            accumulated += reply;
          } catch (e) {
            // not valid JSON: just append raw
            accumulated += textChunk;
          }
        } else {
          // Not JSON-looking chunk: append directly
          accumulated += textChunk;
        }
        if (assistantNode) {
          assistantNode.textContent = accumulated;
          // scroll
          if (messages) messages.scrollTop = messages.scrollHeight;
        }
      };

      const onDone = () => {
        finished = true;
        safe(stopBtn, b => b.style.display = 'none');
        // optional speak
        if (readAloud && accumulated && window.speechSynthesis) {
          try {
            const ut = new SpeechSynthesisUtterance(accumulated);
            window.speechSynthesis.cancel();
            window.speechSynthesis.speak(ut);
          } catch (e) { console.error('speech synthesis error', e); }
        }
        // clear inputs
        if (messageInput) { messageInput.value = ''; messageInput.dispatchEvent(new Event('input')); }
        selectedImage = null; if (previewImage) previewImage.classList.remove('show'); if (imageInput) imageInput.value = '';
        selectedAttachment = null; if (previewMedia) previewMedia.classList.remove('show'); if (mediaInput) mediaInput.value = '';
      };

      const onError = (err) => {
        console.error('stream read error', err);
        safe(stopBtn, b => b.style.display = 'none');
        if (!finished && assistantNode) {
          assistantNode.textContent += '\n\n[Stream ended with error]';
        }
      };

      decodeStream(reader, onChunk, onDone, onError, abortController.signal);

    } catch (err) {
      if (err && err.name === 'AbortError') {
        appendMessageNode('system', 'Request aborted.');
      } else {
        console.error('submit error', err);
        appendMessageNode('assistant', 'An error occurred while sending your request.');
      }
      safe(stopBtn, b => b.style.display = 'none');
    }
  }));

  // Initialize UI placeholders and load history
  try {
    if (messageInput) {
      messageInput.placeholder = codeMode
        ? "Write your code proposal..."
        : "Type your recommendation request, or attach images/videos/PDFs/audio/QR codes...";
    }
    if (menuCodeBtn) menuCodeBtn.classList.toggle('active', codeMode);
    if (menuSpeakBtn) menuSpeakBtn.classList.toggle('active', readAloud);
    safe(stopBtn, b => b.style.display = 'none');
    loadHistory().catch(e => console.error('loadHistory top-level', e));
  } catch (e) {
    console.error('UI init error', e);
  }

  // Global logging
  window.addEventListener('error', ev => console.error('Uncaught error:', ev.error || ev.message || ev));
  window.addEventListener('unhandledrejection', ev => console.error('Unhandled promise rejection:', ev.reason));

})();
