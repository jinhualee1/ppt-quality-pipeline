const state = {
  report: null,
  annotations: {},
  pages: [],
  current: 0,
  fit: true,
  dirty: false,
};

const elements = {
  runSummary: document.querySelector("#run-summary"),
  itemCount: document.querySelector("#item-count"),
  itemList: document.querySelector("#item-list"),
  slideTitle: document.querySelector("#slide-title"),
  slidePosition: document.querySelector("#slide-position"),
  slideImage: document.querySelector("#slide-image"),
  emptyState: document.querySelector("#empty-state"),
  canvas: document.querySelector("#canvas"),
  automatedStatus: document.querySelector("#automated-status"),
  query: document.querySelector("#query"),
  note: document.querySelector("#note"),
  previous: document.querySelector("#previous"),
  next: document.querySelector("#next"),
  fit: document.querySelector("#fit"),
  save: document.querySelector("#save"),
  saveState: document.querySelector("#save-state"),
  labels: [...document.querySelectorAll("[data-label]")],
};

function pageKey(page) {
  return `${page.item.id}/${page.deckIndex + 1}/${page.pageIndex + 1}`;
}

function setDirty(value) {
  state.dirty = value;
  elements.saveState.textContent = value ? "Unsaved changes" : "Saved";
  elements.saveState.classList.toggle("dirty", value);
}

function flattenPages(report) {
  const pages = [];
  report.items.forEach((item) => {
    item.decks.forEach((deck, deckIndex) => {
      deck.pages.forEach((path, pageIndex) => {
        pages.push({ item, deck, deckIndex, pageIndex, path });
      });
    });
  });
  return pages;
}

function renderItems() {
  elements.itemList.innerHTML = "";
  elements.itemCount.textContent = String(state.report.items.length);
  state.report.items.forEach((item) => {
    const firstPage = state.pages.findIndex((page) => page.item.id === item.id);
    const activeItem = state.pages[state.current]?.item.id;
    const button = document.createElement("button");
    button.type = "button";
    button.className = `item-button ${item.status === "needs_review" ? "needs-review" : ""}`;
    button.classList.toggle("active", activeItem === item.id);
    button.disabled = firstPage < 0;
    button.innerHTML = `
      <span class="status-dot" aria-hidden="true"></span>
      <span class="item-copy"><strong>${escapeHtml(item.id)}</strong><span>${escapeHtml(item.query)}</span></span>
    `;
    button.addEventListener("click", () => {
      state.current = firstPage;
      render();
    });
    elements.itemList.append(button);
  });
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function currentAnnotation() {
  const page = state.pages[state.current];
  if (!page) return { labels: [], note: "" };
  const key = pageKey(page);
  state.annotations[key] ||= { labels: [], note: "" };
  return state.annotations[key];
}

function renderAutomatedStatus(item, deck) {
  elements.automatedStatus.innerHTML = "";
  const fidelity = document.createElement("div");
  fidelity.className = `issue-chip ${deck.fidelity === "high" ? "pass" : ""}`;
  fidelity.textContent =
    `${deck.fidelity === "high" ? "High-fidelity" : "Preview"} render · ${deck.renderer}`;
  elements.automatedStatus.append(fidelity);
  const issues = item.issues || [];
  if (!issues.length) {
    const chip = document.createElement("div");
    chip.className = "issue-chip pass";
    chip.textContent = "No automated issues";
    elements.automatedStatus.append(chip);
    return;
  }
  issues.forEach((issue) => {
    const chip = document.createElement("div");
    chip.className = "issue-chip";
    chip.textContent = issue.message;
    elements.automatedStatus.append(chip);
  });
}

function render() {
  const page = state.pages[state.current];
  const hasPage = Boolean(page);
  elements.slideImage.hidden = !hasPage;
  elements.emptyState.hidden = hasPage;
  elements.previous.disabled = !hasPage || state.current === 0;
  elements.next.disabled = !hasPage || state.current === state.pages.length - 1;

  if (!page) {
    elements.slideTitle.textContent = "No rendered slides";
    elements.slidePosition.textContent = "";
    elements.query.textContent = "";
    elements.note.value = "";
    renderItems();
    return;
  }

  elements.slideImage.src = `/assets/${page.path.split("/").map(encodeURIComponent).join("/")}`;
  elements.slideTitle.textContent =
    `${page.item.id} · ${page.deck.kind.toUpperCase()} · ${page.deck.renderer}`;
  elements.slidePosition.textContent = `${state.current + 1} / ${state.pages.length}`;
  elements.query.textContent = page.item.query;
  renderAutomatedStatus(page.item, page.deck);
  const annotation = currentAnnotation();
  elements.note.value = annotation.note || "";
  elements.labels.forEach((button) => {
    button.classList.toggle("selected", annotation.labels.includes(button.dataset.label));
  });
  elements.canvas.classList.toggle("actual-size", !state.fit);
  renderItems();
}

function updateLabel(label) {
  const annotation = currentAnnotation();
  if (label === "no_issue") {
    annotation.labels = annotation.labels.includes(label) ? [] : [label];
  } else {
    annotation.labels = annotation.labels.filter((item) => item !== "no_issue");
    annotation.labels = annotation.labels.includes(label)
      ? annotation.labels.filter((item) => item !== label)
      : [...annotation.labels, label];
  }
  setDirty(true);
  render();
}

async function save() {
  elements.save.disabled = true;
  try {
    const response = await fetch("/api/annotations", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(state.annotations),
    });
    if (!response.ok) throw new Error(`Save failed: ${response.status}`);
    setDirty(false);
  } finally {
    elements.save.disabled = false;
  }
}

async function initialize() {
  const [reportResponse, annotationsResponse] = await Promise.all([
    fetch("/api/report"),
    fetch("/api/annotations"),
  ]);
  state.report = await reportResponse.json();
  state.annotations = await annotationsResponse.json();
  state.pages = flattenPages(state.report);
  const summary = state.report.summary;
  elements.runSummary.textContent =
    `${summary.items} items · ${summary.rendered_pages} slides · ${summary.needs_review} need review`;
  render();
}

elements.previous.addEventListener("click", () => {
  if (state.current > 0) {
    state.current -= 1;
    render();
  }
});

elements.next.addEventListener("click", () => {
  if (state.current < state.pages.length - 1) {
    state.current += 1;
    render();
  }
});

elements.fit.addEventListener("click", () => {
  state.fit = !state.fit;
  render();
});

elements.save.addEventListener("click", save);
elements.labels.forEach((button) => button.addEventListener("click", () => updateLabel(button.dataset.label)));
elements.note.addEventListener("input", () => {
  currentAnnotation().note = elements.note.value;
  setDirty(true);
});

window.addEventListener("beforeunload", (event) => {
  if (state.dirty) event.preventDefault();
});

document.addEventListener("keydown", (event) => {
  if (event.target === elements.note) return;
  if (event.key === "ArrowLeft") elements.previous.click();
  if (event.key === "ArrowRight") elements.next.click();
  if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "s") {
    event.preventDefault();
    save();
  }
});

initialize().catch((error) => {
  elements.runSummary.textContent = error.message;
  elements.emptyState.hidden = false;
  elements.emptyState.textContent = "The review workspace could not load this run.";
});
