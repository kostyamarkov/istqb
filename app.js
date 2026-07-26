const app = document.getElementById('app');
const COMBO_EXAM_ID = 'COMBO';
const BASE_EXAM_IDS = ['A', 'B', 'C', 'D'];
const EXAM_SELECTION_IDS = ['A', 'B', 'C', 'D', 'ADV1'];
const COMBO_COOKIE_NAME = 'istqb_combo_wrong_questions';
const COMBO_COOKIE_MAX_AGE = 60 * 60 * 24 * 365;
const EXAM_FILE_MAP = {
  A: 'data/exam_A.json',
  B: 'data/exam_B.json',
  C: 'data/exam_C.json',
  D: 'data/exam_D.json',
  ADV1: 'data/exam_advanced_1.json'
};
const EXAM_LABEL_MAP = {
  A: 'Test A',
  B: 'Test B',
  C: 'Test C',
  D: 'Test D',
  ADV1: 'Exam Advanced 1'
};

const state = {
  screen: 'start',
  exams: {},
  selectedExamId: null,
  currentIndex: 0,
  selectedByQuestion: {},
  explanationOpenByQuestion: {},
  revealedByQuestion: {},
  result: null,
  pendingComboSyncExamId: null,
  loading: false,
  error: '',
  imageModalSrc: '',
  imageModalAlt: ''
};

function questionStateKey(question) {
  return String(question.uid || question.id);
}

function questionComboKey(question) {
  return `${question.sourceExamId || state.selectedExamId}:${question.id}`;
}

function normalizeExam(exam, sourceExamId) {
  return {
    ...exam,
    sourceExamId,
    questions: exam.questions.map((q) => ({
      ...q,
      sourceExamId,
      uid: `${sourceExamId}-${q.id}`
    }))
  };
}

function readComboKeys() {
  const cookies = document.cookie ? document.cookie.split('; ') : [];
  const item = cookies.find((c) => c.startsWith(`${COMBO_COOKIE_NAME}=`));
  if (!item) {
    return [];
  }

  const raw = item.slice(COMBO_COOKIE_NAME.length + 1);
  try {
    const parsed = JSON.parse(decodeURIComponent(raw));
    if (Array.isArray(parsed)) {
      return parsed.filter((v) => typeof v === 'string');
    }
  } catch (_err) {
  }
  return [];
}

function writeComboKeys(keys) {
  const encoded = encodeURIComponent(JSON.stringify([...new Set(keys)]));
  document.cookie = `${COMBO_COOKIE_NAME}=${encoded}; path=/; max-age=${COMBO_COOKIE_MAX_AGE}; SameSite=Lax`;
}

async function buildComboExam() {
  const comboKeys = readComboKeys();
  if (comboKeys.length === 0) {
    return {
      examId: COMBO_EXAM_ID,
      title: 'Combo-test',
      sourceExamId: COMBO_EXAM_ID,
      questionCount: 0,
      questions: []
    };
  }

  for (const baseExamId of BASE_EXAM_IDS) {
    await ensureExamLoaded(baseExamId);
  }

  const questionByKey = new Map();
  for (const baseExamId of BASE_EXAM_IDS) {
    const exam = state.exams[baseExamId];
    for (const question of exam.questions) {
      questionByKey.set(questionComboKey(question), question);
    }
  }

  const comboQuestions = [];
  for (const key of comboKeys) {
    const q = questionByKey.get(key);
    if (q) {
      comboQuestions.push({ ...q });
    }
  }

  return {
    examId: COMBO_EXAM_ID,
    title: 'Combo-test',
    sourceExamId: COMBO_EXAM_ID,
    questionCount: comboQuestions.length,
    questions: comboQuestions
  };
}

function evaluateQuestion(question) {
  const key = questionStateKey(question);
  const selected = new Set(state.selectedByQuestion[key] || []);

  if (selected.size === 0) {
    return 'unanswered';
  }

  if (isQuestionMulti(question) && !state.revealedByQuestion[key]) {
    return 'unanswered';
  }

  const expected = new Set(question.correctOptions);
  return isSameSet(selected, expected) ? 'correct' : 'incorrect';
}

function syncComboPoolOnBackHome() {
  if (state.pendingComboSyncExamId == null) {
    return;
  }

  const exam = currentExam();
  if (!exam) {
    state.pendingComboSyncExamId = null;
    return;
  }

  const comboSet = new Set(readComboKeys());
  for (const question of exam.questions) {
    const outcome = evaluateQuestion(question);
    const key = questionComboKey(question);

    if (state.pendingComboSyncExamId === COMBO_EXAM_ID) {
      if (outcome === 'correct') {
        comboSet.delete(key);
      }
    } else {
      if (outcome === 'incorrect') {
        comboSet.add(key);
      }
    }
  }

  writeComboKeys([...comboSet]);
  state.pendingComboSyncExamId = null;
}

function loadStateForExam(examId) {
  state.selectedExamId = examId;
  state.currentIndex = 0;
  state.selectedByQuestion = {};
  state.explanationOpenByQuestion = {};
  state.revealedByQuestion = {};
  state.result = null;
  state.pendingComboSyncExamId = null;
}

async function ensureExamLoaded(examId) {
  if (state.exams[examId]) {
    return state.exams[examId];
  }

  const filePath = EXAM_FILE_MAP[examId] || `data/exam_${examId}.json`;
  const response = await fetch(filePath, { cache: 'no-cache' });
  if (!response.ok) {
    throw new Error(`Cannot load exam ${examId}`);
  }

  const json = normalizeExam(await response.json(), examId);
  state.exams[examId] = json;
  return json;
}

function currentExam() {
  return state.exams[state.selectedExamId] || null;
}

function currentQuestion() {
  const exam = currentExam();
  if (!exam) return null;
  return exam.questions[state.currentIndex] || null;
}

function isQuestionMulti(question) {
  return question.correctOptions.length > 1;
}

function selectedSet(questionId) {
  return new Set(state.selectedByQuestion[questionId] || []);
}

function toggleOption(question, optionId) {
  const key = questionStateKey(question);
  const selected = selectedSet(key);

  if (isQuestionMulti(question)) {
    // Multi-select questions are evaluated only after exactly two distinct choices.
    if (state.revealedByQuestion[key]) {
      return;
    }

    if (selected.has(optionId)) {
      return;
    }

    if (selected.size >= 2) {
      return;
    }

    selected.add(optionId);
    state.selectedByQuestion[key] = [...selected];

    if (selected.size === 2) {
      state.revealedByQuestion[key] = true;
      if (state.explanationOpenByQuestion[key] === undefined) {
        state.explanationOpenByQuestion[key] = false;
      }
    }

    return;
  } else {
    selected.clear();
    selected.add(optionId);
    state.selectedByQuestion[key] = [...selected];
    state.revealedByQuestion[key] = true;

    if (state.explanationOpenByQuestion[key] === undefined) {
      state.explanationOpenByQuestion[key] = false;
    }

    return;
  }
}

function isSameSet(a, b) {
  if (a.size !== b.size) return false;
  for (const x of a) {
    if (!b.has(x)) return false;
  }
  return true;
}

function computeResult() {
  const exam = currentExam();
  let correct = 0;
  let incorrect = 0;
  let unanswered = 0;

  for (const q of exam.questions) {
    const outcome = evaluateQuestion(q);
    if (outcome === 'correct') {
      correct += 1;
    } else if (outcome === 'incorrect') {
      incorrect += 1;
    } else {
      unanswered += 1;
    }
  }

  return {
    total: exam.questions.length,
    correct,
    incorrect,
    unanswered
  };
}

function answeredCount() {
  const exam = currentExam();
  if (!exam) return 0;

  let count = 0;
  for (const q of exam.questions) {
    const outcome = evaluateQuestion(q);
    if (outcome === 'correct' || outcome === 'incorrect') {
      count += 1;
    }
  }
  return count;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;');
}

function renderStart() {
  return `
    <section class="screen center">
      <h1 class="title">ISTQB Preparation</h1>
      <p class="subtitle">Simple practice tests</p>
      <button class="btn btn-primary" data-action="open-selection">Start test</button>
      <p class="subtitle" style="max-width: 520px; font-size: 12px;">
        Uses ISTQB sample exam content. See
        <a href="COPYRIGHT_NOTICE.md" target="_blank" rel="noopener">copyright and usage notice</a>.
      </p>
    </section>
  `;
}

function renderSelection() {
  const comboCount = readComboKeys().length;
  return `
    <section class="screen">
      <h2 class="section-title">Choose a test</h2>
      <div class="test-list">
        ${EXAM_SELECTION_IDS
          .map((id) => `<button class="btn" data-action="start-exam" data-exam="${id}">${EXAM_LABEL_MAP[id] || id}</button>`)
          .join('')}
        <button class="btn" data-action="start-exam" data-exam="${COMBO_EXAM_ID}">Combo-test (${comboCount})</button>
      </div>
      <div class="footer-nav">
        <button class="btn" data-action="back-home">Back</button>
      </div>
    </section>
  `;
}

function renderTest() {
  const exam = currentExam();
  const question = currentQuestion();
  if (!exam || !question) {
    return `<section class="screen"><p class="error">Exam data is not available.</p></section>`;
  }

  const qid = questionStateKey(question);
  const selected = selectedSet(qid);
  const correct = new Set(question.correctOptions);
  const revealed = Boolean(state.revealedByQuestion[qid]);
  const explanationOpen = Boolean(state.explanationOpenByQuestion[qid]);
  const answered = answeredCount();
  const progress = exam.questions.length > 0 ? (answered / exam.questions.length) * 100 : 0;
  const media = Array.isArray(question.media) ? question.media : [];

  const options = question.options
    .map((o) => {
      const isSelected = selected.has(o.id);
      const isCorrect = correct.has(o.id);
      const classes = ['option'];

      if (!revealed && isSelected) {
        classes.push('selected');
      }
      if (revealed && isCorrect) {
        classes.push('correct');
      } else if (revealed && isSelected && !isCorrect) {
        classes.push('wrong');
      }

      return `<button class="${classes.join(' ')}" data-action="choose-option" data-option="${o.id}">
        <strong>${escapeHtml(o.id.toUpperCase())}.</strong> ${escapeHtml(o.text)}
      </button>`;
    })
    .join('');

  const mediaMarkup = media
    .map((m, idx) => {
      if (!m || m.type !== 'image' || !m.src) {
        return '';
      }
      const alt = m.alt || `Question ${question.id} visual`;
      return `<button class="question-media" data-action="open-image" data-src="${escapeHtml(m.src)}" data-alt="${escapeHtml(alt)}" data-media-index="${idx}">
        <img src="${escapeHtml(m.src)}" alt="${escapeHtml(alt)}" loading="lazy" />
        <span>Tap to enlarge</span>
      </button>`;
    })
    .join('');

  return `
    <section class="screen">
      <div class="progress-block">
        <div class="progress-head">
          <span>Progress</span>
          <span>Answered ${answered}/${exam.questions.length}</span>
        </div>
        <div class="progress-track"><div class="progress-fill" style="width:${progress}%;"></div></div>
      </div>

      <div class="question-meta">Question ${state.currentIndex + 1} of ${exam.questions.length}</div>
      <h3 class="question-text">${escapeHtml(question.text)}</h3>
      ${mediaMarkup}
      ${isQuestionMulti(question) ? '<div class="hint">Select all correct options</div>' : ''}
      <div class="options">${options}</div>

      ${
        revealed
          ? `<div class="explanation">
              <button data-action="toggle-explanation">Explanation ${explanationOpen ? '▲' : '▼'}</button>
              ${explanationOpen ? `<div class="content">${escapeHtml(question.explanation)}</div>` : ''}
             </div>`
          : ''
      }

      <div class="footer-nav">
        <div class="row">
          <button class="btn" data-action="prev-question" ${state.currentIndex === 0 ? 'disabled' : ''}>Previous</button>
          <button class="btn" data-action="next-question" ${state.currentIndex === exam.questions.length - 1 ? 'disabled' : ''}>Next</button>
          <button class="btn btn-primary" data-action="finish-test">Finish</button>
        </div>
      </div>
    </section>
  `;
}

function renderResult() {
  const result = state.result;
  return `
    <section class="screen center">
      <h2 class="section-title">Test completed</h2>
      <div class="result-list">
        <div class="result-item"><span>Correct</span><strong class="green">${result.correct}</strong></div>
        <div class="result-item"><span>Incorrect</span><strong class="red">${result.incorrect}</strong></div>
        <div class="result-item"><span>Unanswered</span><strong class="gray">${result.unanswered}</strong></div>
        <div class="result-item"><span>Total</span><strong>${result.total}</strong></div>
      </div>
      <button class="btn btn-primary" data-action="restart">Back to Home</button>
    </section>
  `;
}

function renderLoading() {
  return `<section class="screen center"><p class="subtitle">Loading...</p></section>`;
}

function renderImageModal() {
  if (!state.imageModalSrc) {
    return '';
  }

  return `<div class="image-modal" data-action="close-image">
    <div class="image-modal-content" role="dialog" aria-modal="true" aria-label="Question image preview">
      <button class="image-modal-close" data-action="close-image">Close</button>
      <img src="${escapeHtml(state.imageModalSrc)}" alt="${escapeHtml(state.imageModalAlt || 'Question image')}" />
    </div>
  </div>`;
}

function renderError() {
  return `
    <section class="screen center">
      <p class="error">${escapeHtml(state.error || 'Unexpected error')}</p>
      <button class="btn" data-action="back-home">Back</button>
    </section>
  `;
}

function render() {
  let markup = '';

  if (state.loading) {
    markup = renderLoading();
  } else if (state.error) {
    markup = renderError();
  } else if (state.screen === 'start') {
    markup = renderStart();
  } else if (state.screen === 'selection') {
    markup = renderSelection();
  } else if (state.screen === 'test') {
    markup = renderTest();
  } else if (state.screen === 'result') {
    markup = renderResult();
  }

  app.innerHTML = `${markup}${renderImageModal()}`;
}

app.addEventListener('click', async (event) => {
  const target = event.target.closest('[data-action]');
  if (!target) return;

  const action = target.dataset.action;

  if (action === 'open-selection') {
    state.screen = 'selection';
    state.error = '';
    render();
    return;
  }

  if (action === 'back-home' || action === 'restart') {
    if (state.screen === 'result') {
      syncComboPoolOnBackHome();
    }
    state.screen = 'start';
    state.error = '';
    render();
    return;
  }

  if (action === 'open-image') {
    state.imageModalSrc = target.dataset.src || '';
    state.imageModalAlt = target.dataset.alt || '';
    render();
    return;
  }

  if (action === 'close-image') {
    state.imageModalSrc = '';
    state.imageModalAlt = '';
    render();
    return;
  }

  if (action === 'start-exam') {
    const examId = target.dataset.exam;
    state.loading = true;
    state.error = '';
    render();

    try {
      if (examId === COMBO_EXAM_ID) {
        const comboExam = await buildComboExam();
        state.exams[COMBO_EXAM_ID] = comboExam;
      } else {
        await ensureExamLoaded(examId);
      }
      loadStateForExam(examId);
      state.screen = 'test';
    } catch (err) {
      state.error = err.message || 'Failed to load exam data';
      state.screen = 'selection';
    } finally {
      state.loading = false;
      render();
    }
    return;
  }

  if (state.screen !== 'test') {
    return;
  }

  const exam = currentExam();
  const question = currentQuestion();

  if (action === 'choose-option') {
    toggleOption(question, target.dataset.option);
    render();
    return;
  }

  if (action === 'toggle-explanation') {
    const key = questionStateKey(question);
    state.explanationOpenByQuestion[key] = !state.explanationOpenByQuestion[key];
    render();
    return;
  }

  if (action === 'prev-question' && state.currentIndex > 0) {
    state.currentIndex -= 1;
    render();
    return;
  }

  if (action === 'next-question' && state.currentIndex < exam.questions.length - 1) {
    state.currentIndex += 1;
    render();
    return;
  }

  if (action === 'finish-test') {
    state.result = computeResult();
    state.pendingComboSyncExamId = state.selectedExamId;
    state.screen = 'result';
    render();
  }
});

async function bootstrap() {
  if ('serviceWorker' in navigator) {
    try {
      await navigator.serviceWorker.register('./sw.js');
    } catch (_err) {
    }
  }

  render();
}

bootstrap();
