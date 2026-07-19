const app = document.getElementById('app');

const state = {
  screen: 'start',
  exams: {},
  selectedExamId: null,
  currentIndex: 0,
  selectedByQuestion: {},
  explanationOpenByQuestion: {},
  revealedByQuestion: {},
  result: null,
  loading: false,
  error: ''
};

const examIds = ['A', 'B', 'C', 'D'];

function loadStateForExam(examId) {
  state.selectedExamId = examId;
  state.currentIndex = 0;
  state.selectedByQuestion = {};
  state.explanationOpenByQuestion = {};
  state.revealedByQuestion = {};
  state.result = null;
}

async function ensureExamLoaded(examId) {
  if (state.exams[examId]) {
    return state.exams[examId];
  }

  const response = await fetch(`data/exam_${examId}.json`, { cache: 'no-cache' });
  if (!response.ok) {
    throw new Error(`Cannot load exam ${examId}`);
  }

  const json = await response.json();
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
  const key = String(question.id);
  const selected = selectedSet(key);

  if (isQuestionMulti(question)) {
    if (selected.has(optionId)) {
      selected.delete(optionId);
    } else {
      selected.add(optionId);
    }
  } else {
    selected.clear();
    selected.add(optionId);
  }

  state.selectedByQuestion[key] = [...selected];
  state.revealedByQuestion[key] = true;
  if (state.explanationOpenByQuestion[key] === undefined) {
    state.explanationOpenByQuestion[key] = false;
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
    const selected = new Set(state.selectedByQuestion[String(q.id)] || []);
    if (selected.size === 0) {
      unanswered += 1;
      continue;
    }

    const expected = new Set(q.correctOptions);
    if (isSameSet(selected, expected)) {
      correct += 1;
    } else {
      incorrect += 1;
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
    const sel = state.selectedByQuestion[String(q.id)] || [];
    if (sel.length > 0) {
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
  return `
    <section class="screen">
      <h2 class="section-title">Choose a test</h2>
      <div class="test-list">
        ${examIds
          .map((id) => `<button class="btn" data-action="start-exam" data-exam="${id}">Test ${id}</button>`)
          .join('')}
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

  const qid = String(question.id);
  const selected = selectedSet(qid);
  const correct = new Set(question.correctOptions);
  const revealed = Boolean(state.revealedByQuestion[qid]);
  const explanationOpen = Boolean(state.explanationOpenByQuestion[qid]);
  const answered = answeredCount();
  const progress = exam.questions.length > 0 ? (answered / exam.questions.length) * 100 : 0;

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

function renderError() {
  return `
    <section class="screen center">
      <p class="error">${escapeHtml(state.error || 'Unexpected error')}</p>
      <button class="btn" data-action="back-home">Back</button>
    </section>
  `;
}

function render() {
  if (state.loading) {
    app.innerHTML = renderLoading();
    return;
  }

  if (state.error) {
    app.innerHTML = renderError();
    return;
  }

  if (state.screen === 'start') {
    app.innerHTML = renderStart();
  } else if (state.screen === 'selection') {
    app.innerHTML = renderSelection();
  } else if (state.screen === 'test') {
    app.innerHTML = renderTest();
  } else if (state.screen === 'result') {
    app.innerHTML = renderResult();
  }
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
    state.screen = 'start';
    state.error = '';
    render();
    return;
  }

  if (action === 'start-exam') {
    const examId = target.dataset.exam;
    state.loading = true;
    state.error = '';
    render();

    try {
      await ensureExamLoaded(examId);
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
    const key = String(question.id);
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
