import test from "node:test";
import assert from "node:assert/strict";

import {
  createSceneReviewPageActions,
  createLoadingSceneReviewPageState,
  loadSceneReviewPage,
  SceneReviewPage,
  startSceneReviewSave,
  updateSceneReviewDraft,
} from "../src/pages/SceneReviewPage.tsx";
import { findElement } from "./test-tree.ts";

test("scene review page can load scenes and audio metadata", async () => {
  const page = await loadSceneReviewPage({
    api: {
      getSceneReview: async () => [
        {
          id: "scene-001",
          type: "dialogue",
          image: "images/001.png",
          subtitleText: "edited subtitle",
          audio: "audio/001.wav",
          durationMs: 1200,
          stylePreset: "dramatic",
          audioMetadata: {
            id: "voice-001",
            frameId: "frame-001",
            mode: "tts",
            role: "character",
            audioFile: "audio/001.wav",
            durationMs: 1200,
            replaceAudioPath: "/replace",
            skipRecordingPath: "/skip",
          },
        },
      ],
    },
    projectId: "demo-001",
  });

  assert.equal(page.scenes.length, 1);
  assert.equal(page.drafts[0]?.stylePreset, "dramatic");
  assert.equal(page.isLoading, false);
  assert.deepEqual(page.savingSceneIds, []);
});

test("scene review page exposes a loading state and validates edited scenes", async () => {
  const loading = createLoadingSceneReviewPageState();
  assert.equal(loading.isLoading, true);
  assert.equal(loading.scenes.length, 0);
  assert.equal(loading.drafts.length, 0);

  const page = await loadSceneReviewPage({
    api: {
      getSceneReview: async () => [
        {
          id: "scene-001",
          type: "dialogue",
          image: "images/001.png",
          subtitleText: "edited subtitle",
          audio: "audio/001.wav",
          durationMs: 1200,
          stylePreset: "dramatic",
          audioMetadata: {
            id: "voice-001",
            frameId: "frame-001",
            mode: "tts",
            role: "character",
            audioFile: "audio/001.wav",
            durationMs: 1200,
            replaceAudioPath: "/replace",
            skipRecordingPath: "/skip",
          },
        },
      ],
    },
    projectId: "demo-001",
  });

  const edited = updateSceneReviewDraft(page, "scene-001", {
    subtitleText: "edited subtitle",
    durationMs: 0,
    stylePreset: "not-a-style",
  });

  assert.equal(edited.drafts[0]?.subtitleText, "edited subtitle");
  assert.match(edited.validationErrors["scene-001"]?.durationMs ?? "", /positive/i);
  assert.match(edited.validationErrors["scene-001"]?.stylePreset ?? "", /invalid/i);

  let called = false;
  const result = startSceneReviewSave({
    api: {
      updateScene: async () => {
        called = true;
        throw new Error("should not reach api");
      },
    },
    projectId: "demo-001",
    sceneId: "scene-001",
    state: edited,
  });

  assert.equal(called, false);
  assert.equal(result.completion, null);
  assert.equal(result.state.savingSceneIds.includes("scene-001"), false);
  assert.match(result.state.errorMessages["scene-001"] ?? "", /fix validation errors/i);
});

test("scene review page saves changes and refreshes draft state from the response", async () => {
  const calls = [];
  const page = await loadSceneReviewPage({
    api: {
      getSceneReview: async () => [
        {
          id: "scene-001",
          type: "dialogue",
          image: "images/001.png",
          subtitleText: "edited subtitle",
          audio: "audio/001.wav",
          durationMs: 1200,
          stylePreset: "dramatic",
          audioMetadata: null,
        },
      ],
    },
    projectId: "demo-001",
  });

  const edited = updateSceneReviewDraft(page, "scene-001", {
    subtitleText: "draft subtitle",
    durationMs: 900,
    stylePreset: "fast",
  });

  const saveAttempt = startSceneReviewSave({
    api: {
      updateScene: async (projectId, sceneId, payload) => {
        calls.push({ projectId, sceneId, payload });
        return {
          id: sceneId,
          type: "dialogue",
          image: "images/001.png",
          subtitleText: "saved subtitle",
          durationMs: 1100,
          stylePreset: "calm",
          audioMetadata: null,
        };
      },
    },
    projectId: "demo-001",
    sceneId: "scene-001",
    state: edited,
  });

  assert.deepEqual(saveAttempt.state.savingSceneIds, ["scene-001"]);

  const savedState = await saveAttempt.completion;

  assert.deepEqual(calls, [
    {
      projectId: "demo-001",
      sceneId: "scene-001",
      payload: {
        subtitleText: "draft subtitle",
        durationMs: 900,
        stylePreset: "fast",
      },
    },
  ]);
  assert.deepEqual(savedState.savingSceneIds, []);
  assert.equal(savedState.errorMessages["scene-001"], undefined);
  assert.equal(savedState.saveMessages["scene-001"], "Scene review saved.");
  assert.equal(savedState.scenes[0]?.durationMs, 1100);
  assert.equal(savedState.drafts[0]?.subtitleText, "saved subtitle");
  assert.equal(savedState.drafts[0]?.durationMs, 1100);
  assert.equal(savedState.drafts[0]?.stylePreset, "calm");
});

test("scene review page keeps the local draft when save fails", async () => {
  const page = await loadSceneReviewPage({
    api: {
      getSceneReview: async () => [
        {
          id: "scene-001",
          type: "dialogue",
          image: "images/001.png",
          subtitleText: "edited subtitle",
          audio: "audio/001.wav",
          durationMs: 1200,
          stylePreset: "dramatic",
          audioMetadata: null,
        },
      ],
    },
    projectId: "demo-001",
  });

  const edited = updateSceneReviewDraft(page, "scene-001", {
    subtitleText: "failed subtitle",
    durationMs: 1800,
  });

  const saveAttempt = startSceneReviewSave({
    api: {
      updateScene: async () => {
        throw new Error("scene save failed");
      },
    },
    projectId: "demo-001",
    sceneId: "scene-001",
    state: edited,
  });

  assert.deepEqual(saveAttempt.state.savingSceneIds, ["scene-001"]);

  const failedState = await saveAttempt.completion;

  assert.deepEqual(failedState.savingSceneIds, []);
  assert.equal(failedState.saveMessages["scene-001"], undefined);
  assert.equal(failedState.errorMessages["scene-001"], "scene save failed");
  assert.equal(failedState.drafts[0]?.subtitleText, "failed subtitle");
});

test("scene review page actions update draft state and persist through save callbacks", async () => {
  const states = [];
  const calls = [];
  const page = await loadSceneReviewPage({
    api: {
      getSceneReview: async () => [
        {
          id: "scene-001",
          type: "dialogue",
          image: "images/001.png",
          subtitleText: "edited subtitle",
          audio: "audio/001.wav",
          durationMs: 1200,
          stylePreset: "dramatic",
          audioMetadata: null,
        },
      ],
    },
    projectId: "demo-001",
  });

  let currentState = page;
  const actions = createSceneReviewPageActions({
    api: {
      updateScene: async (projectId, sceneId, payload) => {
        calls.push({ projectId, sceneId, payload });
        return {
          id: sceneId,
          type: "dialogue",
          image: "images/001.png",
          subtitleText: "saved subtitle",
          durationMs: 1800,
          stylePreset: "calm",
          audioMetadata: null,
        };
      },
    },
    projectId: "demo-001",
    getState: () => currentState,
    onStateChange: (nextState) => {
      currentState = nextState;
      states.push(nextState);
    },
  });

  actions.onSubtitleTextChange("scene-001", "draft subtitle");
  actions.onDurationMsChange("scene-001", "1500");
  actions.onStylePresetChange("scene-001", "fast");

  assert.equal(currentState.drafts[0]?.subtitleText, "draft subtitle");
  assert.equal(currentState.drafts[0]?.durationMs, 1500);
  assert.equal(currentState.drafts[0]?.stylePreset, "fast");

  await actions.onSaveScene("scene-001");

  assert.equal(states.at(-1)?.saveMessages["scene-001"], "Scene review saved.");
  assert.equal(states.at(-1)?.drafts[0]?.subtitleText, "saved subtitle");
  assert.deepEqual(calls, [
    {
      projectId: "demo-001",
      sceneId: "scene-001",
      payload: {
        subtitleText: "draft subtitle",
        durationMs: 1500,
        stylePreset: "fast",
      },
    },
  ]);
});

test("scene review page keeps newer local edits when an earlier save completes", async () => {
  let resolveSave;
  const page = await loadSceneReviewPage({
    api: {
      getSceneReview: async () => [
        {
          id: "scene-001",
          type: "dialogue",
          image: "images/001.png",
          subtitleText: "edited subtitle",
          audio: "audio/001.wav",
          durationMs: 1200,
          stylePreset: "dramatic",
          audioMetadata: null,
        },
      ],
    },
    projectId: "demo-001",
  });

  let currentState = page;
  const actions = createSceneReviewPageActions({
    api: {
      updateScene: async () =>
        await new Promise((resolve) => {
          resolveSave = resolve;
        }),
    },
    projectId: "demo-001",
    getState: () => currentState,
    onStateChange: (nextState) => {
      currentState = nextState;
    },
  });

  actions.onSubtitleTextChange("scene-001", "save me");
  const savePromise = actions.onSaveScene("scene-001");

  assert.deepEqual(currentState.savingSceneIds, ["scene-001"]);

  actions.onSubtitleTextChange("scene-001", "newer local subtitle");

  resolveSave({
    id: "scene-001",
    type: "dialogue",
    image: "images/001.png",
    subtitleText: "saved on server",
    durationMs: 1600,
    stylePreset: "calm",
    audioMetadata: null,
  });

  await savePromise;

  assert.deepEqual(currentState.savingSceneIds, []);
  assert.equal(currentState.scenes[0]?.subtitleText, "saved on server");
  assert.equal(currentState.drafts[0]?.subtitleText, "newer local subtitle");
});

test("scene review page keeps newer raw whitespace edits when an earlier save completes", async () => {
  let resolveSave;
  const page = await loadSceneReviewPage({
    api: {
      getSceneReview: async () => [
        {
          id: "scene-001",
          type: "dialogue",
          image: "images/001.png",
          subtitleText: "edited subtitle",
          audio: "audio/001.wav",
          durationMs: 1200,
          stylePreset: "dramatic",
          audioMetadata: null,
        },
      ],
    },
    projectId: "demo-001",
  });

  let currentState = page;
  const actions = createSceneReviewPageActions({
    api: {
      updateScene: async () =>
        await new Promise((resolve) => {
          resolveSave = resolve;
        }),
    },
    projectId: "demo-001",
    getState: () => currentState,
    onStateChange: (nextState) => {
      currentState = nextState;
    },
  });

  actions.onSubtitleTextChange("scene-001", " ");
  const savePromise = actions.onSaveScene("scene-001");

  actions.onSubtitleTextChange("scene-001", "   ");

  resolveSave({
    id: "scene-001",
    type: "dialogue",
    image: "images/001.png",
    subtitleText: null,
    durationMs: 1600,
    stylePreset: "calm",
    audioMetadata: null,
  });

  await savePromise;

  assert.equal(currentState.scenes[0]?.subtitleText, null);
  assert.equal(currentState.drafts[0]?.subtitleText, "   ");
});

test("scene review page keeps newer local edits when an earlier save fails", async () => {
  let rejectSave;
  const page = await loadSceneReviewPage({
    api: {
      getSceneReview: async () => [
        {
          id: "scene-001",
          type: "dialogue",
          image: "images/001.png",
          subtitleText: "edited subtitle",
          audio: "audio/001.wav",
          durationMs: 1200,
          stylePreset: "dramatic",
          audioMetadata: null,
        },
      ],
    },
    projectId: "demo-001",
  });

  let currentState = page;
  const actions = createSceneReviewPageActions({
    api: {
      updateScene: async () =>
        await new Promise((_, reject) => {
          rejectSave = reject;
        }),
    },
    projectId: "demo-001",
    getState: () => currentState,
    onStateChange: (nextState) => {
      currentState = nextState;
    },
  });

  actions.onSubtitleTextChange("scene-001", "save me");
  const savePromise = actions.onSaveScene("scene-001");

  assert.deepEqual(currentState.savingSceneIds, ["scene-001"]);

  actions.onSubtitleTextChange("scene-001", "newer local subtitle");
  rejectSave(new Error("scene save failed"));

  await savePromise;

  assert.deepEqual(currentState.savingSceneIds, []);
  assert.equal(currentState.errorMessages["scene-001"], "scene save failed");
  assert.equal(currentState.saveMessages["scene-001"], undefined);
  assert.equal(currentState.drafts[0]?.subtitleText, "newer local subtitle");
});

test("scene review page renders input and save callbacks when actions are provided", () => {
  const events = [];
  const tree = SceneReviewPage({
    scenes: [{ id: "scene-001" }],
    drafts: [
      {
        id: "scene-001",
        subtitleText: "draft subtitle",
        durationMs: 1500,
        stylePreset: "fast",
        audioActions: [],
      },
    ],
    actions: {
      onSubtitleTextChange: (sceneId, value) => events.push(["subtitle", sceneId, value]),
      onDurationMsChange: (sceneId, value) => events.push(["duration", sceneId, value]),
      onStylePresetChange: (sceneId, value) => events.push(["style", sceneId, value]),
      onSaveScene: (sceneId) => events.push(["save", sceneId]),
    },
  });

  const textarea = findElement(
    tree,
    (node) => node.type === "textarea" && node.props?.name === "subtitleText-scene-001"
  );
  const durationInput = findElement(
    tree,
    (node) => node.type === "input" && node.props?.name === "durationMs-scene-001"
  );
  const styleSelect = findElement(
    tree,
    (node) => node.type === "select" && node.props?.name === "stylePreset-scene-001"
  );
  const saveButton = findElement(tree, (node) => node.type === "button");

  assert.equal(textarea.props.value, "draft subtitle");
  assert.equal(textarea.props.defaultValue, undefined);
  assert.equal(durationInput.props.value, 1500);
  assert.equal(durationInput.props.defaultValue, undefined);
  assert.equal(styleSelect.props.value, "fast");
  assert.equal(styleSelect.props.defaultValue, undefined);

  textarea.props.onChange({ target: { value: "subtitle in ui" } });
  durationInput.props.onChange({ target: { value: "2100" } });
  styleSelect.props.onChange({ target: { value: "calm" } });
  saveButton.props.onClick();

  assert.deepEqual(events, [
    ["subtitle", "scene-001", "subtitle in ui"],
    ["duration", "scene-001", "2100"],
    ["style", "scene-001", "calm"],
    ["save", "scene-001"],
  ]);
});

test("scene review page renders invalid duration values as an empty input", () => {
  const tree = SceneReviewPage({
    scenes: [{ id: "scene-001" }],
    drafts: [
      {
        id: "scene-001",
        subtitleText: "draft subtitle",
        durationMs: Number.NaN,
        stylePreset: "fast",
        audioActions: [],
      },
    ],
    validationErrors: {
      "scene-001": {
        durationMs: "Duration must be a positive integer.",
      },
    },
  });

  const durationInput = findElement(
    tree,
    (node) => node.type === "input" && node.props?.name === "durationMs-scene-001"
  );

  assert.equal(durationInput.props.value, "");
});
