import os
import re
import json
import uuid
import shutil
from typing import List, Dict, Any, Optional
from pathlib import Path
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import pypdf
try:
    import pdfplumber
except ImportError:
    pdfplumber = None

# EMBEDDED SINGLE-PAGE APPLICATION FRONTEND (Self-contained, works everywhere)
EMBEDDED_HTML_PAGE = "<!DOCTYPE html>\n<html lang=\"en\">\n<head>\n  <meta charset=\"UTF-8\" />\n  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\" />\n  <title>PYQ Quiz Master | AI Exam & Topic Practice</title>\n  <!-- Tailwind CSS -->\n  <script src=\"https://cdn.tailwindcss.com\"></script>\n  <!-- Lucide Icons -->\n  <script src=\"https://unpkg.com/lucide@latest\"></script>\n  <!-- Canvas Confetti -->\n  <script src=\"https://cdn.jsdelivr.net/npm/canvas-confetti@1.6.0/dist/confetti.browser.min.js\"></script>\n  <script>\n    tailwind.config = {\n      darkMode: 'class',\n      theme: {\n        extend: {\n          colors: {\n            brand: {\n              50: '#eef2ff',\n              100: '#e0e7ff',\n              500: '#6366f1',\n              600: '#4f46e5',\n              700: '#4338ca',\n            }\n          }\n        }\n      }\n    }\n  </script>\n  <style>\n    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap');\n    body { font-family: 'Inter', sans-serif; }\n    .mono { font-family: 'JetBrains Mono', monospace; }\n    .glass-card {\n      background: rgba(255, 255, 255, 0.85);\n      backdrop-filter: blur(12px);\n      border: 1px solid rgba(229, 231, 235, 0.8);\n    }\n    .dark .glass-card {\n      background: rgba(30, 41, 59, 0.85);\n      border: 1px solid rgba(51, 65, 85, 0.8);\n    }\n  </style>\n</head>\n<body class=\"bg-slate-50 text-slate-900 dark:bg-slate-950 dark:text-slate-100 min-h-screen transition-colors duration-200\">\n\n  <!-- ================= NAVBAR ================= -->\n  <nav class=\"sticky top-0 z-50 glass-card border-b border-slate-200 dark:border-slate-800 px-6 py-4 flex items-center justify-between shadow-sm\">\n    <div class=\"flex items-center gap-3 cursor-pointer\" onclick=\"switchView('view-upload')\">\n      <div class=\"w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 to-violet-500 flex items-center justify-center text-white shadow-md shadow-indigo-500/20\">\n        <i data-lucide=\"sparkles\" class=\"w-6 h-6\"></i>\n      </div>\n      <div>\n        <h1 class=\"text-xl font-extrabold tracking-tight bg-gradient-to-r from-indigo-600 to-violet-600 bg-clip-text text-transparent dark:from-indigo-400 dark:to-violet-400\">\n          PYQ Quiz Master\n        </h1>\n        <p class=\"text-xs text-slate-500 dark:text-slate-400 font-medium\">Auto-Extract PYQ Papers & Topics</p>\n      </div>\n    </div>\n\n    <div class=\"flex items-center gap-3\">\n      <button onclick=\"loadPreviousQuizzes()\" class=\"px-3.5 py-2 text-xs font-semibold text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg flex items-center gap-2 border border-slate-200 dark:border-slate-700 transition\">\n        <i data-lucide=\"history\" class=\"w-4 h-4\"></i>\n        <span>My Papers</span>\n      </button>\n      <button id=\"theme-toggle\" onclick=\"toggleTheme()\" class=\"p-2 rounded-lg text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800 border border-slate-200 dark:border-slate-700\">\n        <i data-lucide=\"moon\" class=\"w-4 h-4 dark:hidden\"></i>\n        <i data-lucide=\"sun\" class=\"w-4 h-4 hidden dark:block\"></i>\n      </button>\n    </div>\n  </nav>\n\n  <!-- ================= MAIN CONTAINER ================= -->\n  <main class=\"max-w-6xl mx-auto px-4 py-8\">\n\n    <!-- ================= VIEW 1: UPLOAD & TOPICS ================= -->\n    <section id=\"view-upload\" class=\"space-y-8 block\">\n      <!-- Hero Banner -->\n      <div class=\"text-center max-w-2xl mx-auto pt-4 pb-2\">\n        <span class=\"px-3 py-1 text-xs font-semibold uppercase tracking-wider bg-indigo-100 text-indigo-700 dark:bg-indigo-950/60 dark:text-indigo-400 rounded-full\">\n          100% From Your PDF Only\n        </span>\n        <h2 class=\"mt-4 text-3xl sm:text-4xl font-extrabold text-slate-900 dark:text-white tracking-tight\">\n          Upload Any Exam PYQ PDF.<br/><span class=\"text-indigo-600 dark:text-indigo-400\">Auto-Detect Topics & Start Testing.</span>\n        </h2>\n        <p class=\"mt-3 text-sm text-slate-600 dark:text-slate-400\">\n          Drop your Previous Year Question paper (JEE, NEET, UPSC, SSC, College, Gate, Board exams). The engine automatically extracts all MCQs, separates topics, and builds an instant quiz simulator.\n        </p>\n      </div>\n\n      <!-- Upload Box -->\n      <div class=\"max-w-2xl mx-auto\">\n        <div id=\"drop-zone\" class=\"border-2 border-dashed border-indigo-300 dark:border-indigo-800/70 hover:border-indigo-500 dark:hover:border-indigo-400 rounded-2xl p-8 text-center bg-white dark:bg-slate-900/60 shadow-lg shadow-indigo-500/5 transition cursor-pointer group\">\n          <input type=\"file\" id=\"pdf-input\" accept=\"application/pdf\" class=\"hidden\" onchange=\"handleFileSelect(event)\" />\n          \n          <div class=\"w-16 h-16 mx-auto rounded-2xl bg-indigo-50 dark:bg-indigo-950/80 flex items-center justify-center text-indigo-600 dark:text-indigo-400 group-hover:scale-110 transition duration-200\">\n            <i data-lucide=\"file-up\" class=\"w-8 h-8\"></i>\n          </div>\n          \n          <h3 class=\"mt-4 text-base font-bold text-slate-800 dark:text-slate-200\">\n            Click to upload or drag & drop your PYQ PDF\n          </h3>\n          <p class=\"text-xs text-slate-500 dark:text-slate-400 mt-1\">\n            Supports Question Papers, Mock Tests, and Answer Keys (up to 50MB)\n          </p>\n\n          <div id=\"upload-status\" class=\"mt-4 hidden\">\n            <div class=\"flex items-center justify-center gap-3 text-indigo-600 dark:text-indigo-400 font-semibold text-sm\">\n              <i data-lucide=\"loader-2\" class=\"w-5 h-5 animate-spin\"></i>\n              <span id=\"upload-status-text\">Parsing PDF & Detecting Topics...</span>\n            </div>\n          </div>\n        </div>\n      </div>\n\n      <!-- Loaded Quiz & Detected Topics Section -->\n      <div id=\"topics-section\" class=\"hidden max-w-4xl mx-auto space-y-6\">\n        <div class=\"flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm\">\n          <div>\n            <div class=\"flex items-center gap-2\">\n              <span class=\"w-2.5 h-2.5 rounded-full bg-emerald-500\"></span>\n              <h3 id=\"quiz-title\" class=\"text-lg font-bold text-slate-900 dark:text-white\">Exam Paper</h3>\n            </div>\n            <p id=\"quiz-stats\" class=\"text-xs text-slate-500 dark:text-slate-400 mt-1\">45 Questions Detected across 4 Topics</p>\n          </div>\n          \n          <button onclick=\"startQuiz('all')\" class=\"w-full sm:w-auto px-6 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold rounded-xl text-sm shadow-md shadow-indigo-600/30 flex items-center justify-center gap-2 transition transform active:scale-95\">\n            <i data-lucide=\"play\" class=\"w-4 h-4 fill-current\"></i>\n            <span>Start Full Exam (All Topics)</span>\n          </button>\n        </div>\n\n        <div>\n          <h4 class=\"text-sm font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-3\">\n            Auto-Detected Topics / Sections\n          </h4>\n          <div id=\"topics-grid\" class=\"grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4\">\n            <!-- Topic cards will be dynamically injected here -->\n          </div>\n        </div>\n      </div>\n\n      <!-- Previous Papers Modal / Drawer -->\n      <div id=\"previous-papers-modal\" class=\"hidden fixed inset-0 z-50 bg-slate-950/60 backdrop-blur-sm flex items-center justify-center p-4\">\n        <div class=\"bg-white dark:bg-slate-900 max-w-xl w-full rounded-2xl p-6 border border-slate-200 dark:border-slate-800 shadow-2xl space-y-4\">\n          <div class=\"flex items-center justify-between\">\n            <h3 class=\"text-base font-bold\">Uploaded Papers History</h3>\n            <button onclick=\"closePreviousQuizzes()\" class=\"text-slate-400 hover:text-slate-600 dark:hover:text-slate-200\">\n              <i data-lucide=\"x\" class=\"w-5 h-5\"></i>\n            </button>\n          </div>\n          <div id=\"previous-papers-list\" class=\"space-y-2 max-h-80 overflow-y-auto pr-1\">\n            <!-- List injected here -->\n          </div>\n        </div>\n      </div>\n    </section>\n\n    <!-- ================= VIEW 2: QUIZ ROOM / EXAM ARENA ================= -->\n    <section id=\"view-quiz\" class=\"hidden space-y-6\">\n      \n      <!-- Quiz Header bar -->\n      <div class=\"glass-card rounded-2xl p-4 flex flex-wrap items-center justify-between gap-4\">\n        <div>\n          <span id=\"active-quiz-topic\" class=\"px-2.5 py-0.5 text-xs font-semibold rounded-full bg-indigo-100 text-indigo-700 dark:bg-indigo-950 dark:text-indigo-300\">\n            Topic: Physics\n          </span>\n          <h2 id=\"active-quiz-name\" class=\"text-base font-bold text-slate-900 dark:text-white mt-1 truncate max-w-xs sm:max-w-md\">\n            Exam Quiz\n          </h2>\n        </div>\n\n        <div class=\"flex items-center gap-4\">\n          <!-- Timer -->\n          <div class=\"flex items-center gap-2 bg-slate-100 dark:bg-slate-800/80 px-3.5 py-1.5 rounded-xl border border-slate-200 dark:border-slate-700\">\n            <i data-lucide=\"clock\" class=\"w-4 h-4 text-indigo-600 dark:text-indigo-400\"></i>\n            <span id=\"quiz-timer\" class=\"font-mono text-sm font-bold\">00:00</span>\n          </div>\n\n          <!-- Submit Button -->\n          <button onclick=\"confirmSubmitQuiz()\" class=\"px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold rounded-xl shadow-md shadow-emerald-600/20 flex items-center gap-1.5 transition\">\n            <i data-lucide=\"check-circle\" class=\"w-4 h-4\"></i>\n            <span>Submit Quiz</span>\n          </button>\n        </div>\n      </div>\n\n      <!-- Main Quiz Area: Left Question Body, Right Palette -->\n      <div class=\"grid grid-cols-1 lg:grid-cols-12 gap-6\">\n        \n        <!-- Left: Question Card (8 cols) -->\n        <div class=\"lg:col-span-8 space-y-4\">\n          <div class=\"glass-card rounded-2xl p-6 sm:p-8 space-y-6 min-h-[420px] flex flex-col justify-between shadow-sm\">\n            \n            <div class=\"space-y-4\">\n              <div class=\"flex items-center justify-between border-b border-slate-200 dark:border-slate-800 pb-3\">\n                <span id=\"current-q-index\" class=\"text-xs font-bold uppercase tracking-wider text-indigo-600 dark:text-indigo-400\">\n                  Question 1 of 30\n                </span>\n                <button onclick=\"toggleMarkForReview()\" id=\"btn-review\" class=\"text-xs font-medium text-amber-600 dark:text-amber-400 hover:underline flex items-center gap-1\">\n                  <i data-lucide=\"bookmark\" class=\"w-3.5 h-3.5\"></i>\n                  <span id=\"review-text\">Mark for Review</span>\n                </button>\n              </div>\n\n              <!-- Question Text -->\n              <div id=\"q-text\" class=\"text-base sm:text-lg font-semibold text-slate-900 dark:text-slate-100 leading-relaxed\">\n                Loading Question...\n              </div>\n\n              <!-- Options Container -->\n              <div id=\"q-options\" class=\"space-y-3 pt-2\">\n                <!-- Injected options -->\n              </div>\n            </div>\n\n            <!-- Bottom Navigation buttons -->\n            <div class=\"flex items-center justify-between pt-6 border-t border-slate-200 dark:border-slate-800\">\n              <button onclick=\"prevQuestion()\" id=\"btn-prev\" class=\"px-4 py-2 text-xs font-bold text-slate-700 dark:text-slate-300 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 rounded-xl flex items-center gap-1 transition\">\n                <i data-lucide=\"chevron-left\" class=\"w-4 h-4\"></i>\n                <span>Previous</span>\n              </button>\n\n              <button onclick=\"clearOptionSelection()\" class=\"text-xs text-slate-500 hover:text-slate-800 dark:hover:text-slate-200\">\n                Clear Choice\n              </button>\n\n              <button onclick=\"nextQuestion()\" id=\"btn-next\" class=\"px-5 py-2 text-xs font-bold text-white bg-indigo-600 hover:bg-indigo-700 rounded-xl flex items-center gap-1 shadow-md shadow-indigo-600/20 transition\">\n                <span>Next</span>\n                <i data-lucide=\"chevron-right\" class=\"w-4 h-4\"></i>\n              </button>\n            </div>\n\n          </div>\n        </div>\n\n        <!-- Right: Question Palette / Navigator (4 cols) -->\n        <div class=\"lg:col-span-4 space-y-4\">\n          <div class=\"glass-card rounded-2xl p-5 space-y-4\">\n            <h3 class=\"text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400\">\n              Question Navigator\n            </h3>\n\n            <!-- Question Numbers Grid -->\n            <div id=\"palette-grid\" class=\"grid grid-cols-5 sm:grid-cols-6 gap-2 max-h-72 overflow-y-auto p-1\">\n              <!-- Number buttons injected here -->\n            </div>\n\n            <!-- Legend -->\n            <div class=\"pt-3 border-t border-slate-200 dark:border-slate-800 grid grid-cols-2 gap-2 text-[11px] font-medium text-slate-600 dark:text-slate-400\">\n              <div class=\"flex items-center gap-2\">\n                <span class=\"w-3 h-3 rounded bg-emerald-500\"></span>\n                <span>Answered</span>\n              </div>\n              <div class=\"flex items-center gap-2\">\n                <span class=\"w-3 h-3 rounded bg-amber-500\"></span>\n                <span>Marked</span>\n              </div>\n              <div class=\"flex items-center gap-2\">\n                <span class=\"w-3 h-3 rounded bg-slate-200 dark:bg-slate-700\"></span>\n                <span>Unattempted</span>\n              </div>\n              <div class=\"flex items-center gap-2\">\n                <span class=\"w-3 h-3 rounded border-2 border-indigo-600\"></span>\n                <span>Current</span>\n              </div>\n            </div>\n\n          </div>\n        </div>\n\n      </div>\n\n    </section>\n\n    <!-- ================= VIEW 3: SCORECARD & DETAILED REVIEW ================= -->\n    <section id=\"view-results\" class=\"hidden space-y-8\">\n      \n      <!-- Score Overview Card -->\n      <div class=\"glass-card rounded-3xl p-8 text-center relative overflow-hidden shadow-lg\">\n        <div class=\"max-w-md mx-auto space-y-4\">\n          <span class=\"px-3.5 py-1 text-xs font-bold uppercase tracking-wider rounded-full bg-indigo-100 text-indigo-700 dark:bg-indigo-950 dark:text-indigo-400\">\n            Quiz Completed!\n          </span>\n          <h2 id=\"result-quiz-title\" class=\"text-2xl font-black text-slate-900 dark:text-white\">Exam Results</h2>\n\n          <div class=\"py-4\">\n            <div class=\"inline-flex flex-col items-center justify-center w-36 h-36 rounded-full border-4 border-indigo-600 dark:border-indigo-400 bg-indigo-50/50 dark:bg-indigo-950/30\">\n              <span id=\"score-percentage\" class=\"text-3xl font-black text-indigo-600 dark:text-indigo-400\">85%</span>\n              <span class=\"text-xs font-bold text-slate-500 uppercase\">Accuracy</span>\n            </div>\n          </div>\n\n          <!-- Quick Stats Grid -->\n          <div class=\"grid grid-cols-3 gap-3\">\n            <div class=\"p-3 rounded-2xl bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800/40\">\n              <div id=\"stat-correct\" class=\"text-xl font-black text-emerald-600 dark:text-emerald-400\">18</div>\n              <div class=\"text-[11px] font-semibold text-emerald-700 dark:text-emerald-300\">Correct</div>\n            </div>\n            <div class=\"p-3 rounded-2xl bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-800/40\">\n              <div id=\"stat-wrong\" class=\"text-xl font-black text-rose-600 dark:text-rose-400\">4</div>\n              <div class=\"text-[11px] font-semibold text-rose-700 dark:text-rose-300\">Incorrect</div>\n            </div>\n            <div class=\"p-3 rounded-2xl bg-slate-100 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700\">\n              <div id=\"stat-unattempted\" class=\"text-xl font-black text-slate-600 dark:text-slate-300\">3</div>\n              <div class=\"text-[11px] font-semibold text-slate-500\">Skipped</div>\n            </div>\n          </div>\n\n          <!-- Actions -->\n          <div class=\"flex items-center justify-center gap-3 pt-2\">\n            <button onclick=\"retakeActiveQuiz()\" class=\"px-5 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold rounded-xl shadow-md flex items-center gap-2 transition\">\n              <i data-lucide=\"rotate-ccw\" class=\"w-4 h-4\"></i>\n              <span>Retake Quiz</span>\n            </button>\n            <button onclick=\"switchView('view-upload')\" class=\"px-5 py-2.5 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-xs font-bold rounded-xl transition\">\n              <span>Upload New PDF</span>\n            </button>\n          </div>\n\n        </div>\n      </div>\n\n      <!-- Topic Performance Breakdown -->\n      <div id=\"topic-breakdown-card\" class=\"glass-card rounded-2xl p-6 space-y-4\">\n        <h3 class=\"text-sm font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400\">\n          Topic-Wise Performance\n        </h3>\n        <div id=\"topic-performance-list\" class=\"space-y-3\">\n          <!-- Injected bars -->\n        </div>\n      </div>\n\n      <!-- Detailed Review & Explanation Section -->\n      <div class=\"space-y-4\">\n        <div class=\"flex flex-col sm:flex-row sm:items-center justify-between gap-3\">\n          <h3 class=\"text-lg font-extrabold text-slate-900 dark:text-white\">\n            Detailed Question Review & Verified PDF Answers\n          </h3>\n          <!-- Filter buttons -->\n          <div class=\"flex items-center gap-2 text-xs\">\n            <button onclick=\"filterReview('all')\" class=\"rev-filter-btn active px-3 py-1.5 rounded-lg font-bold bg-indigo-600 text-white\">All</button>\n            <button onclick=\"filterReview('wrong')\" class=\"rev-filter-btn px-3 py-1.5 rounded-lg font-bold bg-slate-200 dark:bg-slate-800 text-slate-700 dark:text-slate-300\">Wrong Only</button>\n            <button onclick=\"filterReview('correct')\" class=\"rev-filter-btn px-3 py-1.5 rounded-lg font-bold bg-slate-200 dark:bg-slate-800 text-slate-700 dark:text-slate-300\">Correct Only</button>\n          </div>\n        </div>\n\n        <div id=\"review-list\" class=\"space-y-4\">\n          <!-- Injected detailed questions with answers & explanations -->\n        </div>\n      </div>\n\n    </section>\n\n  </main>\n\n  <!-- ================= JAVASCRIPT LOGIC ================= -->\n  <script>\n    // State management\n    let currentQuizId = null;\n    let currentQuizData = null;\n    let questions = [];\n    let currentQIndex = 0;\n    let userAnswers = {}; // { q_1: 'A', ... }\n    let markedForReview = new Set();\n    let timerInterval = null;\n    let secondsElapsed = 0;\n    let reviewData = null;\n\n    // Initialize Lucide Icons\n    function updateIcons() {\n      if (window.lucide) {\n        lucide.createIcons();\n      }\n    }\n    document.addEventListener(\"DOMContentLoaded\", () => {\n      updateIcons();\n      setupDragAndDrop();\n    });\n\n    // Theme toggle\n    function toggleTheme() {\n      document.documentElement.classList.toggle('dark');\n      updateIcons();\n    }\n\n    // View switcher\n    function switchView(viewId) {\n      ['view-upload', 'view-quiz', 'view-results'].forEach(id => {\n        const el = document.getElementById(id);\n        if (el) el.classList.toggle('hidden', id !== viewId);\n      });\n      window.scrollTo({ top: 0, behavior: 'smooth' });\n      updateIcons();\n    }\n\n    // Drag and drop setup\n    function setupDragAndDrop() {\n      const dropZone = document.getElementById('drop-zone');\n      const fileInput = document.getElementById('pdf-input');\n\n      dropZone.addEventListener('click', () => fileInput.click());\n\n      ['dragenter', 'dragover'].forEach(eventName => {\n        dropZone.addEventListener(eventName, (e) => {\n          e.preventDefault();\n          dropZone.classList.add('border-indigo-600', 'bg-indigo-50/50', 'dark:bg-indigo-950/20');\n        });\n      });\n\n      ['dragleave', 'drop'].forEach(eventName => {\n        dropZone.addEventListener(eventName, (e) => {\n          e.preventDefault();\n          dropZone.classList.remove('border-indigo-600', 'bg-indigo-50/50', 'dark:bg-indigo-950/20');\n        });\n      });\n\n      dropZone.addEventListener('drop', (e) => {\n        if (e.dataTransfer.files.length > 0) {\n          uploadFile(e.dataTransfer.files[0]);\n        }\n      });\n    }\n\n    function handleFileSelect(e) {\n      if (e.target.files.length > 0) {\n        uploadFile(e.target.files[0]);\n      }\n    }\n\n    async function uploadFile(file) {\n      if (!file.name.toLowerCase().endsWith('.pdf')) {\n        alert('Please select a valid PDF file.');\n        return;\n      }\n\n      const statusEl = document.getElementById('upload-status');\n      const statusText = document.getElementById('upload-status-text');\n      statusEl.classList.remove('hidden');\n      statusText.innerText = `Uploading and parsing \"${file.name}\"...`;\n      updateIcons();\n\n      const formData = new FormData();\n      formData.append('file', file);\n\n      try {\n        const res = await fetch('/api/upload', {\n          method: 'POST',\n          body: formData\n        });\n\n        const data = await res.json();\n        statusEl.classList.add('hidden');\n\n        if (!res.ok) {\n          alert(`Error: ${data.detail || 'Could not parse PDF'}`);\n          return;\n        }\n\n        currentQuizId = data.quiz_id;\n        displayTopicBreakdown(data);\n      } catch (err) {\n        statusEl.classList.add('hidden');\n        alert(`Upload error: ${err.message}`);\n      }\n    }\n\n    function displayTopicBreakdown(data) {\n      document.getElementById('topics-section').classList.remove('hidden');\n      document.getElementById('quiz-title').innerText = data.title;\n      document.getElementById('quiz-stats').innerText = `${data.total_questions} Questions Extracted across ${data.topics.length} Detected Topics`;\n\n      const grid = document.getElementById('topics-grid');\n      grid.innerHTML = '';\n\n      data.topics.forEach((t) => {\n        const card = document.createElement('div');\n        card.className = 'glass-card p-5 rounded-2xl flex flex-col justify-between hover:shadow-md transition space-y-4';\n        card.innerHTML = `\n          <div>\n            <div class=\"flex items-center justify-between\">\n              <span class=\"px-2.5 py-0.5 rounded-full text-xs font-bold bg-indigo-100 text-indigo-700 dark:bg-indigo-950 dark:text-indigo-300\">\n                ${t.count} Questions\n              </span>\n              <i data-lucide=\"layers\" class=\"w-4 h-4 text-slate-400\"></i>\n            </div>\n            <h4 class=\"mt-2 text-base font-bold text-slate-900 dark:text-white line-clamp-1\">${t.name}</h4>\n          </div>\n          <button onclick=\"startQuiz('${t.name}')\" class=\"w-full py-2 bg-slate-100 hover:bg-indigo-600 dark:bg-slate-800 dark:hover:bg-indigo-600 hover:text-white text-slate-700 dark:text-slate-200 text-xs font-bold rounded-xl transition flex items-center justify-center gap-1.5\">\n            <i data-lucide=\"play\" class=\"w-3.5 h-3.5\"></i>\n            <span>Practice Topic</span>\n          </button>\n        `;\n        grid.appendChild(card);\n      });\n\n      updateIcons();\n      document.getElementById('topics-section').scrollIntoView({ behavior: 'smooth' });\n    }\n\n    // Load Quiz for Topic or All\n    async function startQuiz(topic) {\n      if (!currentQuizId) return;\n\n      try {\n        const url = topic === 'all' \n          ? `/api/quiz/${currentQuizId}`\n          : `/api/quiz/${currentQuizId}?topic=${encodeURIComponent(topic)}`;\n\n        const res = await fetch(url);\n        const data = await res.json();\n        if (!res.ok) {\n          alert('Failed to load quiz');\n          return;\n        }\n\n        currentQuizData = data;\n        questions = data.questions;\n        currentQIndex = 0;\n        userAnswers = {};\n        markedForReview.clear();\n        secondsElapsed = 0;\n\n        document.getElementById('active-quiz-name').innerText = data.title;\n        document.getElementById('active-quiz-topic').innerText = `Topic: ${data.selected_topic}`;\n\n        startTimer();\n        renderPalette();\n        renderCurrentQuestion();\n        switchView('view-quiz');\n      } catch (err) {\n        alert(`Error starting quiz: ${err.message}`);\n      }\n    }\n\n    function startTimer() {\n      clearInterval(timerInterval);\n      const timerEl = document.getElementById('quiz-timer');\n      timerInterval = setInterval(() => {\n        secondsElapsed++;\n        const mins = String(Math.floor(secondsElapsed / 60)).padStart(2, '0');\n        const secs = String(secondsElapsed % 60).padStart(2, '0');\n        timerEl.innerText = `${mins}:${secs}`;\n      }, 1000);\n    }\n\n    function renderCurrentQuestion() {\n      if (!questions || questions.length === 0) return;\n      const q = questions[currentQIndex];\n\n      document.getElementById('current-q-index').innerText = `Question ${currentQIndex + 1} of ${questions.length} (Topic: ${q.topic})`;\n      document.getElementById('q-text').innerText = `${q.original_num ? q.original_num + '.' : ''} ${q.question}`;\n\n      // Update Mark for review state\n      const isMarked = markedForReview.has(q.id);\n      document.getElementById('review-text').innerText = isMarked ? 'Unmark Review' : 'Mark for Review';\n\n      // Render Options\n      const optionsContainer = document.getElementById('q-options');\n      optionsContainer.innerHTML = '';\n\n      q.options.forEach((opt) => {\n        const isSelected = userAnswers[q.id] === opt.key;\n        const optBtn = document.createElement('button');\n        optBtn.className = `w-full text-left p-4 rounded-xl border-2 font-medium text-sm flex items-start gap-3 transition ${\n          isSelected \n            ? 'border-indigo-600 bg-indigo-50/80 dark:bg-indigo-950/50 text-indigo-900 dark:text-indigo-200 shadow-sm' \n            : 'border-slate-200 dark:border-slate-800 hover:border-slate-300 dark:hover:border-slate-700 bg-white dark:bg-slate-900 text-slate-800 dark:text-slate-200'\n        }`;\n\n        optBtn.innerHTML = `\n          <span class=\"w-6 h-6 rounded-lg flex items-center justify-center font-bold text-xs shrink-0 ${\n            isSelected \n              ? 'bg-indigo-600 text-white' \n              : 'bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300'\n          }\">${opt.key}</span>\n          <span class=\"pt-0.5\">${opt.text}</span>\n        `;\n\n        optBtn.onclick = () => selectOption(q.id, opt.key);\n        optionsContainer.appendChild(optBtn);\n      });\n\n      // Update Prev / Next button states\n      document.getElementById('btn-prev').disabled = (currentQIndex === 0);\n      document.getElementById('btn-prev').classList.toggle('opacity-50', currentQIndex === 0);\n\n      const isLast = currentQIndex === questions.length - 1;\n      document.getElementById('btn-next').innerHTML = isLast \n        ? `<span>Finish</span><i data-lucide=\"check\" class=\"w-4 h-4\"></i>` \n        : `<span>Next</span><i data-lucide=\"chevron-right\" class=\"w-4 h-4\"></i>`;\n\n      renderPalette();\n      updateIcons();\n    }\n\n    function selectOption(qId, optionKey) {\n      userAnswers[qId] = optionKey;\n      renderCurrentQuestion();\n    }\n\n    function clearOptionSelection() {\n      const q = questions[currentQIndex];\n      delete userAnswers[q.id];\n      renderCurrentQuestion();\n    }\n\n    function toggleMarkForReview() {\n      const q = questions[currentQIndex];\n      if (markedForReview.has(q.id)) {\n        markedForReview.delete(q.id);\n      } else {\n        markedForReview.add(q.id);\n      }\n      renderCurrentQuestion();\n    }\n\n    function nextQuestion() {\n      if (currentQIndex < questions.length - 1) {\n        currentQIndex++;\n        renderCurrentQuestion();\n      } else {\n        confirmSubmitQuiz();\n      }\n    }\n\n    function prevQuestion() {\n      if (currentQIndex > 0) {\n        currentQIndex--;\n        renderCurrentQuestion();\n      }\n    }\n\n    function jumpToQuestion(idx) {\n      currentQIndex = idx;\n      renderCurrentQuestion();\n    }\n\n    function renderPalette() {\n      const palette = document.getElementById('palette-grid');\n      palette.innerHTML = '';\n\n      questions.forEach((q, idx) => {\n        const isAnswered = !!userAnswers[q.id];\n        const isMarked = markedForReview.has(q.id);\n        const isCurrent = (idx === currentQIndex);\n\n        let bgClass = 'bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300';\n        if (isAnswered) bgClass = 'bg-emerald-500 text-white font-bold';\n        if (isMarked) bgClass = 'bg-amber-500 text-white font-bold';\n\n        const btn = document.createElement('button');\n        btn.className = `w-9 h-9 rounded-xl text-xs font-semibold flex items-center justify-center transition ${bgClass} ${\n          isCurrent ? 'ring-2 ring-indigo-600 ring-offset-2 dark:ring-offset-slate-900 scale-105' : ''\n        }`;\n        btn.innerText = idx + 1;\n        btn.onclick = () => jumpToQuestion(idx);\n        palette.appendChild(btn);\n      });\n    }\n\n    // Submit Quiz\n    async function confirmSubmitQuiz() {\n      const answeredCount = Object.keys(userAnswers).length;\n      const total = questions.length;\n      const unanswered = total - answeredCount;\n\n      const confirmed = confirm(\n        `Submit your Exam Quiz?\\n\\nAttempted: ${answeredCount}/${total}\\nUnanswered: ${unanswered}\\nTime: ${document.getElementById('quiz-timer').innerText}`\n      );\n\n      if (!confirmed) return;\n\n      clearInterval(timerInterval);\n\n      try {\n        const res = await fetch(`/api/quiz/${currentQuizId}/submit`, {\n          method: 'POST',\n          headers: { 'Content-Type': 'application/json' },\n          body: JSON.stringify({\n            answers: userAnswers,\n            time_taken_seconds: secondsElapsed\n          })\n        });\n\n        const results = await res.json();\n        if (!res.ok) {\n          alert('Submission error');\n          return;\n        }\n\n        reviewData = results;\n        displayResults(results);\n      } catch (err) {\n        alert(`Error submitting answers: ${err.message}`);\n      }\n    }\n\n    function displayResults(data) {\n      switchView('view-results');\n\n      // Trigger Confetti if score > 50%\n      if (data.percentage >= 50 && window.confetti) {\n        confetti({\n          particleCount: 100,\n          spread: 70,\n          origin: { y: 0.6 }\n        });\n      }\n\n      document.getElementById('result-quiz-title').innerText = data.title;\n      document.getElementById('score-percentage').innerText = `${data.percentage}%`;\n      document.getElementById('stat-correct').innerText = data.score;\n      document.getElementById('stat-wrong').innerText = data.wrong;\n      document.getElementById('stat-unattempted').innerText = data.unattempted;\n\n      // Topic-wise progress\n      const tpContainer = document.getElementById('topic-performance-list');\n      tpContainer.innerHTML = '';\n      for (const [topic, stat] of Object.entries(data.topic_performance)) {\n        const pct = Math.round((stat.correct / stat.total) * 100);\n        const row = document.createElement('div');\n        row.className = 'space-y-1';\n        row.innerHTML = `\n          <div class=\"flex justify-between text-xs font-semibold\">\n            <span>${topic} (${stat.correct}/${stat.total})</span>\n            <span>${pct}%</span>\n          </div>\n          <div class=\"w-full h-2 bg-slate-200 dark:bg-slate-800 rounded-full overflow-hidden\">\n            <div class=\"h-full bg-indigo-600 rounded-full\" style=\"width: ${pct}%\"></div>\n          </div>\n        `;\n        tpContainer.appendChild(row);\n      }\n\n      renderReviewList('all');\n    }\n\n    function filterReview(type) {\n      document.querySelectorAll('.rev-filter-btn').forEach(b => {\n        b.classList.remove('bg-indigo-600', 'text-white');\n        b.classList.add('bg-slate-200', 'dark:bg-slate-800', 'text-slate-700', 'dark:text-slate-300');\n      });\n      event.target.classList.remove('bg-slate-200', 'dark:bg-slate-800', 'text-slate-700', 'dark:text-slate-300');\n      event.target.classList.add('bg-indigo-600', 'text-white');\n\n      renderReviewList(type);\n    }\n\n    function renderReviewList(filter) {\n      if (!reviewData) return;\n      const container = document.getElementById('review-list');\n      container.innerHTML = '';\n\n      let items = reviewData.review;\n      if (filter === 'wrong') items = items.filter(i => i.status === 'wrong');\n      if (filter === 'correct') items = items.filter(i => i.status === 'correct');\n\n      if (items.length === 0) {\n        container.innerHTML = '<div class=\"p-8 text-center text-sm text-slate-500\">No questions in this filter.</div>';\n        return;\n      }\n\n      items.forEach((item, index) => {\n        const card = document.createElement('div');\n        let borderClass = 'border-slate-200 dark:border-slate-800';\n        let badgeColor = 'bg-slate-100 text-slate-700';\n\n        if (item.status === 'correct') {\n          borderClass = 'border-emerald-300 dark:border-emerald-800';\n          badgeColor = 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300';\n        } else if (item.status === 'wrong') {\n          borderClass = 'border-rose-300 dark:border-rose-800';\n          badgeColor = 'bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-300';\n        }\n\n        card.className = `glass-card p-6 rounded-2xl border-2 ${borderClass} space-y-4`;\n\n        let optionsHtml = item.options.map(opt => {\n          let optStyle = 'border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900';\n          let labelBadge = '';\n\n          if (opt.key === item.correct_answer) {\n            optStyle = 'border-emerald-500 bg-emerald-50/70 dark:bg-emerald-950/40 text-emerald-900 dark:text-emerald-200 font-bold';\n            labelBadge = '<span class=\"text-[10px] font-bold uppercase text-emerald-600 dark:text-emerald-400 ml-auto\">Correct Answer</span>';\n          }\n          if (opt.key === item.user_choice && opt.key !== item.correct_answer) {\n            optStyle = 'border-rose-500 bg-rose-50/70 dark:bg-rose-950/40 text-rose-900 dark:text-rose-200 font-bold';\n            labelBadge = '<span class=\"text-[10px] font-bold uppercase text-rose-600 dark:text-rose-400 ml-auto\">Your Choice</span>';\n          }\n\n          return `\n            <div class=\"p-3 rounded-xl border text-xs flex items-center gap-2 ${optStyle}\">\n              <span class=\"w-5 h-5 rounded flex items-center justify-center font-bold\">${opt.key}</span>\n              <span>${opt.text}</span>\n              ${labelBadge}\n            </div>\n          `;\n        }).join('');\n\n        card.innerHTML = `\n          <div class=\"flex items-center justify-between\">\n            <span class=\"text-xs font-bold text-slate-500\">Question ${item.original_num || index + 1} (${item.topic})</span>\n            <span class=\"px-2.5 py-0.5 rounded-full text-xs font-bold uppercase ${badgeColor}\">\n              ${item.status}\n            </span>\n          </div>\n          <div class=\"text-sm font-semibold text-slate-900 dark:text-slate-100\">\n            ${item.question}\n          </div>\n          <div class=\"space-y-2 pt-1\">\n            ${optionsHtml}\n          </div>\n          ${item.explanation ? `\n            <div class=\"p-3 rounded-xl bg-slate-100 dark:bg-slate-800/80 text-xs text-slate-700 dark:text-slate-300\">\n              <strong class=\"text-indigo-600 dark:text-indigo-400 font-bold\">Solution Note / Source:</strong> ${item.explanation}\n            </div>\n          ` : ''}\n        `;\n\n        container.appendChild(card);\n      });\n\n      updateIcons();\n    }\n\n    function retakeActiveQuiz() {\n      if (currentQuizData) {\n        startQuiz(currentQuizData.selected_topic === 'All Topics' ? 'all' : currentQuizData.selected_topic);\n      }\n    }\n\n    async function loadPreviousQuizzes() {\n      try {\n        const res = await fetch('/api/quizzes');\n        const data = await res.json();\n        const list = document.getElementById('previous-papers-list');\n        list.innerHTML = '';\n\n        if (!data || data.length === 0) {\n          list.innerHTML = '<p class=\"text-xs text-slate-500 py-4 text-center\">No previous papers uploaded yet.</p>';\n        } else {\n          data.forEach(q => {\n            const item = document.createElement('div');\n            item.className = 'p-3 rounded-xl border border-slate-200 dark:border-slate-800 hover:border-indigo-500 cursor-pointer flex items-center justify-between transition';\n            item.innerHTML = `\n              <div>\n                <h4 class=\"text-xs font-bold text-slate-900 dark:text-white\">${q.title}</h4>\n                <p class=\"text-[11px] text-slate-500\">${q.total_questions} Questions \u2022 ${q.topics.length} Topics</p>\n              </div>\n              <button class=\"text-xs px-2.5 py-1 rounded bg-indigo-600 text-white font-semibold\">Open</button>\n            `;\n            item.onclick = () => {\n              currentQuizId = q.id;\n              displayTopicBreakdown(q);\n              closePreviousQuizzes();\n            };\n            list.appendChild(item);\n          });\n        }\n\n        document.getElementById('previous-papers-modal').classList.remove('hidden');\n      } catch (err) {\n        alert('Could not fetch quiz history');\n      }\n    }\n\n    function closePreviousQuizzes() {\n      document.getElementById('previous-papers-modal').classList.add('hidden');\n    }\n\n    // Keyboard Shortcuts (1,2,3,4 or A,B,C,D)\n    window.addEventListener('keydown', (e) => {\n      if (document.getElementById('view-quiz').classList.contains('hidden')) return;\n      const keyMap = { '1': 'A', '2': 'B', '3': 'C', '4': 'D', 'a': 'A', 'b': 'B', 'c': 'C', 'd': 'D' };\n      const selected = keyMap[e.key.toLowerCase()];\n      if (selected && questions[currentQIndex]) {\n        selectOption(questions[currentQIndex].id, selected);\n      }\n      if (e.key === 'ArrowRight') nextQuestion();\n      if (e.key === 'ArrowLeft') prevQuestion();\n    });\n  </script>\n</body>\n</html>\n"

app = FastAPI(title="PYQ Quiz Master", description="Instant Quiz Platform from PYQ PDFs with Topic Detection")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
DATA_DIR = BASE_DIR / "data"
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"

for directory in [UPLOAD_DIR, DATA_DIR, STATIC_DIR, TEMPLATES_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

DB_FILE = DATA_DIR / "quizzes.json"

def load_db() -> Dict[str, Any]:
    if DB_FILE.exists():
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_db(data: Dict[str, Any]):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def extract_text_from_pdf(pdf_path: Path) -> str:
    full_text = []
    if pdfplumber:
        try:
            with pdfplumber.open(str(pdf_path)) as pdf:
                for page_idx, page in enumerate(pdf.pages):
                    text = page.extract_text(layout=True) or page.extract_text() or ""
                    if text.strip():
                        full_text.append(f"--- PAGE {page_idx + 1} ---\n" + text)
            if full_text:
                return "\n".join(full_text)
        except Exception as e:
            print(f"pdfplumber extraction failed: {e}, falling back to pypdf")

    try:
        reader = pypdf.PdfReader(str(pdf_path))
        for page_idx, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            if text.strip():
                full_text.append(f"--- PAGE {page_idx + 1} ---\n" + text)
        return "\n".join(full_text)
    except Exception as e:
        print(f"pypdf extraction failed: {e}")
        return ""

def parse_pyq_document(raw_text: str, filename: str) -> Dict[str, Any]:
    lines = raw_text.splitlines()
    
    global_answer_key: Dict[int, str] = {}
    answer_key_patterns = [
        r"(?:(?:Q\.?|Question\s*)?(\d+)[\.\s\:\-\)]+\s*(?:\(?([A-Da-d1-4])\)?))",
        r"(\d+)\s*[-–=:]\s*\(?([A-Da-d1-4])\)?",
    ]
    
    ans_key_section = re.search(r"(?:ANSWER\s*KEYS?|ANSWERS|SOLUTIONS?|KEY SHEET)\s*[\:\n](.*)", raw_text, re.IGNORECASE | re.DOTALL)
    if ans_key_section:
        key_text = ans_key_section.group(1)
        for pat in answer_key_patterns:
            matches = re.findall(pat, key_text)
            for q_num, ans_val in matches:
                try:
                    q_int = int(q_num)
                    global_answer_key[q_int] = ans_val.upper()
                except ValueError:
                    continue

    topic_header_re = re.compile(
        r"^(?:(?:PART|SECTION|UNIT|MODULE|CHAPTER|TOPIC|SUBJECT)[\s\:\-\–]+([A-Z0-9\.\s\-\–&]+)|"
        r"(PHYSICS|CHEMISTRY|MATHEMATICS|BIOLOGY|GENERAL KNOWLEDGE|REASONING|APTITUDE|ENGLISH|POLITY|HISTORY|GEOGRAPHY|ECONOMICS|COMPUTER SCIENCE|DATA STRUCTURES|ALGORITHMS|ELECTRICAL|MECHANICAL|CIVIL))(?:\s*[\:\-\–]|\s*$)",
        re.IGNORECASE
    )

    q_start_re = re.compile(
        r"^(?:Q(?:uestion)?\.?\s*(\d+)[\.\:\-\)\s]|(?:(\d+)[\.\)]\s+)|(?:\[(\d+)\]\s+))",
        re.IGNORECASE
    )

    inline_ans_re = re.compile(r"(?:Ans(?:wer)?|Correct(?:\s*Option)?|Key)[\s\:\.\-\–=]+\(?\s*([A-Da-d1-4])\s*\)?", re.IGNORECASE)
    explanation_re = re.compile(r"(?:Explanation|Solution|Hint|Details?)[\s\:\.\-\–]+(.*)", re.IGNORECASE | re.DOTALL)

    current_topic = "General / Miscellaneous"
    questions = []
    current_q: Optional[Dict[str, Any]] = None
    q_counter = 0

    def finalize_question(q_obj):
        if not q_obj:
            return
        raw_q_text = q_obj.get("raw_body", "").strip()
        if not raw_q_text:
            return

        ans_match = inline_ans_re.search(raw_q_text)
        detected_ans = ""
        if ans_match:
            raw_val = ans_match.group(1).upper()
            val_map = {"1": "A", "2": "B", "3": "C", "4": "D"}
            detected_ans = val_map.get(raw_val, raw_val)
        elif q_obj.get("number") in global_answer_key:
            detected_ans = global_answer_key[q_obj["number"]]

        exp_match = explanation_re.search(raw_q_text)
        explanation = exp_match.group(1).strip() if exp_match else ""

        cleaned_body = inline_ans_re.sub("", raw_q_text)
        cleaned_body = explanation_re.sub("", cleaned_body).strip()

        options = []
        option_matches = list(re.finditer(r"(?:[\(\[\{]?([A-Da-d1-4])[\)\]\}][\.\s\:\-\–]*|\b([A-Da-d])[\.\:]\s+)(.*?)(?=(?:[\(\[\{]?[A-Da-d1-4][\)\]\}][\.\s\:\-\–]*|\b[A-Da-d][\.\:]\s+)|$)", cleaned_body, re.DOTALL))
        
        q_title = cleaned_body
        if option_matches and len(option_matches) >= 2:
            first_opt_idx = option_matches[0].start()
            q_title = cleaned_body[:first_opt_idx].strip()
            
            letter_map = {"1": "A", "2": "B", "3": "C", "4": "D"}
            seen_keys = set()
            for m in option_matches:
                key = (m.group(1) or m.group(2)).upper()
                key = letter_map.get(key, key)
                text = m.group(3).strip()
                text = re.sub(r"\s+", " ", text)
                if key in ["A", "B", "C", "D"] and key not in seen_keys and text:
                    seen_keys.add(key)
                    options.append({"key": key, "text": text})
        
        if len(options) < 2:
            sub_lines = [l.strip() for l in cleaned_body.splitlines() if l.strip()]
            q_title = sub_lines[0] if sub_lines else "Question"
            opt_labels = ["A", "B", "C", "D"]
            candidate_opts = []
            for sl in sub_lines[1:]:
                for lbl in opt_labels:
                    if sl.lower().startswith(f"({lbl.lower()})") or sl.lower().startswith(f"{lbl.lower()}."):
                        candidate_opts.append({"key": lbl, "text": re.sub(r"^[(\[]?[A-Da-d][)\]\.\:]\s*", "", sl).strip()})
                        break
            if len(candidate_opts) >= 2:
                options = candidate_opts

        if len(options) < 2:
            options = [
                {"key": "A", "text": "Option A (See PDF text)"},
                {"key": "B", "text": "Option B (See PDF text)"},
                {"key": "C", "text": "Option C (See PDF text)"},
                {"key": "D", "text": "Option D (See PDF text)"}
            ]

        if not detected_ans:
            detected_ans = "A"

        questions.append({
            "id": f"q_{len(questions) + 1}",
            "original_num": q_obj.get("number", len(questions) + 1),
            "topic": q_obj.get("topic", "General"),
            "question": q_title,
            "options": options,
            "correct_answer": detected_ans,
            "explanation": explanation or f"Extracted from original PYQ sheet ({filename})"
        })

    for line in lines:
        cleaned_line = line.strip()
        if not cleaned_line or cleaned_line.startswith("--- PAGE"):
            continue

        top_match = topic_header_re.search(cleaned_line)
        if top_match and len(cleaned_line) < 80:
            potential_topic = (top_match.group(1) or top_match.group(2) or "").strip()
            if len(potential_topic) >= 3:
                current_topic = potential_topic.title()
                continue

        q_match = q_start_re.match(cleaned_line)
        if q_match:
            finalize_question(current_q)
            q_num_str = q_match.group(1) or q_match.group(2) or q_match.group(3) or str(q_counter + 1)
            try:
                q_num = int(q_num_str)
            except ValueError:
                q_num = q_counter + 1
            q_counter += 1
            
            start_len = len(q_match.group(0))
            rest_of_line = cleaned_line[start_len:].strip()
            
            current_q = {
                "number": q_num,
                "topic": current_topic,
                "raw_body": rest_of_line
            }
        else:
            if current_q:
                current_q["raw_body"] += " " + cleaned_line

    finalize_question(current_q)

    topic_counts = {}
    for q in questions:
        t = q["topic"]
        topic_counts[t] = topic_counts.get(t, 0) + 1

    topics_summary = [{"name": t, "count": c} for t, c in topic_counts.items()]

    return {
        "title": Path(filename).stem.replace("_", " ").replace("-", " ").title(),
        "filename": filename,
        "total_questions": len(questions),
        "topics": topics_summary,
        "questions": questions
    }

# ======================= API ROUTES =======================

@app.api_route("/", methods=["GET", "HEAD"], response_class=HTMLResponse)
@app.api_route("/index.html", methods=["GET", "HEAD"], response_class=HTMLResponse)
@app.api_route("/home", methods=["GET", "HEAD"], response_class=HTMLResponse)
@app.api_route("/quiz", methods=["GET", "HEAD"], response_class=HTMLResponse)
async def serve_home():
    for candidate in [TEMPLATES_DIR / "index.html", BASE_DIR / "index.html"]:
        if candidate.exists():
            try:
                with open(candidate, "r", encoding="utf-8") as f:
                    return HTMLResponse(content=f.read())
            except Exception:
                pass
    return HTMLResponse(content=EMBEDDED_HTML_PAGE)

@app.get("/health")
@app.get("/healthz")
async def health_check():
    return JSONResponse({"status": "ok", "app": "PYQ Quiz Master"})

@app.post("/api/upload")
async def upload_pdf(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    file_id = str(uuid.uuid4())[:8]
    safe_filename = f"{file_id}_{file.filename}"
    saved_pdf_path = UPLOAD_DIR / safe_filename

    with open(saved_pdf_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    raw_text = extract_text_from_pdf(saved_pdf_path)
    if not raw_text.strip():
        raise HTTPException(status_code=400, detail="Could not extract readable text from PDF. Ensure it contains text and is not an image-only scan.")

    parsed_quiz = parse_pyq_document(raw_text, file.filename)
    if parsed_quiz["total_questions"] == 0:
        raise HTTPException(
            status_code=422,
            detail="No formatted questions detected. Please ensure your PDF has numbered questions (e.g. 1., Q1., Question 1) and options (A, B, C, D)."
        )

    quiz_id = f"quiz_{file_id}"
    parsed_quiz["id"] = quiz_id
    parsed_quiz["created_at"] = str(Path(saved_pdf_path).stat().st_ctime)

    db = load_db()
    db[quiz_id] = parsed_quiz
    save_db(db)

    return JSONResponse({
        "status": "success",
        "quiz_id": quiz_id,
        "title": parsed_quiz["title"],
        "total_questions": parsed_quiz["total_questions"],
        "topics": parsed_quiz["topics"]
    })

@app.get("/api/quizzes")
async def get_all_quizzes():
    db = load_db()
    summary = []
    for q_id, q_data in db.items():
        summary.append({
            "id": q_id,
            "title": q_data.get("title", "Untitled Quiz"),
            "filename": q_data.get("filename", ""),
            "total_questions": q_data.get("total_questions", 0),
            "topics": q_data.get("topics", [])
        })
    return JSONResponse(summary)

@app.get("/api/quiz/{quiz_id}")
async def get_quiz(quiz_id: str, topic: Optional[str] = None):
    db = load_db()
    quiz = db.get(quiz_id)
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    questions = quiz["questions"]
    if topic and topic.lower() != "all":
        questions = [q for q in questions if q["topic"].lower() == topic.lower()]

    client_questions = []
    for q in questions:
        client_questions.append({
            "id": q["id"],
            "original_num": q.get("original_num"),
            "topic": q["topic"],
            "question": q["question"],
            "options": q["options"]
        })

    return JSONResponse({
        "id": quiz_id,
        "title": quiz["title"],
        "selected_topic": topic or "All Topics",
        "total_questions": len(client_questions),
        "topics": quiz["topics"],
        "questions": client_questions
    })

@app.post("/api/quiz/{quiz_id}/submit")
async def submit_quiz(quiz_id: str, payload: Dict[str, Any]):
    db = load_db()
    quiz = db.get(quiz_id)
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    user_answers: Dict[str, str] = payload.get("answers", {})
    time_taken: int = payload.get("time_taken_seconds", 0)

    all_questions_map = {q["id"]: q for q in quiz["questions"]}

    correct_count = 0
    wrong_count = 0
    unattempted_count = 0
    detailed_review = []
    topic_performance = {}

    for q_id, q_data in all_questions_map.items():
        user_choice = user_answers.get(q_id, "").upper().strip()
        correct_ans = q_data.get("correct_answer", "").upper().strip()
        is_correct = (user_choice == correct_ans) and (user_choice != "")
        is_unattempted = (user_choice == "")

        if is_unattempted:
            unattempted_count += 1
            status = "unattempted"
        elif is_correct:
            correct_count += 1
            status = "correct"
        else:
            wrong_count += 1
            status = "wrong"

        t_name = q_data.get("topic", "General")
        if t_name not in topic_performance:
            topic_performance[t_name] = {"total": 0, "correct": 0, "wrong": 0, "unattempted": 0}
        topic_performance[t_name]["total"] += 1
        topic_performance[t_name][status] += 1

        detailed_review.append({
            "id": q_id,
            "original_num": q_data.get("original_num"),
            "topic": t_name,
            "question": q_data["question"],
            "options": q_data["options"],
            "user_choice": user_choice,
            "correct_answer": correct_ans,
            "is_correct": is_correct,
            "status": status,
            "explanation": q_data.get("explanation", "")
        })

    total_submitted_eval = len(detailed_review)
    percentage = round((correct_count / total_submitted_eval * 100), 2) if total_submitted_eval > 0 else 0

    return JSONResponse({
        "quiz_id": quiz_id,
        "title": quiz["title"],
        "total_questions": total_submitted_eval,
        "score": correct_count,
        "wrong": wrong_count,
        "unattempted": unattempted_count,
        "percentage": percentage,
        "time_taken_seconds": time_taken,
        "topic_performance": topic_performance,
        "review": detailed_review
    })

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    print(f"Starting PYQ Quiz Server on port {port}")
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=True)
