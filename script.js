'use strict';

const MIN_PID = 1;
const MAX_PID = 900;
const QUESTIONS = [
  {
    id: 1,
    text: 'ex) a',
    correct: '1' //ここで実際の問題文と正解を入れる
  },
  {
    id: 2,
    text: 'ex) b',
    correct: '2'
  },
  {
    id: 3,
    text: 'ex) c',
    correct: '3'
  },
  {
    id: 4,
    text: 'ex) d',
    correct: '4'
  }
];

const CHOICE_POOL = [
  '1', //ここで実際の選択肢を入れる
  '2',
  '3',
  '4',
  '5',
  '6',
  '7',
  '8',
  '9',
  '10',
  '11',
  '12',
  '13',
  '14',
  '15',
  '16',
  '17',
  '18',
  '19',
  '20'
];

let participantId = null;
let learnType = null;
let answerType = null;
let condition = null;
let quiz = [];
let results = [];
let testStart = null;
let choiceHandlersBound = false;
let pidIsComposing = false;

let pidInputArea = null;
let pidInput = null;
let pidSubmit = null;
let startButton = null;
let quizDiv = null;
let finishButton = null;

function normalizePid(value) {
  if (typeof value !== 'string') {
    return '';
  }

  return value
    .replace(/[０-９]/g, (ch) => String.fromCharCode(ch.charCodeAt(0) - 0xFEE0))
    .trim();
}

function normalizePidInput(input) {
  if (!input || !input.value) {
    return;
  }

  const normalized = normalizePid(input.value);
  if (normalized === input.value) {
    return;
  }

  const start = input.selectionStart;
  const end = input.selectionEnd;
  input.value = normalized;
  if (start !== null && end !== null) {
    input.setSelectionRange(start, end);
  }
}

function isValidPid(value) {
  const normalized = normalizePid(value);
  const number = Number(normalized);
  return normalized !== '' && Number.isFinite(number) && number >= MIN_PID && number <= MAX_PID;
}

function getConditionFormID(pid) { //条件を決める
  const id = Number(pid);
  if (id >= 1 && id <= 50) return { learnType: 'analog', answerType: 'analog' }; //1~100は試験用のpid
  if (id >= 51 && id <= 100) return { learnType: 'digital', answerType: 'digital' };
  if (id >= 101 && id <= 200) return { learnType: 'analog', answerType: 'analog' }; //ここからが本番用
  if (id >= 201 && id <= 300) return { learnType: 'digital', answerType: 'digital' };
  return null;
}

function setParticipantFromPid(pid) {
  const normalized = normalizePid(pid);
  const conditionInfo = getConditionFormID(normalized);
  if (!conditionInfo) {
    alert('無効な参加者IDです。1〜900の数字を指定してください。');
    showState('pid');
    return false;
  }

  participantId = normalized;
  learnType = conditionInfo.learnType;
  answerType = conditionInfo.answerType;
  condition = `${conditionInfo.learnType}_learn_${conditionInfo.answerType}_answer`;
  return true;
}

function setVisible(element, visible) {
  if (!element) {
    return;
  }
  element.classList.toggle('hidden', !visible);
}

function showState(stateName) {
  setVisible(pidInputArea, stateName === 'pid');
  setVisible(startButton, stateName === 'start');
  setVisible(quizDiv, stateName === 'quiz');
  setVisible(finishButton, stateName === 'quiz' || stateName === 'finish');

  if (stateName === 'pid') {
    pidInput?.focus();
  }
}

function submitPid(value) {
  if (!isValidPid(value)) {
    alert('有効な参加者IDを入力してください（1〜900の数字）。');
    return;
  }

  const normalized = normalizePid(value);
  window.location.assign(`?pid=${encodeURIComponent(normalized)}`);
}

function bindPidSubmit() {
  if (!pidInput || !pidSubmit) {
    console.warn('PID input or submit button was not found.');
    return;
  }

  pidInput.addEventListener('compositionstart', () => {
    pidIsComposing = true;
  });

  pidInput.addEventListener('compositionend', () => {
    pidIsComposing = false;
    normalizePidInput(pidInput);
  });

  pidInput.addEventListener('input', () => {
    if (!pidIsComposing) {
      normalizePidInput(pidInput);
    }
  });

  pidInput.addEventListener('keydown', (event) => {
    if (event.key !== 'Enter') {
      return;
    }
    event.preventDefault();
    submitPid(pidInput.value);
  });

  pidSubmit.addEventListener('click', (event) => {
    event.preventDefault();
    submitPid(pidInput.value);
  });
}

function shuffle(array) {
  const copy = [...array];
  for (let i = copy.length - 1; i > 0; i -= 1) {
    const j = Math.floor(Math.random() * (i + 1));
    [copy[i], copy[j]] = [copy[j], copy[i]];
  }
  return copy;
}

function generateChoices(correctLabel) {
  const choices = [correctLabel];
  const pool = CHOICE_POOL.filter((item) => item !== correctLabel);

  while (choices.length < 4) {
    const pick = pool[Math.floor(Math.random() * pool.length)];
    if (!choices.includes(pick)) {
      choices.push(pick);
    }
  }

  return shuffle(choices);
}

function initializeQuiz() {
  quiz = QUESTIONS.map((question) => ({
    id: question.id,
    text: question.text,
    correct: question.correct,
    choices: generateChoices(question.correct)
  }));
}

function renderQuestions() {
  if (!quizDiv) {
    return;
  }

  quizDiv.innerHTML = '';
  quiz.forEach((question, index) => {
    startTimes[question.id] = Date.now();

    const questionBlock = document.createElement('div');
    questionBlock.className = 'question-block';
    questionBlock.innerHTML = `
      <h3>問題 ${index + 1}: ${question.text}</h3>
      <div class="choices-row">
        ${question.choices
          .map(
            (choice) => `
            <div class="choicebox" data-qid="${question.id}" data-value="${choice}" tabindex="0" role="button" aria-pressed="false">
              <span class="checkFrame"></span>
              <span class="choiceText">${choice}</span>
            </div>`
          )
          .join('')}
      </div>
    `;

    quizDiv.appendChild(questionBlock);
  });

  setupChoiceHandlers();
}

function handleChoiceClick(button) {
  if (button.classList.contains('disabled')) {
    return;
  }

  const qid = Number(button.dataset.qid);
  const value = button.dataset.value;
  const question = quiz.find((item) => item.id === qid);
  const elapsedSeconds = (Date.now() - startTimes[qid]) / 1000;
  const isCorrect = question ? value === question.correct : false;

  results.push({
    id: qid,
    text: question ? question.text : '',
    correctAnswer: question ? question.correct : '',
    participantAnswer: value,
    correct: isCorrect,
    timeSec: elapsedSeconds
  });

  const questionBlock = button.closest('.question-block');
  if (!questionBlock) {
    return;
  }

  questionBlock.querySelectorAll('.choicebox').forEach((choiceItem) => {
    choiceItem.style.pointerEvents = 'none';
    choiceItem.classList.add('disabled');
    choiceItem.setAttribute('aria-pressed', 'true');
  });
}

function setupChoiceHandlers() {
  if (!quizDiv || choiceHandlersBound) {
    return;
  }

  choiceHandlersBound = true;

  quizDiv.addEventListener('click', (event) => {
    const button = event.target.closest ? event.target.closest('.choicebox') : null;
    if (!button) {
      return;
    }
    handleChoiceClick(button);
  });

  quizDiv.addEventListener('keydown', (event) => {
    if (event.key !== 'Enter' && event.key !== ' ') {
      return;
    }

    const button = event.target.closest ? event.target.closest('.choicebox') : null;
    if (!button) {
      return;
    }

    event.preventDefault();
    handleChoiceClick(button);
  });
}

function finishSession() {
  if (!participantId || !learnType || !answerType) {
    alert('参加者情報が不足しています。ページをリロードしてください。');
    return;
  }

  const payload = {
    participantId,
    learnType,
    answerType,
    condition,
    totalTimeSec: (Date.now() - testStart) / 1000,
    totalCorrect: results.filter((item) => item.correct).length,
    questions: results,
    timestamp: new Date().toISOString()
  };

  fetch('/submit', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(payload)
  })
    .then((response) => {
      if (!response.ok) {
        throw new Error(`送信に失敗しました: ${response.status}`);
      }
      return response.json();
    })
    .then(() => {
      window.location.assign('finish.html');
    })
    .catch((error) => {
      console.error(`送信エラー: ${error.message || error}`);
    });
}

function parsePidFromUrl() {
  return normalizePid(new URLSearchParams(window.location.search).get('pid') || '');
}

function initPage() {
  pidInputArea = document.getElementById('pid-input-area');
  pidInput = document.getElementById('pid');
  pidSubmit = document.getElementById('pid-submit');
  startButton = document.getElementById('start');
  quizDiv = document.getElementById('quiz');
  finishButton = document.getElementById('finish');

  const hasPidFlow = Boolean(pidInputArea || pidInput || pidSubmit);

  if (hasPidFlow) {
    bindPidSubmit();
  }

  if (startButton) {
    startButton.addEventListener('click', () => {
      if (!answerType || !participantId || !learnType) {
        if (hasPidFlow) {
          alert('参加者IDを先に入力してください。');
          return;
        }

        if (!setParticipantFromPid('1')) {
          alert('参加者情報の初期化に失敗しました。');
          return;
        }
      }

      results = [];
      testStart = Date.now();
      if (!quiz.length) {
        initializeQuiz();
      }

      if (answerType === 'analog') {
        showState('finish');
        return;
      }

      showState('quiz');
      renderQuestions();
    });
  }

  if (finishButton) {
    finishButton.addEventListener('click', finishSession);
  }

  if (hasPidFlow) {
    const pidFromUrl = parsePidFromUrl();
    if (pidFromUrl && setParticipantFromPid(pidFromUrl)) {
      showState('start');
    } else {
      showState('pid');
    }
    return;
  }

  showState('start');
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initPage);
} else {
  initPage();
}
