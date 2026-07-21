let participantId = localStorage.getItem("participantId") || null;
let learnType = null; // 修正: undefined 参照を防ぐための初期値
let answerType = null; // 修正: undefined 参照を防ぐための初期値
let condition = null; // 修正: グローバル条件も初期化

function getConditionFormID(pid) { //条件を決める
  const id = Number(pid);

  if (id >= 1 && id <= 25) //1~100は試験用のpid
    return { learnType: "analog", answerType: "analog" };
  else if (id >= 26 && id <= 50)
    return { learnType: "analog", answerType: "digital" };
  else if (id >= 51 && id <= 75)
    return { learnType: "digital", answerType: "analog" };
  else if (id >= 76 && id <= 100)
    return { learnType: "digital", answerType: "digital" };
  else if (id >= 101 && id <= 300) //ここからが本番用
    return { learnType: "analog", answerType: "analog" };
  else if (id >= 301 && id <= 500) 
    return { learnType: "analog", answerType: "digital" };
  else if (id >= 501 && id <= 700) 
    return { learnType: "digital", answerType: "analog" };
  else if (id >= 701 && id <= 900) 
    return { learnType: "digital", answerType: "digital" };
  return null;
}

const pidInputArea = document.getElementById("pid-input-area");
const startButton = document.getElementById("start");
const finishButton = document.getElementById("finish");
const quizDiv = document.getElementById("quiz");
let pidIsComposing = false; // 修正: IME 変換中の input イベントを制御するフラグ

function showPidInputState() {
  pidInputArea.style.display = "block";
  startButton.style.display = "none";
  quizDiv.style.display = "none";
  finishButton.style.display = "none";
}

function showStartState() {
  pidInputArea.style.display = "none";
  startButton.style.display = "block";
  quizDiv.style.display = "none";
  finishButton.style.display = "none";
}

function showQuizState() {
  pidInputArea.style.display = "none";
  startButton.style.display = "none";
  quizDiv.style.display = "block";
  finishButton.style.display = "block";
}

function showAnalogState() {
  pidInputArea.style.display = "none";
  startButton.style.display = "none";
  quizDiv.style.display = "none";
  finishButton.style.display = "block";
}

function normalizePid(pid) {
  if (typeof pid !== 'string') return '';
  return pid
    .replace(/[０-９]/g, (ch) => String.fromCharCode(ch.charCodeAt(0) - 0xFEE0))
    .trim();
} // 修正: 全角数字を半角数字へ変換する

function normalizePidInput(input) {
  if (!input || !input.value) return;
  const normalized = normalizePid(input.value);
  if (normalized !== input.value) {
    const start = input.selectionStart;
    const end = input.selectionEnd;
    input.value = normalized;
    if (start !== null && end !== null) {
      input.setSelectionRange(start, end);
    }
  }
} // 修正: 入力欄の値を正規化し、カーソル位置を保持する

function setParticipantFromPid(pid) {
  if (!input || !input.value) return;
  const normalized = normalizePid(input.value);
  if (normalized !== input.value) {
    const start = input.selectionStart;
    const end = input.selectionEnd;
    input.value = normalized;
    if (start !== null && end !== null) {
      input.setSelectionRange(start, end);
    }
  }
}

function setParticipantFromPid(pid) {
  pid = normalizePid(pid); // 修正: URL や入力値から受け取った PID を半角化してから判定
  const cond = getConditionFormID(pid);
  if (!cond) {
    alert("無効な参加者IDです。1〜900の数字を指定してください。");
    showPidInputState();
    return false;
  }

  window.participantId = pid;
  window.learnType = cond.learnType;
  window.answerType = cond.answerType;
  window.condition = `${cond.learnType}_learn_${cond.answerType}_answer`;
  return true;
}

console.log("script.js loaded");
window.submitPid = function(event) {
  if (event) {
    event.preventDefault();
  }
  const pidInput = document.getElementById("pid");
  if (!pidInput) {
    alert("参加者ID入力欄が見つかりません。");
    return;
  }

  const pid = normalizePid(pidInput.value); // 修正: submitPid でも全角数字を半角に変換
  pidInput.value = pid;
  if (!pid || isNaN(pid) || Number(pid) < 1 || Number(pid) > 900) {
    alert("有効な参加者IDを入力してください（1〜900の数字）。");
    return;
  }

  console.log("submitPid called", pid); // 追加: クリック時ログ
  try {
    window.location.assign(`?pid=${encodeURIComponent(pid)}`);
  } catch (e) {
    console.error("submitPid location.assign failed, fallback to search set", e);
    window.location.search = `?pid=${encodeURIComponent(pid)}`;
  }
};

console.log("submitPid defined on window", typeof window.submitPid);

const pidFromURL = normalizePid(new URLSearchParams(window.location.search).get("pid") || ""); // 修正: URL パラメータの全角 PID も半角化
if (pidFromURL && setParticipantFromPid(pidFromURL)) {
  showStartState();
} else {
  showPidInputState();
}

function bindPidSubmit() {
  const pidInput = document.getElementById("pid");
  const pidSubmit = document.getElementById("pid-submit");

  if (!pidInput || !pidSubmit) {
    console.warn("bindPidSubmit: pidInput or pidSubmit not found", { pidInput, pidSubmit });
    return;
  }

  // 修正: 古い inline onclick があれば削除して、エラーになる古い submitPid 参照を防止
  if (pidSubmit.hasAttribute("onclick")) {
    pidSubmit.removeAttribute("onclick");
  }

  // 修正: DOM 構築後に送信ボタンのイベントを登録し、デフォルト動作を止めて明示的に遷移する
  console.log("bindPidSubmit: binding pid submit handler");
  pidInput.addEventListener("compositionstart", () => {
    pidIsComposing = true; // 修正: IME 変換開始中は input 正規化を一時停止
  });
  pidInput.addEventListener("compositionend", () => {
    pidIsComposing = false; // 修正: 変換確定後に全角数字を半角化
    normalizePidInput(pidInput);
  });
  pidInput.addEventListener("input", () => {
    if (!pidIsComposing) {
      normalizePidInput(pidInput); // 修正: 変換中でなければリアルタイムで半角化
    }
  });

  pidSubmit.addEventListener("click", (event) => {
    event.preventDefault();
    const pid = normalizePid(pidInput.value); // 修正: 送信時にも全角から半角に変換
    pidInput.value = pid;
    console.log("pidSubmit clicked, pid=", pid); // 追加: クリック時ログ

    if (!pid || isNaN(pid) || Number(pid) < 1 || Number(pid) > 900) {
      alert("有効な参加者IDを入力してください（1〜900の数字）。");
      return;
    }

    // 修正: 通常の location.href に加え、assign を使ったフォールバックを用意
    try {
      window.location.assign(`?pid=${encodeURIComponent(pid)}`);
    } catch (e) {
      // 万一失敗した場合は search を直接書き換えてみる
      console.error("location.assign failed, fallback to search set", e);
      window.location.search = `?pid=${encodeURIComponent(pid)}`;
    }
  });
}

// 修正: body にもフォールバックの click リスナーを追加して、ボタンが直接クリックされた場合でも捕捉する
if (document.body) {
  document.body.addEventListener("click", (event) => {
    const target = event.target;
    if (!target) {
      return;
    }
    const button = target.closest ? target.closest("#pid-submit") : null;
    if (button) {
      console.log("body fallback click caught pid-submit");
      submitPid(event);
    }
  });
} else {
  document.addEventListener("DOMContentLoaded", () => {
    document.body.addEventListener("click", (event) => {
      const target = event.target;
      if (!target) {
        return;
      }
      const button = target.closest ? target.closest("#pid-submit") : null;
      if (button) {
        console.log("body fallback click caught pid-submit after DOMContentLoaded");
        submitPid(event);
      }
    });
  });
}

// 修正: スクリプトが body の末尾で読み込まれる場合、DOMContentLoaded は既に発火している可能性がある。
// そのため、まだ読み込み中ならイベントで登録し、既に読み込み済みなら即時バインドする。
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", bindPidSubmit);
} else {
  bindPidSubmit();
}

const Questions = [
    {
        id: 1,
        text: "ex) a", correct: "1", //ここで実際の問題文と正解を入れる
    },
    {
        id: 2,
        text: "ex) b", correct: "2",
    }, 
    {
      id: 3,
      text: "ex) c", correct: "3",
    },
    {
      id: 4,
      text: "ex) d", correct: "4"
    }
];

const choicePool = [
    "1", //ここで実際の選択肢を入れる
    "2",
    "3",
    "4",
    "5",
    "6",
    "7",
    "8",
    "9",
    "10",
    "11",
    "12",
    "13",
    "14",
    "15",
    "16",
    "17",
    "18",
    "19",
    "20",
];

function shuffle(array) {
  // 修正: shuffle() が未定義だったため、選択肢のランダム化処理を追加
  const copy = [...array];
  for (let i = copy.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [copy[i], copy[j]] = [copy[j], copy[i]];
  }
  return copy;
}

function generateChoices(correctLabel) {
  const choices = [correctLabel]; //正解を入れる
  const incorrectChoices = choicePool.filter(c => c !== correctLabel); //正解以外の選択肢を抽出
  while (choices.length < 4 ){ //選択肢が4つになるまで
    const pick = incorrectChoices[Math.floor(Math.random() * incorrectChoices.length)]; //ランダムに選択肢を選ぶ
    if (!choices.includes(pick)) {
      choices.push(pick);
    }
  }
  return shuffle(choices);
}

// 修正: generateChoices() をpid設定後にしか実行しないよう遅延初期化
let quiz = null;
function initializeQuiz() {
  quiz = Questions.map(q => {
    return {
      id: q.id,
      text: q.text,
      correct: q.correct,
      choices: generateChoices(q.correct)
    };
  });
}

const startTimes = {};

function showQuestions() {
  if (!quiz) {
    // 修正: quizが初期化されていない場合の防止策
    alert("クイズが初期化されていません。ページをリロードしてください。");
    return;
  }
  quizDiv.innerHTML = ""; // 初期化
  quiz.forEach((q, index) => {
    startTimes[q.id] = Date.now(); // 各問題の開始時刻を記録
    const div = document.createElement("div");
    div.className = "question-block";
    const choices = generateChoices(q.correct);
    div.innerHTML = `
      <h3>問題 ${index + 1}: ${q.text}</h3>
      <div class="choices-row">
      ${choices
        .map(
          c => `
          <div class="choicebox" data-qid="${q.id}" data-value="${c}" tabindex="0" role="button" aria-pressed="false">
            <span class="checkFrame"></span>
            <span class="choiceText">${c}</span>
          </div>
      `
        )
        .join("")}
      </div>
    `;

    quizDiv.appendChild(div);
  });
  setupChoiceHandlers();
}


const results = [];
let _choiceHandlersBound = false;

function handleChoiceClick(btn) {
  const qid = Number(btn.dataset.qid);
  const value = btn.dataset.value;
  const end = Date.now();
  const elapsed = (end - startTimes[qid]) / 1000;
  const question = quiz.find(q => q.id === qid);
  const isCorrect = value === question.correct;
  results.push({
    id: qid,
    text: question.text,
    correctAnswer: question.correct,
    participantAnswer: value,
    correct: isCorrect,
    timeSec: elapsed
  });

  const questionBlock = btn.closest(".question-block");
  if (questionBlock) {
    questionBlock.querySelectorAll(".choicebox").forEach(b => {
      b.style.pointerEvents = "none";
      b.classList.add("disabled");
      b.setAttribute("aria-pressed", "true");
    });
  }
}

function setupChoiceHandlers() {
  if (!quizDiv) return;
  if (_choiceHandlersBound) return; // 一度だけバインド
  _choiceHandlersBound = true;

  // イベント委任でクリックを処理（動的要素でも確実に拾える）
  quizDiv.addEventListener("click", (event) => {
    const btn = event.target.closest ? event.target.closest('.choicebox') : null;
    if (!btn) return;
    handleChoiceClick(btn);
  });

  // キーボード操作にも対応（Enter / Space）
  quizDiv.addEventListener("keydown", (event) => {
    if (event.key === "Enter" || event.key === " ") {
      const btn = event.target.closest ? event.target.closest('.choicebox') : null;
      if (!btn) return;
      event.preventDefault();
      handleChoiceClick(btn);
    }
  });
}

let testStart = null;

// クイズ開始イベント
if (startButton) {
  startButton.addEventListener("click", () => {
    if (!window.answerType) {
      alert("回答タイプが設定されていません。参加者IDを確認してください。");
      return;
    }
    if (!window.participantId || !window.learnType) {
      alert("参加者情報が不完全です。ページをリロードして再試行してください。");
      return;
    }
    // 修正: startボタンを押した時点でもinitializeQuiz()を確実に実行し、quizが初期化されていることを保証する
    if (!quiz) {
      initializeQuiz();
    }
    startButton.style.display = "none"; //スタートボタンを消す
    if (window.answerType === "analog") { //アナログ回答の場合；問題を出さない
      quizDiv.style.display = "none"; //クイズを非表示
      finishButton.style.display = "block"; // 回答終了ボタンを表示
      testStart = Date.now(); //テスト開始時刻を記録
    }
    if (window.answerType === "digital") { //デジタル回答の場合；問題を出す
      quizDiv.style.display = "block"; //クイズを表示
      testStart = Date.now(); //テスト開始時刻を記録
      results.length = 0; //結果を初期化
      showQuestions(); //問題を表示
      finishButton.style.display = "block"; // 回答終了ボタンを表示
    }
  });
}

// 回答終了ボタンのイベントリスナー（1回だけ登録）
if (finishButton) {
  finishButton.addEventListener("click", () => {
    const testEnd = Date.now();
    const totalTimeSec = (testEnd - testStart) / 1000;
    const totalCorrect = results.filter(r => r.correct).length;
    const payload = {
      participantId: window.participantId,
      learnType: window.learnType,
      answerType: window.answerType,
      condition: window.condition,
      totalTimeSec: totalTimeSec,
      totalCorrect: totalCorrect,
      questions: results,
      timestamp: new Date().toISOString()
    };

    fetch("https://prod-h9qw.onrender.com/submit", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(payload)
    })
    .then(res => {
      if (!res.ok) {
        throw new Error(`送信に失敗しました: ${res.status}`);
      }
      return res.json();
    })
    .then(data => {
      console.log("response:", JSON.stringify(data, null, 2));
      window.location.assign("finish.html"); // 修正: 送信完了後は finish.html に遷移
    })
    .catch(err => {
      console.error(`送信エラー: ${err.message || err}`); // 修正: ポップアップではなく console.error へ変更
    });
  });
}