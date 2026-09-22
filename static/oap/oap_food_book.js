(() => {
  "use strict";

  const heading = document.querySelector("#food-fact-title");
  const copy = document.querySelector("#food-fact-copy");
  const areaShapes = Array.from(document.querySelectorAll("[data-body-area]"));
  const areaButtons = Array.from(document.querySelectorAll("[data-area-button]"));
  const foodButtons = Array.from(document.querySelectorAll("[data-food]"));
  const checkpointForm = document.querySelector("#food-checkpoint-form");
  const checkpointResult = document.querySelector("#food-checkpoint-result");
  const workspace = document.querySelector(".learning-card-workspace");
  const cardForm = document.querySelector("#learning-card-form");
  const reflectionInput = document.querySelector("#learning-reflection");
  const rightsInput = document.querySelector("#learning-rights");
  const characterCount = document.querySelector("#learning-character-count");
  const selectionCopy = document.querySelector("#learning-card-selection");
  const cardMessage = document.querySelector("#learning-card-message");
  const previewTitle = document.querySelector("#learning-card-preview-title");
  const previewFact = document.querySelector("#learning-card-fact");
  const previewReflection = document.querySelector("#learning-card-reflection");
  const previewSources = document.querySelector("#learning-card-sources");
  const preserveButton = document.querySelector("#preserve-learning-card");
  const downloadButton = document.querySelector("#download-learning-card");
  const shareButton = document.querySelector("#share-learning-card");
  const savedMessage = document.querySelector("#private-learning-records-message");
  const savedList = document.querySelector("#private-learning-records-list");

  if (!heading || !copy || areaButtons.length === 0) return;

  const areas = new Map(
    areaButtons.map((button) => [
      button.dataset.areaButton,
      {
        id: button.dataset.areaButton,
        name: button.dataset.areaName || "Body area",
        summary: button.dataset.areaSummary || "",
        sources: (button.dataset.areaSources || "").split(",").filter(Boolean),
      },
    ]),
  );
  const sources = new Map(
    Array.from(document.querySelectorAll("[data-food-source]")).map((item) => {
      const link = item.querySelector("a");
      return [
        item.dataset.foodSource,
        {
          id: item.dataset.foodSource,
          name: link?.textContent.replace("↗", "").trim() || "Official source",
          url: link?.href || "",
        },
      ];
    }),
  );

  let selectedFood = null;
  let currentCard = null;

  const setMessage = (node, message, tone = "") => {
    if (!node) return;
    node.textContent = message;
    if (tone) node.dataset.tone = tone;
    else delete node.dataset.tone;
  };

  const setCardActions = (enabled) => {
    [preserveButton, downloadButton, shareButton].forEach((button) => {
      if (button) button.disabled = !enabled;
    });
  };

  const invalidateCard = () => {
    currentCard = null;
    setCardActions(false);
  };

  function selectArea(areaId, foodButton = null) {
    const area = areas.get(areaId);
    if (!area) return;

    areaShapes.forEach((shape) => {
      shape.classList.toggle("is-active", shape.dataset.bodyArea === areaId);
    });
    areaButtons.forEach((button) => {
      button.setAttribute(
        "aria-pressed",
        String(button.dataset.areaButton === areaId),
      );
    });
    foodButtons.forEach((button) => {
      button.setAttribute("aria-pressed", String(button === foodButton));
    });

    if (foodButton) {
      const foodName = foodButton.dataset.foodName || "Vegetable";
      const nutrients = foodButton.dataset.foodNutrients || "Nutrients";
      selectedFood = {
        id: foodButton.dataset.food,
        name: foodName,
        nutrients,
        areaId,
        sources: (foodButton.dataset.foodSources || "")
          .split(",")
          .filter(Boolean),
      };
      heading.textContent = `${foodName} → ${area.name}`;
      copy.textContent = `${nutrients}. ${area.summary}`;
      if (selectionCopy) {
        selectionCopy.textContent = `${foodName} selected · linked to ${area.name}`;
      }
    } else {
      selectedFood = null;
      heading.textContent = area.name;
      copy.textContent = area.summary;
      if (selectionCopy) {
        selectionCopy.textContent = "Choose a vegetable above to attach an official Food Book fact.";
      }
    }
    invalidateCard();
  }

  areaShapes.forEach((shape) => {
    const activate = () => selectArea(shape.dataset.bodyArea);
    shape.addEventListener("click", activate);
    shape.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        activate();
      }
    });
  });

  areaButtons.forEach((button) => {
    button.addEventListener("click", () => selectArea(button.dataset.areaButton));
  });

  foodButtons.forEach((button) => {
    button.addEventListener("click", () => {
      selectArea(button.dataset.foodArea, button);
    });
  });

  if (checkpointForm && checkpointResult) {
    checkpointForm.addEventListener("submit", (event) => {
      event.preventDefault();
      const checkpoints = Array.from(
        checkpointForm.querySelectorAll("[data-checkpoint]"),
      );
      let answered = 0;
      let correct = 0;
      checkpoints.forEach((checkpoint) => {
        const chosen = checkpoint.querySelector("input:checked");
        if (!chosen) return;
        answered += 1;
        if (chosen.value === checkpoint.dataset.checkpointAnswer) correct += 1;
      });
      if (answered !== checkpoints.length) {
        setMessage(
          checkpointResult,
          `Answer all ${checkpoints.length} questions before checking.`,
          "warning",
        );
      } else if (correct === checkpoints.length) {
        setMessage(
          checkpointResult,
          `${correct}/${checkpoints.length} correct. You understood the source-backed core.`,
          "success",
        );
      } else {
        setMessage(
          checkpointResult,
          `${correct}/${checkpoints.length} correct. Re-read the chapters and try again.`,
          "warning",
        );
      }
    });
  }

  const uniqueSourceList = (food, area) => {
    const ids = [...new Set([...(food.sources || []), ...(area.sources || [])])];
    return ids.map((id) => sources.get(id)).filter(Boolean);
  };

  const exportText = (card) => {
    const sourceLines = card.sources
      .map((source) => `- ${source.name}: ${source.url}`)
      .join("\n");
    return [
      "OAP LIBRARY · FOOD BOOK",
      "",
      "SOURCE-BACKED FACT",
      card.fact,
      "",
      "MY REFLECTION",
      card.reflection,
      "",
      "OFFICIAL SOURCES",
      sourceLines,
      "",
      "Educational information only. Food supports the whole body and this card does not diagnose or treat illness.",
      "",
      "BORN LOCAL. BUILT GLOBAL. EARTH IS OUR TURF.",
    ].join("\n");
  };

  const renderPreview = (card) => {
    if (!previewTitle || !previewFact || !previewReflection || !previewSources) return;
    previewTitle.textContent = `${card.foodName} → ${card.areaName}`;
    previewFact.textContent = card.fact;
    previewReflection.textContent = card.reflection;
    previewSources.replaceChildren();
    card.sources.forEach((source) => {
      const item = document.createElement("li");
      const link = document.createElement("a");
      link.href = source.url;
      link.target = "_blank";
      link.rel = "noreferrer noopener";
      link.textContent = source.name;
      item.append(link);
      previewSources.append(item);
    });
  };

  const downloadText = (text) => {
    const blob = new Blob([text], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "oap-food-book-learning-card.txt";
    document.body.append(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
  };

  const shareText = async (text) => {
    if (navigator.share) {
      await navigator.share({ title: "OAP Food Book learning card", text });
      return "Device share opened. You remain in control of the destination.";
    }
    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(text);
      return "Learning card copied with its official sources.";
    }
    throw new Error("device_share_unavailable");
  };

  if (reflectionInput && characterCount) {
    reflectionInput.addEventListener("input", () => {
      characterCount.textContent = String(reflectionInput.value.length);
      invalidateCard();
    });
  }
  rightsInput?.addEventListener("change", invalidateCard);

  cardForm?.addEventListener("submit", (event) => {
    event.preventDefault();
    const reflection = reflectionInput?.value.trim() || "";
    if (!selectedFood) {
      setMessage(cardMessage, "Choose a vegetable before building the card.", "warning");
      return;
    }
    if (!reflection) {
      setMessage(cardMessage, "Write your reflection before building the card.", "warning");
      reflectionInput?.focus();
      return;
    }
    if (!rightsInput?.checked) {
      setMessage(cardMessage, "Confirm the reflection is yours and keep its sources attached.", "warning");
      rightsInput?.focus();
      return;
    }
    const area = areas.get(selectedFood.areaId);
    if (!area) return;
    currentCard = {
      foodId: selectedFood.id,
      foodName: selectedFood.name,
      areaId: area.id,
      areaName: area.name,
      fact: `${selectedFood.name}: ${selectedFood.nutrients}. ${area.summary}`,
      reflection,
      sources: uniqueSourceList(selectedFood, area),
    };
    currentCard.exportText = exportText(currentCard);
    renderPreview(currentCard);
    setCardActions(true);
    setMessage(cardMessage, "Learning card built locally. Nothing has been shared.", "success");
  });

  downloadButton?.addEventListener("click", () => {
    if (!currentCard) return;
    downloadText(currentCard.exportText);
    setMessage(cardMessage, "Learning card downloaded to your device.", "success");
  });

  shareButton?.addEventListener("click", async () => {
    if (!currentCard || !rightsInput?.checked) return;
    try {
      const message = await shareText(currentCard.exportText);
      setMessage(cardMessage, message, "success");
    } catch (error) {
      if (error?.name !== "AbortError") {
        setMessage(cardMessage, "Device sharing is unavailable. Download the card instead.", "warning");
      }
    }
  });

  const recordsUrl = workspace?.dataset.learningRecordsUrl || "";
  const csrfToken = workspace?.dataset.csrfToken || "";

  const apiJson = async (url, options = {}) => {
    const response = await fetch(url, {
      credentials: "same-origin",
      ...options,
      headers: { Accept: "application/json", ...(options.headers || {}) },
    });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) {
      const error = new Error(payload?.error?.message || "request_failed");
      error.code = payload?.error?.code || "request_failed";
      throw error;
    }
    return payload;
  };

  const savedCard = (record) => {
    const article = document.createElement("article");
    article.className = "private-learning-record";
    article.dataset.recordId = record.record_id;

    const title = document.createElement("h4");
    title.textContent = record.fact?.split(":", 1)[0] || "Food Book card";
    const fact = document.createElement("p");
    fact.textContent = record.fact || "";
    const reflection = document.createElement("blockquote");
    reflection.textContent = record.reflection || "";
    const actions = document.createElement("div");
    actions.className = "private-learning-record-actions";

    const download = document.createElement("button");
    download.type = "button";
    download.textContent = "Download";
    download.addEventListener("click", () => downloadText(record.export_text || ""));

    const share = document.createElement("button");
    share.type = "button";
    share.textContent = "Share from device";
    share.addEventListener("click", async () => {
      try {
        const message = await shareText(record.export_text || "");
        setMessage(savedMessage, message, "success");
      } catch (error) {
        if (error?.name !== "AbortError") {
          setMessage(savedMessage, "Device sharing is unavailable. Download the card instead.", "warning");
        }
      }
    });

    const remove = document.createElement("button");
    remove.type = "button";
    remove.textContent = "Delete private copy";
    remove.addEventListener("click", async () => {
      remove.disabled = true;
      try {
        await apiJson(`${recordsUrl}/${encodeURIComponent(record.record_id)}`, {
          method: "DELETE",
          headers: { "X-OAP-CSRF": csrfToken },
        });
        article.remove();
        setMessage(savedMessage, "Private learning card deleted.", "success");
      } catch (error) {
        remove.disabled = false;
        setMessage(savedMessage, error.message || "The private card could not be deleted.", "warning");
      }
    });

    actions.append(download, share, remove);
    article.append(title, fact, reflection, actions);
    return article;
  };

  const renderSavedRecords = (records) => {
    if (!savedList) return;
    savedList.replaceChildren();
    records.forEach((record) => savedList.append(savedCard(record)));
    if (records.length === 0) {
      const empty = document.createElement("p");
      empty.textContent = "No private learning cards saved yet.";
      savedList.append(empty);
    }
  };

  preserveButton?.addEventListener("click", async () => {
    if (!currentCard || !recordsUrl || !rightsInput?.checked) return;
    preserveButton.disabled = true;
    try {
      const payload = await apiJson(recordsUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-OAP-CSRF": csrfToken,
        },
        body: JSON.stringify({
          food_id: currentCard.foodId,
          area_id: currentCard.areaId,
          reflection: currentCard.reflection,
          rights_attested: true,
        }),
      });
      if (savedList && payload.record) {
        if (!savedList.querySelector("[data-record-id]")) savedList.replaceChildren();
        savedList.prepend(savedCard(payload.record));
      }
      setMessage(cardMessage, "Learning card preserved privately in OAP Data.", "success");
    } catch (error) {
      setMessage(
        cardMessage,
        error.message || "Private preservation is unavailable. Download still works.",
        "warning",
      );
    } finally {
      preserveButton.disabled = false;
    }
  });

  if (recordsUrl && savedList) {
    apiJson(recordsUrl)
      .then((payload) => renderSavedRecords(payload.records || []))
      .catch(() => {
        setMessage(
          savedMessage,
          "Private OAP preservation is unavailable. You can still build and download a card.",
          "warning",
        );
      });
  }
})();
