// Determine backend URL dynamically based on environment
const API_BASE = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1' 
  ? 'http://127.0.0.1:8000' 
  : 'https://nepali-converter-api.onrender.com'; // REPLACE WITH LIVE BACKEND URL

// --- DOM Elements ---
const sourceText = document.getElementById('sourceText');
const resultText = document.getElementById('resultText');
const copyBtn = document.getElementById('copyBtn');
const directionToggle = document.getElementById('directionToggle');
const detectedDirection = document.getElementById('detectedDirection');
const manualModeLabel = document.getElementById('manualModeLabel');
const autoDetectBadge = document.getElementById('autoDetectBadge');

const uploadZone = document.getElementById('uploadZone');
const fileInput = document.getElementById('fileInput');
const folderInput = document.getElementById('folderInput');
const fileList = document.getElementById('fileList');
const queueCount = document.getElementById('queueCount');

// --- State ---
let debounceTimer;
let isManualOverride = false;
let uploadQueue = [];
let isUploading = false;

// --- Auto-Detect Logic ---
function detectDirection(text) {
  // Check for Devanagari Unicode range (U+0900 to U+097F)
  const unicodeRegex = /[\u0900-\u097F]/;
  return unicodeRegex.test(text) ? 'unicode_to_preeti' : 'preeti_to_unicode';
}

function updateDirectionUI(direction, manual = false) {
  if (direction === 'unicode_to_preeti') {
    detectedDirection.textContent = 'Unicode → Preeti';
  } else {
    detectedDirection.textContent = 'Preeti → Unicode';
  }
  
  if (manual) {
    autoDetectBadge.style.opacity = '0.5';
    manualModeLabel.style.color = 'var(--accent-primary)';
  } else {
    autoDetectBadge.style.opacity = '1';
    manualModeLabel.style.color = 'var(--text-muted)';
  }
}

// --- Text Conversion ---
async function convertText() {
  const text = sourceText.value.trim();
  if (!text) {
    resultText.value = '';
    return;
  }

  let direction = 'auto';
  if (isManualOverride) {
    direction = directionToggle.checked ? 'preeti_to_unicode' : 'unicode_to_preeti';
  } else {
    direction = detectDirection(text);
    updateDirectionUI(direction, false);
    // Sync toggle switch state silently
    directionToggle.checked = (direction === 'preeti_to_unicode');
  }

  try {
    // Send text as a simulated .txt file upload to use the same unified API
    const file = new File([text], "conversion.txt", { type: "text/plain" });
    const formData = new FormData();
    formData.append('file', file);
    formData.append('direction', isManualOverride ? direction : 'auto');

    const response = await fetch(`${API_BASE}/api/convert`, {
      method: 'POST',
      body: formData
    });

    if (!response.ok) {
      throw new Error(`API Error: ${response.status}`);
    }

    const convertedBlob = await response.blob();
    const convertedText = await convertedBlob.text();
    resultText.value = convertedText;
  } catch (error) {
    console.error('Conversion failed:', error);
    resultText.value = 'Error converting text. Please check the backend connection.';
  }
}

// Debounce handler
sourceText.addEventListener('input', () => {
  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(convertText, 300);
});

// Toggle override handler
directionToggle.addEventListener('change', () => {
  isManualOverride = true;
  const direction = directionToggle.checked ? 'preeti_to_unicode' : 'unicode_to_preeti';
  updateDirectionUI(direction, true);
  convertText();
});

// Copy handler
copyBtn.addEventListener('click', async () => {
  if (!resultText.value) return;
  try {
    await navigator.clipboard.writeText(resultText.value);
    
    // UI feedback
    const svg = copyBtn.innerHTML;
    copyBtn.innerHTML = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>';
    copyBtn.classList.add('copied');
    
    setTimeout(() => {
      copyBtn.innerHTML = svg;
      copyBtn.classList.remove('copied');
    }, 2000);
  } catch (err) {
    console.error('Failed to copy', err);
  }
});

// --- File Upload Logic ---

// Drag & Drop
uploadZone.addEventListener('dragover', (e) => {
  e.preventDefault();
  uploadZone.classList.add('dragover');
});

uploadZone.addEventListener('dragleave', () => {
  uploadZone.classList.remove('dragover');
});

uploadZone.addEventListener('drop', (e) => {
  e.preventDefault();
  uploadZone.classList.remove('dragover');
  handleFiles(e.dataTransfer.files);
});

// File Inputs
fileInput.addEventListener('change', (e) => handleFiles(e.target.files));
folderInput.addEventListener('change', (e) => handleFiles(e.target.files));

function handleFiles(files) {
  if (!files || files.length === 0) return;
  
  const allowedExts = ['.txt', '.docx', '.pdf', '.odt'];
  
  for (const file of files) {
    const ext = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();
    if (allowedExts.includes(ext) && file.size <= 100 * 1024 * 1024) {
      const id = 'file-' + Math.random().toString(36).substr(2, 9);
      uploadQueue.push({ id, file, status: 'pending' });
      addFileToUI(id, file.name);
    }
  }
  
  updateQueueCount();
  
  if (!isUploading) {
    processQueue();
  }
}

function addFileToUI(id, filename) {
  const li = document.createElement('li');
  li.className = 'file-item';
  li.id = id;
  
  let icon = '📄';
  if (filename.endsWith('.pdf')) icon = '📕';
  else if (filename.endsWith('.docx')) icon = '📘';
  else if (filename.endsWith('.txt')) icon = '📝';

  li.innerHTML = `
    <div class="file-icon">${icon}</div>
    <div class="file-info">
      <div class="file-name" title="${filename}">${filename}</div>
      <div class="file-progress-bar">
        <div class="file-progress-fill" id="progress-${id}"></div>
      </div>
    </div>
    <div class="file-status" id="status-${id}">Pending</div>
  `;
  
  fileList.appendChild(li);
}

function updateQueueCount() {
  const pendingCount = uploadQueue.filter(f => f.status === 'pending').length;
  queueCount.textContent = `(${pendingCount} pending)`;
}

// Sequential API Upload Queue
async function processQueue() {
  if (uploadQueue.length === 0) {
    isUploading = false;
    return;
  }

  isUploading = true;
  
  // Find next pending file
  const fileObj = uploadQueue.find(f => f.status === 'pending');
  if (!fileObj) {
    isUploading = false;
    return;
  }

  fileObj.status = 'uploading';
  const statusEl = document.getElementById(`status-${fileObj.id}`);
  const progressEl = document.getElementById(`progress-${fileObj.id}`);
  
  statusEl.textContent = 'Converting...';
  progressEl.style.width = '50%';

  try {
    const formData = new FormData();
    formData.append('file', fileObj.file);
    formData.append('direction', 'auto'); // Backend will auto-detect text content where possible, though we could parse DOCX locally. For simplicity, passing auto to API. Wait, backend converter.py only auto-detects text. It doesn't auto-detect inside DOCX right now since we pass the direction directly to convert_nepali_text. If we pass 'auto', backend will try to detect the first text node it encounters.

    const response = await fetch(`${API_BASE}/api/convert`, {
      method: 'POST',
      body: formData
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    progressEl.style.width = '100%';
    statusEl.textContent = 'Done';
    statusEl.className = 'file-status status-success';
    fileObj.status = 'success';

    // Trigger Download
    const blob = await response.blob();
    const contentDisposition = response.headers.get('Content-Disposition');
    let downloadName = `converted_${fileObj.file.name}`;
    
    if (contentDisposition && contentDisposition.includes('filename=')) {
      downloadName = contentDisposition.split('filename=')[1].replace(/['"]/g, '');
    }

    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = downloadName;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    a.remove();

  } catch (error) {
    console.error('File processing error:', error);
    progressEl.style.width = '100%';
    progressEl.style.backgroundColor = 'var(--error)';
    statusEl.textContent = 'Failed';
    statusEl.className = 'file-status status-error';
    fileObj.status = 'error';
  }

  updateQueueCount();
  
  // Recursively process next
  setTimeout(processQueue, 300); // Slight delay for UX
}
