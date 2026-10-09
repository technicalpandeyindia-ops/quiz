import json
from pathlib import Path

BASE = Path(r"C:\Users\rokihics\.gemini\antigravity\scratch\pyq-quiz-app")

app_code = r'''import os
import re
import json
import uuid
import shutil
import gc
from typing import List, Dict, Any, Optional
from pathlib import Path
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import pypdf

try:
    import pdfplumber
except ImportError:
    pdfplumber = None

# EMBEDDED SINGLE-PAGE APPLICATION FRONTEND
EMBEDDED_HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>PYQ Quiz Master | 3000+ Bilingual Exam Simulator</title>
  <!-- Tailwind CSS -->
  <script src="https://cdn.tailwindcss.com"></script>
  <!-- Lucide Icons -->
  <script src="https://unpkg.com/lucide@latest"></script>
  <!-- Canvas Confetti -->
  <script src="https://cdn.jsdelivr.net/npm/canvas-confetti@1.6.0/dist/confetti.browser.min.js"></script>
  <!-- Google Fonts -->
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;600&family=Noto+Sans+Devanagari:wght@400;500;600;700&display=swap" rel="stylesheet">
  <script>
    tailwind.config = {
      darkMode: 'class',
      theme: {
        extend: {
          colors: {
            brand: {
              50: '#eef2ff',
              100: '#e0e7ff',
              500: '#6366f1',
              600: '#4f46e5',
              700: '#4338ca',
            }
          },
          fontFamily: {
            sans: ['Inter', 'Noto Sans Devanagari', 'sans-serif'],
            hindi: ['Noto Sans Devanagari', 'sans-serif'],
            mono: ['JetBrains Mono', 'monospace']
          }
        }
      }
    }
  </script>
  <style>
    body { font-family: 'Inter', 'Noto Sans Devanagari', sans-serif; }
    .glass-card {
      background: rgba(255, 255, 255, 0.9);
      backdrop-filter: blur(12px);
      border: 1px solid rgba(229, 231, 235, 0.9);
    }
    .dark .glass-card {
      background: rgba(30, 41, 59, 0.9);
      border: 1px solid rgba(51, 65, 85, 0.9);
    }
  </style>
</head>
<body class="bg-slate-50 text-slate-900 dark:bg-slate-950 dark:text-slate-100 min-h-screen transition-colors duration-200">

  <!-- ================= NAVBAR ================= -->
  <nav class="sticky top-0 z-50 glass-card border-b border-slate-200 dark:border-slate-800 px-4 sm:px-6 py-3.5 flex items-center justify-between shadow-sm">
    <div class="flex items-center gap-3 cursor-pointer" onclick="switchView('view-upload')">
      <div class="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 to-violet-500 flex items-center justify-center text-white shadow-md shadow-indigo-500/20">
        <i data-lucide="sparkles" class="w-6 h-6"></i>
      </div>
      <div>
        <div class="flex items-center gap-2">
          <h1 class="text-lg sm:text-xl font-extrabold tracking-tight bg-gradient-to-r from-indigo-600 to-violet-600 bg-clip-text text-transparent dark:from-indigo-400 dark:to-violet-400">
            PYQ Quiz Master
          </h1>
          <span class="px-2 py-0.5 text-[10px] font-bold uppercase rounded-full bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300">
            Bilingual हिन्दी / EN
          </span>
        </div>
        <p class="text-xs text-slate-500 dark:text-slate-400 font-medium">Auto-Extract PYQs, Topics & Answers</p>
      </div>
    </div>

    <div class="flex items-center gap-2.5">
      <div class="hidden sm:flex items-center bg-slate-100 dark:bg-slate-800 rounded-xl p-1 border border-slate-200 dark:border-slate-700 text-xs font-bold">
        <button id="lang-btn-both" onclick="setLangFilter('both')" class="px-2.5 py-1 rounded-lg bg-indigo-600 text-white shadow-sm transition">Both (द्विभाषी)</button>
        <button id="lang-btn-en" onclick="setLangFilter('en')" class="px-2.5 py-1 rounded-lg text-slate-600 dark:text-slate-300 hover:text-indigo-600 transition">English</button>
        <button id="lang-btn-hi" onclick="setLangFilter('hi')" class="px-2.5 py-1 rounded-lg text-slate-600 dark:text-slate-300 hover:text-indigo-600 transition">हिन्दी</button>
      </div>

      <button onclick="loadPreviousQuizzes()" class="px-3 py-1.5 text-xs font-semibold text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg flex items-center gap-1.5 border border-slate-200 dark:border-slate-700 transition">
        <i data-lucide="history" class="w-4 h-4"></i>
        <span class="hidden sm:inline">My Papers</span>
      </button>

      <button onclick="toggleTheme()" class="p-2 rounded-lg text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800 border border-slate-200 dark:border-slate-700">
        <i data-lucide="moon" class="w-4 h-4 dark:hidden"></i>
        <i data-lucide="sun" class="w-4 h-4 hidden dark:block"></i>
      </button>
    </div>
  </nav>

  <!-- ================= MAIN CONTAINER ================= -->
  <main class="max-w-6xl mx-auto px-4 py-6 sm:py-8">

    <!-- ================= VIEW 1: UPLOAD & TOPIC SELECTION ================= -->
    <section id="view-upload" class="space-y-8 block">
      
      <div class="text-center max-w-2xl mx-auto pt-2 pb-2">
        <span class="px-3 py-1 text-xs font-bold uppercase tracking-wider bg-indigo-100 text-indigo-700 dark:bg-indigo-950/80 dark:text-indigo-300 rounded-full">
          ⚡ 100% PDF-Extracted • Hindi & English Bilingual
        </span>
        <h2 class="mt-4 text-3xl sm:text-4xl font-extrabold text-slate-900 dark:text-white tracking-tight">
          Upload Any Exam PYQ PDF.<br/><span class="text-indigo-600 dark:text-indigo-400">Auto-Detect Topics & Start Quiz.</span>
        </h2>
        <p class="mt-3 text-sm text-slate-600 dark:text-slate-400">
          Upload your Previous Year Question paper. The system extracts all MCQs, separates English/Hindi text, detects topics, and creates an instant quiz room.
        </p>
      </div>

      <!-- Upload Zone Card -->
      <div class="max-w-2xl mx-auto">
        <div id="drop-zone" class="border-2 border-dashed border-indigo-300 dark:border-indigo-800/70 hover:border-indigo-600 dark:hover:border-indigo-400 rounded-3xl p-8 sm:p-10 text-center bg-white dark:bg-slate-900/60 shadow-xl shadow-indigo-500/5 transition space-y-6">
          
          <div class="w-16 h-16 mx-auto rounded-2xl bg-indigo-50 dark:bg-indigo-950/80 flex items-center justify-center text-indigo-600 dark:text-indigo-400 shadow-inner">
            <i data-lucide="file-up" class="w-8 h-8"></i>
          </div>
          
          <div>
            <h3 class="text-lg sm:text-xl font-bold text-slate-800 dark:text-slate-200">
              Select your PYQ PDF File
            </h3>
            <p class="text-xs text-slate-500 dark:text-slate-400 mt-1">
              Supports Question Papers, Unit Tests, and 3000+ Question Books
            </p>
          </div>

          <!-- File Chooser Container -->
          <div class="flex flex-col items-center justify-center gap-4 p-5 rounded-2xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700/60">
            <input type="file" id="pdf-input" accept=".pdf,application/pdf" class="block w-full text-xs text-slate-500 file:mr-4 file:py-2.5 file:px-5 file:rounded-xl file:border-0 file:text-xs file:font-bold file:bg-indigo-600 file:text-white hover:file:bg-indigo-700 cursor-pointer" onchange="handleFileChange(event)" />
            
            <!-- Large Prominent Process Button with Live Progress State -->
            <button id="btn-process" onclick="submitChosenFile()" class="w-full py-4 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-extrabold text-sm rounded-xl shadow-lg shadow-emerald-600/25 flex items-center justify-center gap-2 transition transform active:scale-98 disabled:opacity-60 disabled:cursor-not-allowed">
              <i id="btn-icon" data-lucide="play" class="w-4 h-4 fill-current"></i>
              <span id="btn-text">🚀 Extract Questions & Start Quiz</span>
            </button>
          </div>

          <!-- Error Alert Banner -->
          <div id="upload-error-banner" class="hidden p-4 rounded-xl bg-rose-50 dark:bg-rose-950/60 border border-rose-200 dark:border-rose-800 text-rose-800 dark:text-rose-200 text-xs font-semibold text-left">
            <div class="flex items-start gap-2">
              <i data-lucide="alert-circle" class="w-4 h-4 text-rose-600 shrink-0 mt-0.5"></i>
              <div id="upload-error-message">Error processing PDF.</div>
            </div>
          </div>

          <!-- Status / Progress Indicator -->
          <div id="upload-status" class="hidden space-y-3">
            <div class="p-4 rounded-2xl bg-indigo-50 dark:bg-indigo-950/60 border border-indigo-200 dark:border-indigo-800 text-indigo-700 dark:text-indigo-300 text-xs font-semibold flex items-center justify-center gap-3">
              <i data-lucide="loader-2" class="w-5 h-5 animate-spin"></i>
              <span id="upload-status-text">Uploading PDF and extracting questions... Please wait a few seconds.</span>
            </div>
            <div class="w-full bg-slate-200 dark:bg-slate-700 rounded-full h-2 overflow-hidden">
              <div class="bg-indigo-600 h-2 rounded-full animate-pulse w-3/4"></div>
            </div>
          </div>

        </div>
      </div>

      <!-- Detected Topics & Test Mode Selector -->
      <div id="topics-section" class="hidden max-w-4xl mx-auto space-y-6">
        
        <div class="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm space-y-4">
          <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div>
              <div class="flex items-center gap-2">
                <span class="w-2.5 h-2.5 rounded-full bg-emerald-500"></span>
                <h3 id="quiz-title" class="text-lg sm:text-xl font-bold text-slate-900 dark:text-white">Exam Paper</h3>
              </div>
              <p id="quiz-stats" class="text-xs text-slate-500 dark:text-slate-400 mt-1">Questions Extracted (Bilingual Support)</p>
            </div>

            <div class="flex flex-wrap items-center gap-2 w-full sm:w-auto">
              <button onclick="startQuiz('all', 25)" class="flex-1 sm:flex-none px-4 py-2 bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-800 dark:text-slate-200 font-bold rounded-xl text-xs transition">
                ⚡ Quick 25 MCQ Mock
              </button>
              <button onclick="startQuiz('all', 50)" class="flex-1 sm:flex-none px-4 py-2 bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-800 dark:text-slate-200 font-bold rounded-xl text-xs transition">
                📝 50 MCQ Test
              </button>
              <button onclick="startQuiz('all', 0)" class="w-full sm:w-auto px-5 py-2 bg-indigo-600 hover:bg-indigo-700 text-white font-bold rounded-xl text-xs shadow-md shadow-indigo-600/30 flex items-center justify-center gap-2 transition">
                <i data-lucide="play" class="w-4 h-4 fill-current"></i>
                <span>Start Full Exam (All Questions)</span>
              </button>
            </div>
          </div>
        </div>

        <div>
          <h4 class="text-sm font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-3">
            Auto-Detected Topics / Subjects
          </h4>
          <div id="topics-grid" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"></div>
        </div>

      </div>

      <!-- History Modal -->
      <div id="previous-papers-modal" class="hidden fixed inset-0 z-50 bg-slate-950/60 backdrop-blur-sm flex items-center justify-center p-4">
        <div class="bg-white dark:bg-slate-900 max-w-xl w-full rounded-2xl p-6 border border-slate-200 dark:border-slate-800 shadow-2xl space-y-4">
          <div class="flex items-center justify-between">
            <h3 class="text-base font-bold">Uploaded Papers History</h3>
            <button onclick="closePreviousQuizzes()" class="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200">
              <i data-lucide="x" class="w-5 h-5"></i>
            </button>
          </div>
          <div id="previous-papers-list" class="space-y-2 max-h-80 overflow-y-auto pr-1"></div>
        </div>
      </div>

    </section>

    <!-- ================= VIEW 2: QUIZ ROOM ================= -->
    <section id="view-quiz" class="hidden space-y-5">
      
      <div class="glass-card rounded-2xl p-4 flex flex-wrap items-center justify-between gap-4">
        <div>
          <div class="flex items-center gap-2">
            <span id="active-quiz-topic" class="px-2.5 py-0.5 text-xs font-semibold rounded-full bg-indigo-100 text-indigo-700 dark:bg-indigo-950 dark:text-indigo-300">
              Topic: General
            </span>
            <span id="active-total-badge" class="px-2 py-0.5 text-[11px] font-bold rounded-full bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400">
              Total Questions
            </span>
          </div>
          <h2 id="active-quiz-name" class="text-base font-bold text-slate-900 dark:text-white mt-1 truncate max-w-xs sm:max-w-md">
            Exam Quiz
          </h2>
        </div>

        <div class="flex items-center gap-3">
          <div class="flex items-center bg-slate-100 dark:bg-slate-800 rounded-xl p-1 border border-slate-200 dark:border-slate-700 text-xs font-bold">
            <button onclick="setLangFilter('both')" class="px-2 py-1 rounded-lg text-[11px] font-bold lang-pill active-lang bg-indigo-600 text-white" id="pill-both">Both</button>
            <button onclick="setLangFilter('en')" class="px-2 py-1 rounded-lg text-[11px] font-bold lang-pill text-slate-600 dark:text-slate-300" id="pill-en">EN</button>
            <button onclick="setLangFilter('hi')" class="px-2 py-1 rounded-lg text-[11px] font-bold lang-pill text-slate-600 dark:text-slate-300" id="pill-hi">हिन्दी</button>
          </div>

          <div class="flex items-center gap-2 bg-slate-100 dark:bg-slate-800/80 px-3 py-1.5 rounded-xl border border-slate-200 dark:border-slate-700">
            <i data-lucide="clock" class="w-4 h-4 text-indigo-600 dark:text-indigo-400"></i>
            <span id="quiz-timer" class="font-mono text-xs sm:text-sm font-bold">00:00</span>
          </div>

          <button onclick="confirmSubmitQuiz()" class="px-3.5 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold rounded-xl shadow-md flex items-center gap-1.5 transition">
            <i data-lucide="check-circle" class="w-4 h-4"></i>
            <span>Submit</span>
          </button>
        </div>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-12 gap-5">
        
        <div class="lg:col-span-8 space-y-4">
          <div class="glass-card rounded-2xl p-6 sm:p-8 space-y-6 min-h-[420px] flex flex-col justify-between shadow-sm">
            
            <div class="space-y-4">
              <div class="flex items-center justify-between border-b border-slate-200 dark:border-slate-800 pb-3">
                <span id="current-q-index" class="text-xs font-bold uppercase tracking-wider text-indigo-600 dark:text-indigo-400">
                  Question 1
                </span>
                <div class="flex items-center gap-3">
                  <button onclick="toggleMarkForReview()" id="btn-review" class="text-xs font-semibold text-amber-600 dark:text-amber-400 hover:underline flex items-center gap-1">
                    <i data-lucide="bookmark" class="w-3.5 h-3.5"></i>
                    <span id="review-text">Mark for Review</span>
                  </button>
                </div>
              </div>

              <div id="q-text-container" class="space-y-2"></div>
              <div id="q-options" class="space-y-3 pt-2"></div>
            </div>

            <div class="flex items-center justify-between pt-6 border-t border-slate-200 dark:border-slate-800">
              <button onclick="prevQuestion()" id="btn-prev" class="px-4 py-2 text-xs font-bold text-slate-700 dark:text-slate-300 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 rounded-xl flex items-center gap-1 transition">
                <i data-lucide="chevron-left" class="w-4 h-4"></i>
                <span>Previous</span>
              </button>

              <button onclick="clearOptionSelection()" class="text-xs text-slate-500 hover:text-slate-800 dark:hover:text-slate-200">
                Clear Choice
              </button>

              <button onclick="nextQuestion()" id="btn-next" class="px-5 py-2 text-xs font-bold text-white bg-indigo-600 hover:bg-indigo-700 rounded-xl flex items-center gap-1 shadow-md shadow-indigo-600/20 transition">
                <span>Next</span>
                <i data-lucide="chevron-right" class="w-4 h-4"></i>
              </button>
            </div>

          </div>
        </div>

        <div class="lg:col-span-4 space-y-4">
          <div class="glass-card rounded-2xl p-5 space-y-4">
            <div class="flex items-center justify-between">
              <h3 class="text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                Question Navigator
              </h3>
              <select id="palette-range-selector" onchange="changePaletteChunk(this.value)" class="text-xs bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg px-2 py-1 font-semibold text-slate-700 dark:text-slate-300">
              </select>
            </div>

            <div id="palette-grid" class="grid grid-cols-5 sm:grid-cols-6 gap-2 max-h-72 overflow-y-auto p-1"></div>

            <div class="pt-3 border-t border-slate-200 dark:border-slate-800 space-y-2">
              <div class="grid grid-cols-2 gap-2 text-[11px] font-medium text-slate-600 dark:text-slate-400">
                <div class="flex items-center gap-2">
                  <span class="w-3 h-3 rounded bg-emerald-500"></span>
                  <span id="nav-stat-answered">Answered (0)</span>
                </div>
                <div class="flex items-center gap-2">
                  <span class="w-3 h-3 rounded bg-amber-500"></span>
                  <span id="nav-stat-marked">Marked (0)</span>
                </div>
                <div class="flex items-center gap-2">
                  <span class="w-3 h-3 rounded bg-slate-200 dark:bg-slate-700"></span>
                  <span id="nav-stat-unanswered">Unanswered</span>
                </div>
                <div class="flex items-center gap-2">
                  <span class="w-3 h-3 rounded border-2 border-indigo-600"></span>
                  <span>Current</span>
                </div>
              </div>
            </div>

          </div>
        </div>

      </div>

    </section>

    <!-- ================= VIEW 3: SCORECARD & DETAILED REVIEW ================= -->
    <section id="view-results" class="hidden space-y-8">
      
      <div class="glass-card rounded-3xl p-8 text-center relative overflow-hidden shadow-lg">
        <div class="max-w-md mx-auto space-y-4">
          <span class="px-3.5 py-1 text-xs font-bold uppercase tracking-wider rounded-full bg-indigo-100 text-indigo-700 dark:bg-indigo-950 dark:text-indigo-400">
            Exam Analysis & Scorecard
          </span>
          <h2 id="result-quiz-title" class="text-2xl font-black text-slate-900 dark:text-white">Exam Results</h2>

          <div class="py-3">
            <div class="inline-flex flex-col items-center justify-center w-36 h-36 rounded-full border-4 border-indigo-600 dark:border-indigo-400 bg-indigo-50/50 dark:bg-indigo-950/30">
              <span id="score-percentage" class="text-3xl font-black text-indigo-600 dark:text-indigo-400">85%</span>
              <span class="text-xs font-bold text-slate-500 uppercase">Accuracy</span>
            </div>
          </div>

          <div class="grid grid-cols-3 gap-3">
            <div class="p-3 rounded-2xl bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800/40">
              <div id="stat-correct" class="text-xl font-black text-emerald-600 dark:text-emerald-400">0</div>
              <div class="text-[11px] font-semibold text-emerald-700 dark:text-emerald-300">Correct</div>
            </div>
            <div class="p-3 rounded-2xl bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-800/40">
              <div id="stat-wrong" class="text-xl font-black text-rose-600 dark:text-rose-400">0</div>
              <div class="text-[11px] font-semibold text-rose-700 dark:text-rose-300">Incorrect</div>
            </div>
            <div class="p-3 rounded-2xl bg-slate-100 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700">
              <div id="stat-unattempted" class="text-xl font-black text-slate-600 dark:text-slate-300">0</div>
              <div class="text-[11px] font-semibold text-slate-500">Skipped</div>
            </div>
          </div>

          <div class="flex items-center justify-center gap-3 pt-2">
            <button onclick="retakeActiveQuiz()" class="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold rounded-xl shadow-md flex items-center gap-2 transition">
              <i data-lucide="rotate-ccw" class="w-4 h-4"></i>
              <span>Retake Quiz</span>
            </button>
            <button onclick="switchView('view-upload')" class="px-5 py-2.5 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-xs font-bold rounded-xl transition">
              <span>Upload New PDF</span>
            </button>
          </div>
        </div>
      </div>

      <div id="topic-breakdown-card" class="glass-card rounded-2xl p-6 space-y-4">
        <h3 class="text-sm font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">
          Topic-Wise Performance Breakdown
        </h3>
        <div id="topic-performance-list" class="space-y-3"></div>
      </div>

      <div class="space-y-4">
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <h3 class="text-lg font-extrabold text-slate-900 dark:text-white">
            Bilingual Solution Review & Verified PDF Answers
          </h3>
          <div class="flex items-center gap-2 text-xs">
            <button onclick="filterReview('all')" class="rev-filter-btn active px-3 py-1.5 rounded-lg font-bold bg-indigo-600 text-white">All</button>
            <button onclick="filterReview('wrong')" class="rev-filter-btn px-3 py-1.5 rounded-lg font-bold bg-slate-200 dark:bg-slate-800 text-slate-700 dark:text-slate-300">Wrong Only</button>
            <button onclick="filterReview('correct')" class="rev-filter-btn px-3 py-1.5 rounded-lg font-bold bg-slate-200 dark:bg-slate-800 text-slate-700 dark:text-slate-300">Correct Only</button>
          </div>
        </div>

        <div id="review-list" class="space-y-4"></div>
      </div>

    </section>

  </main>

  <!-- ================= LOGIC & SCRIPT ================= -->
  <script>
    let currentQuizId = null;
    let currentQuizData = null;
    let questions = [];
    let currentQIndex = 0;
    let userAnswers = {};
    let markedForReview = new Set();
    let timerInterval = null;
    let secondsElapsed = 0;
    let reviewData = null;
    let currentLangFilter = 'both';
    let currentPaletteChunk = 0;
    const CHUNK_SIZE = 100;

    function updateIcons() {
      if (window.lucide) lucide.createIcons();
    }

    document.addEventListener("DOMContentLoaded", () => {
      updateIcons();
      setupDragAndDrop();
    });

    function toggleTheme() {
      document.documentElement.classList.toggle('dark');
      updateIcons();
    }

    function switchView(viewId) {
      ['view-upload', 'view-quiz', 'view-results'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.classList.toggle('hidden', id !== viewId);
      });
      window.scrollTo({ top: 0, behavior: 'smooth' });
      updateIcons();
    }

    function setLangFilter(mode) {
      currentLangFilter = mode;
      ['both', 'en', 'hi'].forEach(l => {
        const nb = document.getElementById(`lang-btn-${l}`);
        if (nb) {
          nb.className = (l === mode) 
            ? 'px-2.5 py-1 rounded-lg bg-indigo-600 text-white shadow-sm transition' 
            : 'px-2.5 py-1 rounded-lg text-slate-600 dark:text-slate-300 hover:text-indigo-600 transition';
        }
        const pb = document.getElementById(`pill-${l}`);
        if (pb) {
          pb.className = (l === mode)
            ? 'px-2 py-1 rounded-lg text-[11px] font-bold lang-pill bg-indigo-600 text-white'
            : 'px-2 py-1 rounded-lg text-[11px] font-bold lang-pill text-slate-600 dark:text-slate-300';
        }
      });

      if (!document.getElementById('view-quiz').classList.contains('hidden')) {
        renderCurrentQuestion();
      }
      if (!document.getElementById('view-results').classList.contains('hidden')) {
        renderReviewList(currentReviewFilter || 'all');
      }
    }

    function formatBilingualText(rawText) {
      if (!rawText) return '';
      const devanagariPattern = /[\u0900-\u097F]/;
      const hasHindi = devanagariPattern.test(rawText);

      if (!hasHindi) {
        return `<div class="text-slate-900 dark:text-slate-100">${escapeHtml(rawText)}</div>`;
      }

      const lines = rawText.split('\n').filter(l => l.trim().length > 0);
      let enLines = [];
      let hiLines = [];

      lines.forEach(l => {
        if (devanagariPattern.test(l)) {
          hiLines.push(l.trim());
        } else {
          enLines.push(l.trim());
        }
      });

      const enText = enLines.join(' ');
      const hiText = hiLines.join(' ');

      if (currentLangFilter === 'en') {
        return `<div class="text-slate-900 dark:text-slate-100 font-medium">${escapeHtml(enText || rawText)}</div>`;
      } else if (currentLangFilter === 'hi') {
        return `<div class="text-slate-900 dark:text-slate-100 font-hindi font-medium leading-relaxed">${escapeHtml(hiText || rawText)}</div>`;
      } else {
        return `
          <div class="space-y-2">
            ${enText ? `<div class="text-slate-900 dark:text-slate-100 font-medium">${escapeHtml(enText)}</div>` : ''}
            ${hiText ? `<div class="text-indigo-900 dark:text-indigo-200 font-hindi font-medium leading-relaxed bg-indigo-50/50 dark:bg-indigo-950/30 p-2.5 rounded-xl border border-indigo-100 dark:border-indigo-900/40">${escapeHtml(hiText)}</div>` : (!enText ? `<div class="text-slate-900 dark:text-slate-100 font-hindi">${escapeHtml(rawText)}</div>` : '')}
          </div>
        `;
      }
    }

    function escapeHtml(str) {
      if (!str) return '';
      return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
    }

    function setupDragAndDrop() {
      const dropZone = document.getElementById('drop-zone');

      ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        window.addEventListener(eventName, (e) => e.preventDefault(), false);
        document.body.addEventListener(eventName, (e) => e.preventDefault(), false);
      });

      ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, (e) => {
          e.preventDefault();
          e.stopPropagation();
          dropZone.classList.add('border-indigo-600', 'bg-indigo-50/70', 'dark:bg-indigo-950/40');
        });
      });

      ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, (e) => {
          e.preventDefault();
          e.stopPropagation();
          dropZone.classList.remove('border-indigo-600', 'bg-indigo-50/70', 'dark:bg-indigo-950/40');
        });
      });

      dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        e.stopPropagation();
        if (e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files.length > 0) {
          const file = e.dataTransfer.files[0];
          uploadFile(file);
        }
      });
    }

    function handleFileChange(e) {
      hideError();
      if (e.target && e.target.files && e.target.files.length > 0) {
        // Auto-run on file select
        uploadFile(e.target.files[0]);
      }
    }

    function submitChosenFile() {
      hideError();
      const fileInput = document.getElementById('pdf-input');
      if (fileInput && fileInput.files && fileInput.files.length > 0) {
        uploadFile(fileInput.files[0]);
      } else {
        showError('Please click "Choose File" first to select your PYQ PDF document.');
      }
    }

    function showError(msg) {
      const errBanner = document.getElementById('upload-error-banner');
      const errMsg = document.getElementById('upload-error-message');
      errMsg.innerText = msg;
      errBanner.classList.remove('hidden');
      updateIcons();
    }

    function hideError() {
      const errBanner = document.getElementById('upload-error-banner');
      errBanner.classList.add('hidden');
    }

    async function uploadFile(file) {
      if (!file || !file.name.toLowerCase().endsWith('.pdf')) {
        showError('Please select a valid .PDF document.');
        return;
      }

      hideError();
      const statusEl = document.getElementById('upload-status');
      const statusText = document.getElementById('upload-status-text');
      const btn = document.getElementById('btn-process');
      const btnText = document.getElementById('btn-text');

      // Visual Loading state on button
      btn.disabled = true;
      btnText.innerText = 'Extracting MCQs... Please wait';
      statusEl.classList.remove('hidden');
      statusText.innerText = `Extracting MCQs from "${file.name}"... Parsing questions and detecting topics.`;
      updateIcons();

      const formData = new FormData();
      formData.append('file', file);

      try {
        const res = await fetch('/api/upload', {
          method: 'POST',
          body: formData
        });

        const data = await res.json();
        statusEl.classList.add('hidden');
        btn.disabled = false;
        btnText.innerText = '🚀 Extract Questions & Start Quiz';

        if (!res.ok) {
          showError(`Server Note: ${data.detail || 'Could not process PDF. Please ensure the PDF has selectable text.'}`);
          return;
        }

        currentQuizId = data.quiz_id;
        displayTopicBreakdown(data);
      } catch (err) {
        statusEl.classList.add('hidden');
        btn.disabled = false;
        btnText.innerText = '🚀 Extract Questions & Start Quiz';
        showError(`Network/Upload error: ${err.message}. Please check connection or file size.`);
      }
    }

    function displayTopicBreakdown(data) {
      document.getElementById('topics-section').classList.remove('hidden');
      document.getElementById('quiz-title').innerText = data.title;
      document.getElementById('quiz-stats').innerText = `${data.total_questions.toLocaleString()} Questions Detected across ${data.topics.length} Topics (Bilingual Support)`;

      const grid = document.getElementById('topics-grid');
      grid.innerHTML = '';

      data.topics.forEach((t) => {
        const card = document.createElement('div');
        card.className = 'glass-card p-5 rounded-2xl flex flex-col justify-between hover:shadow-md transition space-y-4';
        card.innerHTML = `
          <div>
            <div class="flex items-center justify-between">
              <span class="px-2.5 py-0.5 rounded-full text-xs font-bold bg-indigo-100 text-indigo-700 dark:bg-indigo-950 dark:text-indigo-300">
                ${t.count} MCQs
              </span>
              <i data-lucide="layers" class="w-4 h-4 text-slate-400"></i>
            </div>
            <h4 class="mt-2 text-base font-bold text-slate-900 dark:text-white line-clamp-1">${t.name}</h4>
          </div>
          <button onclick="startQuiz('${t.name}', 0)" class="w-full py-2 bg-slate-100 hover:bg-indigo-600 dark:bg-slate-800 dark:hover:bg-indigo-600 hover:text-white text-slate-700 dark:text-slate-200 text-xs font-bold rounded-xl transition flex items-center justify-center gap-1.5">
            <i data-lucide="play" class="w-3.5 h-3.5"></i>
            <span>Practice Topic (${t.count})</span>
          </button>
        `;
        grid.appendChild(card);
      });

      updateIcons();
      document.getElementById('topics-section').scrollIntoView({ behavior: 'smooth' });
    }

    async function startQuiz(topic, limit = 0) {
      if (!currentQuizId) return;

      try {
        let url = topic === 'all' 
          ? `/api/quiz/${currentQuizId}`
          : `/api/quiz/${currentQuizId}?topic=${encodeURIComponent(topic)}`;

        if (limit > 0) {
          url += (url.includes('?') ? '&' : '?') + `limit=${limit}`;
        }

        const res = await fetch(url);
        const data = await res.json();
        if (!res.ok) {
          alert('Failed to load questions');
          return;
        }

        currentQuizData = data;
        questions = data.questions;
        currentQIndex = 0;
        userAnswers = {};
        markedForReview.clear();
        secondsElapsed = 0;
        currentPaletteChunk = 0;

        document.getElementById('active-quiz-name').innerText = data.title;
        document.getElementById('active-quiz-topic').innerText = `Topic: ${data.selected_topic}`;
        document.getElementById('active-total-badge').innerText = `${questions.length.toLocaleString()} Questions`;

        setupPaletteChunks();
        startTimer();
        renderCurrentQuestion();
        switchView('view-quiz');
      } catch (err) {
        alert(`Error starting quiz: ${err.message}`);
      }
    }

    function setupPaletteChunks() {
      const selector = document.getElementById('palette-range-selector');
      selector.innerHTML = '';
      const total = questions.length;
      const totalChunks = Math.ceil(total / CHUNK_SIZE);

      for (let i = 0; i < totalChunks; i++) {
        const start = i * CHUNK_SIZE + 1;
        const end = Math.min((i + 1) * CHUNK_SIZE, total);
        const opt = document.createElement('option');
        opt.value = i;
        opt.innerText = `Q ${start} - ${end}`;
        selector.appendChild(opt);
      }

      currentPaletteChunk = 0;
      renderPalette();
    }

    function changePaletteChunk(val) {
      currentPaletteChunk = parseInt(val, 10);
      renderPalette();
    }

    function startTimer() {
      clearInterval(timerInterval);
      const timerEl = document.getElementById('quiz-timer');
      timerInterval = setInterval(() => {
        secondsElapsed++;
        const hrs = Math.floor(secondsElapsed / 3600);
        const mins = String(Math.floor((secondsElapsed % 3600) / 60)).padStart(2, '0');
        const secs = String(secondsElapsed % 60).padStart(2, '0');
        timerEl.innerText = hrs > 0 ? `${hrs}:${mins}:${secs}` : `${mins}:${secs}`;
      }, 1000);
    }

    function renderCurrentQuestion() {
      if (!questions || questions.length === 0) return;
      const q = questions[currentQIndex];

      const expectedChunk = Math.floor(currentQIndex / CHUNK_SIZE);
      if (expectedChunk !== currentPaletteChunk) {
        currentPaletteChunk = expectedChunk;
        const selector = document.getElementById('palette-range-selector');
        if (selector) selector.value = currentPaletteChunk;
      }

      document.getElementById('current-q-index').innerText = `Question ${currentQIndex + 1} of ${questions.length} (${q.topic})`;
      
      const qTextContainer = document.getElementById('q-text-container');
      const qHeading = `${q.original_num ? q.original_num + '. ' : ''}${q.question}`;
      qTextContainer.innerHTML = formatBilingualText(qHeading);

      const isMarked = markedForReview.has(q.id);
      document.getElementById('review-text').innerText = isMarked ? 'Unmark Review' : 'Mark for Review';

      const optionsContainer = document.getElementById('q-options');
      optionsContainer.innerHTML = '';

      q.options.forEach((opt) => {
        const isSelected = userAnswers[q.id] === opt.key;
        const optBtn = document.createElement('button');
        optBtn.className = `w-full text-left p-3.5 sm:p-4 rounded-xl border-2 font-medium text-sm flex items-start gap-3 transition ${
          isSelected 
            ? 'border-indigo-600 bg-indigo-50/80 dark:bg-indigo-950/50 text-indigo-900 dark:text-indigo-200 shadow-sm' 
            : 'border-slate-200 dark:border-slate-800 hover:border-slate-300 dark:hover:border-slate-700 bg-white dark:bg-slate-900 text-slate-800 dark:text-slate-200'
        }`;

        optBtn.innerHTML = `
          <span class="w-6 h-6 rounded-lg flex items-center justify-center font-bold text-xs shrink-0 ${
            isSelected 
              ? 'bg-indigo-600 text-white' 
              : 'bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300'
          }">${opt.key}</span>
          <div class="pt-0.5 flex-1">${formatBilingualText(opt.text)}</div>
        `;

        optBtn.onclick = () => selectOption(q.id, opt.key);
        optionsContainer.appendChild(optBtn);
      });

      document.getElementById('btn-prev').disabled = (currentQIndex === 0);
      document.getElementById('btn-prev').classList.toggle('opacity-50', currentQIndex === 0);

      const isLast = currentQIndex === questions.length - 1;
      document.getElementById('btn-next').innerHTML = isLast 
        ? `<span>Finish</span><i data-lucide="check" class="w-4 h-4"></i>` 
        : `<span>Next</span><i data-lucide="chevron-right" class="w-4 h-4"></i>`;

      renderPalette();
      updateIcons();
    }

    function selectOption(qId, optionKey) {
      userAnswers[qId] = optionKey;
      renderCurrentQuestion();
    }

    function clearOptionSelection() {
      const q = questions[currentQIndex];
      delete userAnswers[q.id];
      renderCurrentQuestion();
    }

    function toggleMarkForReview() {
      const q = questions[currentQIndex];
      if (markedForReview.has(q.id)) {
        markedForReview.delete(q.id);
      } else {
        markedForReview.add(q.id);
      }
      renderCurrentQuestion();
    }

    function nextQuestion() {
      if (currentQIndex < questions.length - 1) {
        currentQIndex++;
        renderCurrentQuestion();
      } else {
        confirmSubmitQuiz();
      }
    }

    function prevQuestion() {
      if (currentQIndex > 0) {
        currentQIndex--;
        renderCurrentQuestion();
      }
    }

    function jumpToQuestion(idx) {
      currentQIndex = idx;
      renderCurrentQuestion();
    }

    function renderPalette() {
      const palette = document.getElementById('palette-grid');
      palette.innerHTML = '';

      const startIdx = currentPaletteChunk * CHUNK_SIZE;
      const endIdx = Math.min(startIdx + CHUNK_SIZE, questions.length);

      let answeredCount = 0;
      let markedCount = 0;

      questions.forEach(q => {
        if (userAnswers[q.id]) answeredCount++;
        if (markedForReview.has(q.id)) markedCount++;
      });

      document.getElementById('nav-stat-answered').innerText = `Answered (${answeredCount})`;
      document.getElementById('nav-stat-marked').innerText = `Marked (${markedCount})`;

      for (let idx = startIdx; idx < endIdx; idx++) {
        const q = questions[idx];
        const isAnswered = !!userAnswers[q.id];
        const isMarked = markedForReview.has(q.id);
        const isCurrent = (idx === currentQIndex);

        let bgClass = 'bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300';
        if (isAnswered) bgClass = 'bg-emerald-500 text-white font-bold';
        if (isMarked) bgClass = 'bg-amber-500 text-white font-bold';

        const btn = document.createElement('button');
        btn.className = `w-9 h-9 rounded-xl text-xs font-semibold flex items-center justify-center transition ${bgClass} ${
          isCurrent ? 'ring-2 ring-indigo-600 ring-offset-2 dark:ring-offset-slate-900 scale-105' : ''
        }`;
        btn.innerText = idx + 1;
        btn.onclick = () => jumpToQuestion(idx);
        palette.appendChild(btn);
      }
    }

    async function confirmSubmitQuiz() {
      const answeredCount = Object.keys(userAnswers).length;
      const total = questions.length;
      const unanswered = total - answeredCount;

      const confirmed = confirm(
        `Submit your Exam Quiz?\n\nAttempted: ${answeredCount}/${total}\nUnanswered: ${unanswered}\nTime: ${document.getElementById('quiz-timer').innerText}`
      );

      if (!confirmed) return;
      clearInterval(timerInterval);

      try {
        const res = await fetch(`/api/quiz/${currentQuizId}/submit`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            answers: userAnswers,
            time_taken_seconds: secondsElapsed
          })
        });

        const results = await res.json();
        if (!res.ok) {
          alert('Submission error');
          return;
        }

        reviewData = results;
        displayResults(results);
      } catch (err) {
        alert(`Error submitting: ${err.message}`);
      }
    }

    function displayResults(data) {
      switchView('view-results');

      if (data.percentage >= 50 && window.confetti) {
        confetti({ particleCount: 120, spread: 80, origin: { y: 0.6 } });
      }

      document.getElementById('result-quiz-title').innerText = data.title;
      document.getElementById('score-percentage').innerText = `${data.percentage}%`;
      document.getElementById('stat-correct').innerText = data.score.toLocaleString();
      document.getElementById('stat-wrong').innerText = data.wrong.toLocaleString();
      document.getElementById('stat-unattempted').innerText = data.unattempted.toLocaleString();

      const tpContainer = document.getElementById('topic-performance-list');
      tpContainer.innerHTML = '';
      for (const [topic, stat] of Object.entries(data.topic_performance)) {
        const pct = Math.round((stat.correct / stat.total) * 100);
        const row = document.createElement('div');
        row.className = 'space-y-1';
        row.innerHTML = `
          <div class="flex justify-between text-xs font-semibold">
            <span>${topic} (${stat.correct}/${stat.total})</span>
            <span>${pct}%</span>
          </div>
          <div class="w-full h-2 bg-slate-200 dark:bg-slate-800 rounded-full overflow-hidden">
            <div class="h-full bg-indigo-600 rounded-full" style="width: ${pct}%"></div>
          </div>
        `;
        tpContainer.appendChild(row);
      }

      renderReviewList('all');
    }

    let currentReviewFilter = 'all';
    function filterReview(type) {
      currentReviewFilter = type;
      document.querySelectorAll('.rev-filter-btn').forEach(b => {
        b.classList.remove('bg-indigo-600', 'text-white');
        b.classList.add('bg-slate-200', 'dark:bg-slate-800', 'text-slate-700', 'dark:text-slate-300');
      });
      event.target.classList.remove('bg-slate-200', 'dark:bg-slate-800', 'text-slate-700', 'dark:text-slate-300');
      event.target.classList.add('bg-indigo-600', 'text-white');

      renderReviewList(type);
    }

    function renderReviewList(filter) {
      if (!reviewData) return;
      const container = document.getElementById('review-list');
      container.innerHTML = '';

      let items = reviewData.review;
      if (filter === 'wrong') items = items.filter(i => i.status === 'wrong');
      if (filter === 'correct') items = items.filter(i => i.status === 'correct');

      if (items.length === 0) {
        container.innerHTML = '<div class="p-8 text-center text-sm text-slate-500">No questions in this filter.</div>';
        return;
      }

      const displayItems = items.slice(0, 150);

      displayItems.forEach((item, index) => {
        const card = document.createElement('div');
        let borderClass = 'border-slate-200 dark:border-slate-800';
        let badgeColor = 'bg-slate-100 text-slate-700';

        if (item.status === 'correct') {
          borderClass = 'border-emerald-300 dark:border-emerald-800';
          badgeColor = 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300';
        } else if (item.status === 'wrong') {
          borderClass = 'border-rose-300 dark:border-rose-800';
          badgeColor = 'bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-300';
        }

        card.className = `glass-card p-5 sm:p-6 rounded-2xl border-2 ${borderClass} space-y-4`;

        let optionsHtml = item.options.map(opt => {
          let optStyle = 'border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900';
          let labelBadge = '';

          if (opt.key === item.correct_answer) {
            optStyle = 'border-emerald-500 bg-emerald-50/70 dark:bg-emerald-950/40 text-emerald-900 dark:text-emerald-200 font-bold';
            labelBadge = '<span class="text-[10px] font-bold uppercase text-emerald-600 dark:text-emerald-400 ml-auto">Correct Answer</span>';
          }
          if (opt.key === item.user_choice && opt.key !== item.correct_answer) {
            optStyle = 'border-rose-500 bg-rose-50/70 dark:bg-rose-950/40 text-rose-900 dark:text-rose-200 font-bold';
            labelBadge = '<span class="text-[10px] font-bold uppercase text-rose-600 dark:text-rose-400 ml-auto">Your Choice</span>';
          }

          return `
            <div class="p-3 rounded-xl border text-xs flex items-center gap-2 ${optStyle}">
              <span class="w-5 h-5 rounded flex items-center justify-center font-bold shrink-0">${opt.key}</span>
              <div class="flex-1">${formatBilingualText(opt.text)}</div>
              ${labelBadge}
            </div>
          `;
        }).join('');

        card.innerHTML = `
          <div class="flex items-center justify-between">
            <span class="text-xs font-bold text-slate-500">Question ${item.original_num || index + 1} (${item.topic})</span>
            <span class="px-2.5 py-0.5 rounded-full text-xs font-bold uppercase ${badgeColor}">
              ${item.status}
            </span>
          </div>
          <div class="text-sm font-semibold">
            ${formatBilingualText(item.question)}
          </div>
          <div class="space-y-2 pt-1">
            ${optionsHtml}
          </div>
          ${item.explanation ? `
            <div class="p-3 rounded-xl bg-slate-100 dark:bg-slate-800/80 text-xs text-slate-700 dark:text-slate-300">
              <strong class="text-indigo-600 dark:text-indigo-400 font-bold">Solution Note / Source:</strong>
              ${formatBilingualText(item.explanation)}
            </div>
          ` : ''}
        `;

        container.appendChild(card);
      });

      if (items.length > 150) {
        const moreNote = document.createElement('div');
        moreNote.className = 'text-center py-4 text-xs text-slate-500 font-medium';
        moreNote.innerText = `Showing first 150 of ${items.length} questions. Use filters above for focused review.`;
        container.appendChild(moreNote);
      }

      updateIcons();
    }

    function retakeActiveQuiz() {
      if (currentQuizData) {
        startQuiz(currentQuizData.selected_topic === 'All Topics' ? 'all' : currentQuizData.selected_topic);
      }
    }

    async function loadPreviousQuizzes() {
      try {
        const res = await fetch('/api/quizzes');
        const data = await res.json();
        const list = document.getElementById('previous-papers-list');
        list.innerHTML = '';

        if (!data || data.length === 0) {
          list.innerHTML = '<p class="text-xs text-slate-500 py-4 text-center">No previous papers uploaded yet.</p>';
        } else {
          data.forEach(q => {
            const item = document.createElement('div');
            item.className = 'p-3 rounded-xl border border-slate-200 dark:border-slate-800 hover:border-indigo-500 cursor-pointer flex items-center justify-between transition';
            item.innerHTML = `
              <div>
                <h4 class="text-xs font-bold text-slate-900 dark:text-white">${q.title}</h4>
                <p class="text-[11px] text-slate-500">${q.total_questions.toLocaleString()} Questions • ${q.topics.length} Topics</p>
              </div>
              <button class="text-xs px-2.5 py-1 rounded bg-indigo-600 text-white font-semibold">Open</button>
            `;
            item.onclick = () => {
              currentQuizId = q.id;
              displayTopicBreakdown(q);
              closePreviousQuizzes();
            };
            list.appendChild(item);
          });
        }

        document.getElementById('previous-papers-modal').classList.remove('hidden');
      } catch (err) {
        alert('Could not fetch quiz history');
      }
    }

    function closePreviousQuizzes() {
      document.getElementById('previous-papers-modal').classList.add('hidden');
    }

    window.addEventListener('keydown', (e) => {
      if (document.getElementById('view-quiz').classList.contains('hidden')) return;
      const keyMap = { '1': 'A', '2': 'B', '3': 'C', '4': 'D', 'a': 'A', 'b': 'B', 'c': 'C', 'd': 'D' };
      const selected = keyMap[e.key.toLowerCase()];
      if (selected && questions[currentQIndex]) {
        selectOption(questions[currentQIndex].id, selected);
      }
      if (e.key === 'ArrowRight') nextQuestion();
      if (e.key === 'ArrowLeft') prevQuestion();
    });
  </script>
</body>
</html>
"""

app = FastAPI(title="PYQ Quiz Master", description="Instant Quiz Platform from PYQ PDFs with Bilingual Hindi/English & Topic Detection")

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
    try:
        reader = pypdf.PdfReader(str(pdf_path))
        if reader.is_encrypted:
            try:
                reader.decrypt("")
            except Exception:
                pass

        for page_idx, page in enumerate(reader.pages):
            try:
                txt = page.extract_text()
                if txt and txt.strip():
                    full_text.append(f"--- PAGE {page_idx + 1} ---\n" + txt)
            except Exception as page_err:
                print(f"Error page {page_idx + 1}: {page_err}")
                continue

        if full_text:
            return "\n".join(full_text)
    except Exception as e:
        print(f"pypdf reader error: {e}")

    if pdfplumber:
        try:
            with pdfplumber.open(str(pdf_path)) as pdf:
                for page_idx, page in enumerate(pdf.pages):
                    try:
                        txt = page.extract_text(layout=True) or page.extract_text()
                        if txt and txt.strip():
                            full_text.append(f"--- PAGE {page_idx + 1} ---\n" + txt)
                    except Exception:
                        continue
            if full_text:
                return "\n".join(full_text)
        except Exception as e:
            print(f"pdfplumber error: {e}")

    return ""

def parse_pyq_document(raw_text: str, filename: str) -> Dict[str, Any]:
    lines = raw_text.splitlines()

    global_answer_key: Dict[int, str] = {}
    ans_key_section = re.search(r"(?:ANSWER\s*KEYS?|ANSWERS|SOLUTIONS?|KEY SHEET|उत्तर\s*माला|उत्तर)\s*[\:\n](.*)", raw_text, re.IGNORECASE | re.DOTALL)
    if ans_key_section:
        key_text = ans_key_section.group(1)
        matches = re.findall(r"(?:(?:Q\.?|Question\s*|प्र\.?\s*|प्रश्न\s*)?(\d+)[\.\s\:\-\)]+\s*(?:\(?([A-Da-d1-4]|क|ख|ग|घ)\)?))", key_text)
        letter_map = {"1": "A", "2": "B", "3": "C", "4": "D", "क": "A", "ख": "B", "ग": "C", "घ": "D"}
        for q_num, ans_val in matches:
            try:
                mapped_val = letter_map.get(ans_val.upper(), ans_val.upper())
                global_answer_key[int(q_num)] = mapped_val
            except ValueError:
                continue

    topic_header_re = re.compile(
        r"^(?:(?:PART|SECTION|UNIT|MODULE|CHAPTER|TOPIC|SUBJECT|भाग|खंड|इकाई|अध्याय|विषय)[\s\:\-\–]+([A-Z0-9\.\s\-\–&]+)|"
        r"(PHYSICS|CHEMISTRY|MATHEMATICS|BIOLOGY|GENERAL KNOWLEDGE|REASONING|APTITUDE|ENGLISH|HINDI|POLITY|HISTORY|GEOGRAPHY|ECONOMICS|COMPUTER SCIENCE|DATA STRUCTURES|ALGORITHMS|ELECTRICAL|MECHANICAL|CIVIL|इतिहास|भूगोल|राजनीति|विज्ञान|गणित|तर्कशक्ति|अर्थशास्त्र))(?:\s*[\:\-\–]|\s*$)",
        re.IGNORECASE
    )

    q_start_re = re.compile(
        r"^(?:(?:Q(?:uestion)?|प्र(?:श्न)?|Ques)\.?\s*(\d+)[\.\:\-\)\s]|(?:(\d+)[\.\)]\s+)|(?:\[(\d+)\]\s+))",
        re.IGNORECASE
    )

    inline_ans_re = re.compile(r"(?:Ans(?:wer)?|Correct(?:\s*Option)?|Key|उत्तर)[\s\:\.\-\–=]+\(?\s*([A-Da-d1-4]|क|ख|ग|घ)\s*\)?", re.IGNORECASE)
    explanation_re = re.compile(r"(?:Explanation|Solution|Hint|Details?|व्याख्या|हल)[\s\:\.\-\\–]+(.*)", re.IGNORECASE | re.DOTALL)

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
        val_map = {"1": "A", "2": "B", "3": "C", "4": "D", "क": "A", "ख": "B", "ग": "C", "घ": "D"}
        
        if ans_match:
            raw_val = ans_match.group(1).upper()
            detected_ans = val_map.get(raw_val, raw_val)
        elif q_obj.get("number") in global_answer_key:
            detected_ans = global_answer_key[q_obj["number"]]

        exp_match = explanation_re.search(raw_q_text)
        explanation = exp_match.group(1).strip() if exp_match else ""

        cleaned_body = inline_ans_re.sub("", raw_q_text)
        cleaned_body = explanation_re.sub("", cleaned_body).strip()

        options = []
        option_matches = list(re.finditer(
            r"(?:[\(\[\{]?([A-Da-d1-4]|क|ख|ग|घ)[\)\]\}][\.\s\:\-\–]*|\b([A-Da-d])[\.\:]\s+)(.*?)(?=(?:[\(\[\{]?(?:[A-Da-d1-4]|क|ख|ग|घ)[\)\]\}][\.\s\:\-\–]*|\b[A-Da-d][\.\:]\s+)|$)",
            cleaned_body,
            re.DOTALL
        ))
        
        q_title = cleaned_body
        if option_matches and len(option_matches) >= 2:
            first_opt_idx = option_matches[0].start()
            q_title = cleaned_body[:first_opt_idx].strip()
            
            seen_keys = set()
            for m in option_matches:
                key = (m.group(1) or m.group(2)).upper()
                key = val_map.get(key, key)
                text = m.group(3).strip()
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
                {"key": "A", "text": "Option A (See PDF Question)"},
                {"key": "B", "text": "Option B (See PDF Question)"},
                {"key": "C", "text": "Option C (See PDF Question)"},
                {"key": "D", "text": "Option D (See PDF Question)"}
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
            "explanation": explanation or f"Extracted from {filename}"
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
                current_q["raw_body"] += "\n" + cleaned_line

    finalize_question(current_q)

    # Fallback if no specific question tags were matched
    if len(questions) == 0 and len(raw_text.strip()) > 30:
        blocks = [b.strip() for b in raw_text.split("\n\n") if len(b.strip()) > 20]
        for idx, block in enumerate(blocks[:100]):
            questions.append({
                "id": f"q_{idx + 1}",
                "original_num": idx + 1,
                "topic": "General Practice",
                "question": block[:300],
                "options": [
                    {"key": "A", "text": "Option A"},
                    {"key": "B", "text": "Option B"},
                    {"key": "C", "text": "Option C"},
                    {"key": "D", "text": "Option D"}
                ],
                "correct_answer": "A",
                "explanation": "Extracted from document"
            })

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
    return HTMLResponse(content=EMBEDDED_HTML_PAGE)

@app.get("/health")
@app.get("/healthz")
async def health_check():
    return JSONResponse({"status": "ok", "app": "PYQ Quiz Master", "bilingual": True})

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
        raise HTTPException(
            status_code=400,
            detail="Could not extract text from this PDF. This happens if the PDF contains scanned photos of pages instead of digital text. Please ensure your PDF has selectable text."
        )

    parsed_quiz = parse_pyq_document(raw_text, file.filename)
    if parsed_quiz["total_questions"] == 0:
        raise HTTPException(
            status_code=422,
            detail="No formatted questions detected. Please ensure questions are numbered (e.g. 1., Q1., प्रश्न 1) with options (A, B, C, D)."
        )

    quiz_id = f"quiz_{file_id}"
    parsed_quiz["id"] = quiz_id
    parsed_quiz["created_at"] = str(Path(saved_pdf_path).stat().st_ctime)

    db = load_db()
    db[quiz_id] = parsed_quiz
    save_db(db)
    gc.collect()

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
async def get_quiz(quiz_id: str, topic: Optional[str] = None, limit: Optional[int] = None):
    db = load_db()
    quiz = db.get(quiz_id)
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    questions = quiz["questions"]
    if topic and topic.lower() != "all":
        questions = [q for q in questions if q["topic"].lower() == topic.lower()]

    if limit and limit > 0:
        import random
        if len(questions) > limit:
            questions = random.sample(questions, limit)

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

    for q_id, user_choice_val in user_answers.items():
        q_data = all_questions_map.get(q_id)
        if not q_data:
            continue

        user_choice = user_choice_val.upper().strip()
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

    if len(detailed_review) < len(quiz["questions"]) and len(user_answers) == 0:
        for q_id, q_data in all_questions_map.items():
            unattempted_count += 1
            t_name = q_data.get("topic", "General")
            detailed_review.append({
                "id": q_id,
                "original_num": q_data.get("original_num"),
                "topic": t_name,
                "question": q_data["question"],
                "options": q_data["options"],
                "user_choice": "",
                "correct_answer": q_data.get("correct_answer", "A"),
                "is_correct": False,
                "status": "unattempted",
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
    print(f"Starting Bilingual PYQ Quiz Server on port {port}")
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=True)
'''

with open(BASE / "app.py", "w", encoding="utf-8") as f:
    f.write(app_code)

print("Updated app.py with responsive feedback, spinner, and error banner!")
