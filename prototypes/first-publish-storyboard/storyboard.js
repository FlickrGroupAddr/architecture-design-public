"use strict";

const scenes = Array.from(document.querySelectorAll("[data-scene]"));
const sceneList = document.querySelector("#scene-list");
const progressLabel = document.querySelector("#progress-label");
const contextLabel = document.querySelector("#context-label");
const stage = document.querySelector("#scene-stage");
const resettableNotes = ["refresh-note", "inspect-note"].map((id) => document.querySelector(`#${id}`));
const initialNoteText = new Map(resettableNotes.map((note) => [note, note.textContent]));
let currentScene = 0;

function sceneTitle(scene) {
  const heading = scene.querySelector("h2");
  return heading ? heading.textContent.trim() : scene.dataset.scene;
}

function buildSceneNavigation() {
  scenes.forEach((scene, index) => {
    const item = document.createElement("li");
    const button = document.createElement("button");
    button.type = "button";
    button.dataset.sceneIndex = String(index);
    button.dataset.number = String(index + 1).padStart(2, "0");
    button.textContent = sceneTitle(scene);
    button.addEventListener("click", () => showScene(index, true));
    item.append(button);
    sceneList.append(item);
  });
}

function boundedIndex(index) {
  return Math.max(0, Math.min(index, scenes.length - 1));
}

function showScene(index, moveFocus = false) {
  currentScene = boundedIndex(index);
  scenes.forEach((scene, sceneIndex) => {
    scene.hidden = sceneIndex !== currentScene;
  });

  const navigationButtons = sceneList.querySelectorAll("button");
  navigationButtons.forEach((button, sceneIndex) => {
    if (sceneIndex === currentScene) {
      button.setAttribute("aria-current", "step");
      button.scrollIntoView({ block: "nearest", inline: "nearest" });
    } else {
      button.removeAttribute("aria-current");
    }
  });

  const scene = scenes[currentScene];
  progressLabel.textContent = `Scene ${currentScene + 1} of ${scenes.length}`;
  contextLabel.textContent = scene.dataset.context;
  history.replaceState(null, "", `#${scene.dataset.scene}`);

  if (moveFocus) {
    stage.focus({ preventScroll: true });
    window.scrollTo({ top: 0, left: 0, behavior: "smooth" });
  }
}

function sceneIndexFromHash() {
  const requestedId = window.location.hash.slice(1);
  const index = scenes.findIndex((scene) => scene.dataset.scene === requestedId);
  return index === -1 ? 0 : index;
}

function resetStoryboard() {
  document.querySelectorAll("input[type='checkbox']").forEach((input) => {
    input.checked = input.defaultChecked;
  });
  initialNoteText.forEach((noteText, note) => {
    note.textContent = noteText;
  });
  showScene(0, true);
}

document.addEventListener("click", (event) => {
  const target = event.target.closest("button");
  if (!target) {
    return;
  }

  if (target.matches("[data-next]")) {
    showScene(currentScene + 1, true);
  } else if (target.matches("[data-previous]")) {
    showScene(currentScene - 1, true);
  } else if (target.matches("[data-restart]")) {
    resetStoryboard();
  } else if (target.matches("[data-refresh-note]")) {
    const note = document.querySelector(`#${target.dataset.refreshNote}`);
    if (note) {
      note.textContent = "Status refreshed from fake durable state. No worker action was triggered.";
    }
  } else if (target.matches("[data-inspect]")) {
    const note = document.querySelector("#inspect-note");
    if (note) {
      note.textContent = "No page opened. In production this would be read-only Flickr inspection guidance.";
    }
  }
});

document.addEventListener("keydown", (event) => {
  const element = event.target;
  const isFormControl = element instanceof HTMLElement && element.matches("input, select, textarea");
  if (isFormControl) {
    return;
  }

  if (event.key === "ArrowRight") {
    event.preventDefault();
    showScene(currentScene + 1, true);
  } else if (event.key === "ArrowLeft") {
    event.preventDefault();
    showScene(currentScene - 1, true);
  }
});

window.addEventListener("hashchange", () => showScene(sceneIndexFromHash()));

buildSceneNavigation();
showScene(sceneIndexFromHash());
window.addEventListener("load", () => window.scrollTo({ top: 0, left: 0 }));
