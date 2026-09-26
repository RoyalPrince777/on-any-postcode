"use strict";

(() => {
  const consoleRoot = document.querySelector("[data-arena-console]");
  const initialNode = document.getElementById("arena-initial-state");
  if (!consoleRoot || !initialNode) return;

  const csrf = document.querySelector('meta[name="oap-csrf-token"]')?.content || "";
  const statusNode = consoleRoot.querySelector("[data-arena-status]");
  const scoreNode = consoleRoot.querySelector("[data-arena-score]");
  const answeredNode = consoleRoot.querySelector("[data-arena-answered]");
  const questionNode = consoleRoot.querySelector("[data-arena-question]");
  const feedbackNode = consoleRoot.querySelector("[data-arena-feedback]");
  const errorNode = consoleRoot.querySelector("[data-arena-error]");
  const receiptNode = consoleRoot.querySelector("[data-arena-receipt]");
  const actions = [...consoleRoot.querySelectorAll("[data-arena-action]")];
  let state;

  try {
    state = JSON.parse(initialNode.textContent || "{}");
  } catch (_error) {
    state = {started: false, status: "idle", score: 0, answered: 0, total: 7};
  }

  const requestId = () => {
    if (globalThis.crypto?.randomUUID) return globalThis.crypto.randomUUID();
    return `arena-${Date.now()}-${Math.random().toString(16).slice(2)}`;
  };

  const setBusy = (busy) => {
    actions.forEach((button) => { button.disabled = busy; });
    questionNode.querySelectorAll("button").forEach((button) => { button.disabled = busy; });
  };

  const showError = (message) => {
    errorNode.textContent = message;
    errorNode.hidden = false;
  };

  const clearError = () => {
    errorNode.textContent = "";
    errorNode.hidden = true;
  };

  const render = () => {
    statusNode.textContent = state.status || "idle";
    scoreNode.textContent = String(state.score || 0);
    answeredNode.textContent = `${state.answered || 0}/${state.total || 7}`;
    questionNode.replaceChildren();

    if (!state.started) {
      const message = document.createElement("p");
      message.textContent = "Start when you are ready. No profile, payment or precise location is collected.";
      questionNode.append(message);
    } else if (state.status === "paused") {
      const message = document.createElement("p");
      message.textContent = "Challenge paused. Resume keeps the verified score and checkpoint.";
      questionNode.append(message);
    } else if (state.status === "stopped") {
      const message = document.createElement("p");
      message.textContent = "STOP is active. This session cannot resume; start a recovered session to play again.";
      questionNode.append(message);
    } else if (state.status === "completed") {
      const heading = document.createElement("h3");
      heading.textContent = `Challenge complete · ${state.score}/${state.total}`;
      const message = document.createElement("p");
      message.textContent = "This result is session-scoped and unranked. It has not been published or added to My Card.";
      questionNode.append(heading, message);
    } else if (state.question) {
      const eyebrow = document.createElement("p");
      eyebrow.className = "mc-eyebrow";
      eyebrow.textContent = `${state.question.category} · Question ${state.question.number}`;
      const heading = document.createElement("h3");
      heading.textContent = state.question.prompt;
      const choices = document.createElement("div");
      choices.className = "arena-choices";
      state.question.choices.forEach((choice) => {
        const button = document.createElement("button");
        button.type = "button";
        button.className = "arena-choice";
        button.textContent = choice.label;
        button.addEventListener("click", () => submitAnswer(state.question.id, choice.id));
        choices.append(button);
      });
      questionNode.append(eyebrow, heading, choices);
    }

    if (state.feedback?.explanation) {
      feedbackNode.hidden = false;
      feedbackNode.dataset.tone = state.feedback.correct ? "correct" : "wrong";
      feedbackNode.textContent = `${state.feedback.correct ? "Correct." : `Not this time. Correct: ${state.feedback.correct_label}.`} ${state.feedback.explanation}`;
    } else {
      feedbackNode.hidden = true;
      feedbackNode.textContent = "";
    }

    receiptNode.textContent = `Receipts: ${state.receipt_count || 0}${state.latest_receipt_hash ? ` · ${state.latest_receipt_hash}` : ""}`;
    const byAction = Object.fromEntries(actions.map((button) => [button.dataset.arenaAction, button]));
    byAction.start.hidden = Boolean(state.started && !["stopped", "completed"].includes(state.status));
    byAction.pause.hidden = state.status !== "active";
    byAction.resume.hidden = state.status !== "paused";
    byAction.stop.hidden = !["active", "paused"].includes(state.status);
    byAction.recover.hidden = !state.started || !["stopped", "completed"].includes(state.status);
  };

  const post = async (endpoint, payload) => {
    clearError();
    setBusy(true);
    try {
      const response = await fetch(endpoint, {
        method: "POST",
        credentials: "same-origin",
        headers: {"Content-Type": "application/json", "X-OAP-CSRF": csrf},
        body: JSON.stringify(payload),
      });
      const body = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(body?.error?.code || "arena_request_failed");
      state = body;
      render();
    } catch (error) {
      showError(`Arena could not continue safely: ${error.message}`);
    } finally {
      setBusy(false);
    }
  };

  const submitAnswer = (questionId, choiceId) => post("/arena/session/answer", {
    question_id: questionId,
    choice_id: choiceId,
    request_id: requestId(),
  });

  actions.forEach((button) => {
    button.addEventListener("click", () => {
      const action = button.dataset.arenaAction;
      const endpoint = button.dataset.endpoint;
      const payload = ["start", "recover"].includes(action) ? {} : {request_id: requestId()};
      post(endpoint, payload);
    });
  });

  render();
})();
