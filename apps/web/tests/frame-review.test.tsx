import test from "node:test";
import assert from "node:assert/strict";

import {
  createFrameReviewPageActions,
  createLoadingFrameReviewPageState,
  editFrameReviewBubble,
  FrameReviewPage,
  loadFrameReviewPage,
  startFrameReviewSave,
} from "../src/pages/FrameReviewPage.tsx";
import { findElement } from "./test-tree.ts";

test("frame review page can load review data for a frame", async () => {
  const page = await loadFrameReviewPage({
    api: {
      getFrames: async () => [
        {
          frameId: "frame-001",
          image: "images/001.png",
          ocrFile: "ocr/001.json",
          bubbles: [
            {
              id: "bubble-a",
              text: "raw line",
              bbox: { x: 0, y: 0, w: 10, h: 10 },
              order: 0,
              confidence: 0.9,
              language: "ja",
            },
          ],
          reviewedBubbles: [
            {
              id: "review-a",
              sourceBubbleId: "bubble-a",
              textOriginal: "raw line",
              textEdited: "edited line",
              order: 0,
              kind: "dialogue",
              speaker: "Hero",
            },
          ],
        },
      ],
    },
    projectId: "demo-001",
    frameId: "frame-001",
  });

  assert.equal(page.frame.frameId, "frame-001");
  assert.equal(page.draft.bubbles[0]?.textEdited, "edited line");
  assert.equal(page.isLoading, false);
  assert.equal(page.isSaving, false);
  assert.equal(page.errorMessage, null);
  assert.equal(page.saveMessage, null);
});

test("frame review page exposes a loading state and validates edited bubbles", async () => {
  const loading = createLoadingFrameReviewPageState();
  assert.equal(loading.isLoading, true);
  assert.equal(loading.frame, null);
  assert.equal(loading.draft, null);

  const page = await loadFrameReviewPage({
    api: {
      getFrames: async () => [
        {
          frameId: "frame-001",
          image: "images/001.png",
          ocrFile: "ocr/001.json",
          bubbles: [
            {
              id: "bubble-a",
              text: "raw line",
              bbox: { x: 0, y: 0, w: 10, h: 10 },
              order: 0,
              confidence: 0.9,
              language: "ja",
            },
          ],
          reviewedBubbles: [
            {
              id: "review-a",
              sourceBubbleId: "bubble-a",
              textOriginal: "raw line",
              textEdited: "edited line",
              order: 0,
              kind: "dialogue",
              speaker: "Hero",
            },
          ],
        },
      ],
    },
    projectId: "demo-001",
    frameId: "frame-001",
  });

  const edited = editFrameReviewBubble(page, "bubble-a", {
    textEdited: "   ",
    order: -1,
    kind: "narration",
    speaker: "Narrator",
  });

  assert.equal(edited.draft.bubbles[0]?.kind, "narration");
  assert.equal(edited.draft.bubbles[0]?.speaker, "Narrator");
  assert.match(edited.validationErrors["bubble-a"]?.textEdited ?? "", /required/i);
  assert.match(edited.validationErrors["bubble-a"]?.order ?? "", /non-negative/i);

  let called = false;
  const result = startFrameReviewSave({
    api: {
      updateFrameReview: async () => {
        called = true;
        throw new Error("should not reach api");
      },
    },
    projectId: "demo-001",
    frameId: "frame-001",
    state: edited,
  });

  assert.equal(called, false);
  assert.equal(result.completion, null);
  assert.equal(result.state.isSaving, false);
  assert.match(result.state.errorMessage ?? "", /fix validation errors/i);
});

test("frame review page saves changes and refreshes draft state from the response", async () => {
  const calls = [];
  const page = await loadFrameReviewPage({
    api: {
      getFrames: async () => [
        {
          frameId: "frame-001",
          image: "images/001.png",
          ocrFile: "ocr/001.json",
          bubbles: [
            {
              id: "bubble-a",
              text: "raw line",
              bbox: { x: 0, y: 0, w: 10, h: 10 },
              order: 0,
              confidence: 0.9,
              language: "ja",
            },
          ],
          reviewedBubbles: [],
        },
      ],
    },
    projectId: "demo-001",
    frameId: "frame-001",
  });

  const edited = editFrameReviewBubble(page, "bubble-a", {
    textEdited: "draft line",
    order: 2,
    kind: "narration",
    speaker: "Narrator",
  });

  const saveAttempt = startFrameReviewSave({
    api: {
      updateFrameReview: async (projectId, frameId, payload) => {
        calls.push({ projectId, frameId, payload });
        return {
          frameId,
          image: "images/001.png",
          ocrFile: "ocr/001.json",
          bubbles: [],
          reviewedBubbles: [
            {
              id: "review-a",
              sourceBubbleId: "bubble-a",
              textOriginal: "raw line",
              textEdited: "saved line",
              order: 4,
              kind: "dialogue",
              speaker: "Narrator",
            },
          ],
        };
      },
    },
    projectId: "demo-001",
    frameId: "frame-001",
    state: edited,
  });

  assert.equal(saveAttempt.state.isSaving, true);

  const savedState = await saveAttempt.completion;

  assert.deepEqual(calls, [
    {
      projectId: "demo-001",
      frameId: "frame-001",
      payload: {
        reviewedBubbles: [
          {
            sourceBubbleId: "bubble-a",
            textEdited: "draft line",
            order: 2,
            kind: "narration",
            speaker: "Narrator",
          },
        ],
        skip: false,
      },
    },
  ]);
  assert.equal(savedState.isSaving, false);
  assert.equal(savedState.errorMessage, null);
  assert.equal(savedState.saveMessage, "Frame review saved.");
  assert.equal(savedState.frame.reviewedBubbles[0]?.textEdited, "saved line");
  assert.equal(savedState.draft.bubbles[0]?.textEdited, "saved line");
  assert.equal(savedState.draft.bubbles[0]?.order, 4);
  assert.equal(savedState.draft.bubbles[0]?.kind, "dialogue");
});

test("frame review page allows ignored bubbles with empty edited text to save", async () => {
  const calls = [];
  const page = await loadFrameReviewPage({
    api: {
      getFrames: async () => [
        {
          frameId: "frame-001",
          image: "images/001.png",
          ocrFile: "ocr/001.json",
          bubbles: [
            {
              id: "bubble-a",
              text: "",
              bbox: { x: 0, y: 0, w: 10, h: 10 },
              order: 0,
              confidence: 0.9,
              language: "ja",
            },
          ],
          reviewedBubbles: [],
        },
      ],
    },
    projectId: "demo-001",
    frameId: "frame-001",
  });

  const edited = editFrameReviewBubble(page, "bubble-a", {
    textEdited: "",
    kind: "ignore",
  });

  const saveAttempt = startFrameReviewSave({
    api: {
      updateFrameReview: async (projectId, frameId, payload) => {
        calls.push({ projectId, frameId, payload });
        return {
          frameId,
          image: "images/001.png",
          ocrFile: "ocr/001.json",
          bubbles: [],
          reviewedBubbles: [
            {
              id: "review-a",
              sourceBubbleId: "bubble-a",
              textOriginal: "",
              textEdited: "",
              order: 0,
              kind: "ignore",
              speaker: undefined,
            },
          ],
        };
      },
    },
    projectId: "demo-001",
    frameId: "frame-001",
    state: edited,
  });

  assert.equal(edited.validationErrors["bubble-a"]?.textEdited, undefined);
  assert.notEqual(saveAttempt.completion, null);

  const savedState = await saveAttempt.completion;

  assert.deepEqual(calls, [
    {
      projectId: "demo-001",
      frameId: "frame-001",
      payload: {
        reviewedBubbles: [
          {
            sourceBubbleId: "bubble-a",
            textEdited: "",
            order: 0,
            kind: "ignore",
          },
        ],
        skip: false,
      },
    },
  ]);
  assert.equal(savedState.errorMessage, null);
  assert.equal(savedState.draft.bubbles[0]?.kind, "ignore");
});

test("frame review page allows clearing speaker and omits it from the saved payload", async () => {
  let called = false;
  const page = await loadFrameReviewPage({
    api: {
      getFrames: async () => [
        {
          frameId: "frame-001",
          image: "images/001.png",
          ocrFile: "ocr/001.json",
          bubbles: [
            {
              id: "bubble-a",
              text: "raw line",
              bbox: { x: 0, y: 0, w: 10, h: 10 },
              order: 0,
              confidence: 0.9,
              language: "ja",
            },
          ],
          reviewedBubbles: [
            {
              id: "review-a",
              sourceBubbleId: "bubble-a",
              textOriginal: "raw line",
              textEdited: "edited line",
              order: 0,
              kind: "dialogue",
              speaker: "Hero",
            },
          ],
        },
      ],
    },
    projectId: "demo-001",
    frameId: "frame-001",
  });

  const edited = editFrameReviewBubble(page, "bubble-a", {
    speaker: "",
  });

  const saveAttempt = startFrameReviewSave({
    api: {
      updateFrameReview: async (_projectId, frameId, payload) => {
        called = true;
        assert.deepEqual(payload, {
          reviewedBubbles: [
            {
              sourceBubbleId: "bubble-a",
              textEdited: "edited line",
              order: 0,
              kind: "dialogue",
            },
          ],
          skip: false,
        });

        return {
          frameId,
          image: "images/001.png",
          ocrFile: "ocr/001.json",
          bubbles: [],
          reviewedBubbles: [
            {
              id: "review-a",
              sourceBubbleId: "bubble-a",
              textOriginal: "raw line",
              textEdited: "edited line",
              order: 0,
              kind: "dialogue",
              speaker: undefined,
            },
          ],
        };
      },
    },
    projectId: "demo-001",
    frameId: "frame-001",
    state: edited,
  });

  assert.equal(edited.draft.bubbles[0]?.speaker, "");
  assert.equal(saveAttempt.state.validationErrors["bubble-a"]?.speaker, undefined);
  assert.equal(saveAttempt.state.isSaving, true);
  assert.notEqual(saveAttempt.completion, null);

  const savedState = await saveAttempt.completion;

  assert.equal(called, true);
  assert.equal(savedState.errorMessage, null);
  assert.equal(savedState.draft.bubbles[0]?.speaker, undefined);
});

test("frame review page keeps the local draft when save fails", async () => {
  const page = await loadFrameReviewPage({
    api: {
      getFrames: async () => [
        {
          frameId: "frame-001",
          image: "images/001.png",
          ocrFile: "ocr/001.json",
          bubbles: [
            {
              id: "bubble-a",
              text: "raw line",
              bbox: { x: 0, y: 0, w: 10, h: 10 },
              order: 0,
              confidence: 0.9,
              language: "ja",
            },
          ],
          reviewedBubbles: [],
        },
      ],
    },
    projectId: "demo-001",
    frameId: "frame-001",
  });

  const edited = editFrameReviewBubble(page, "bubble-a", {
    textEdited: "failed draft",
    kind: "narration",
    speaker: "Narrator",
  });

  const saveAttempt = startFrameReviewSave({
    api: {
      updateFrameReview: async () => {
        throw new Error("frame save failed");
      },
    },
    projectId: "demo-001",
    frameId: "frame-001",
    state: edited,
  });

  assert.equal(saveAttempt.state.isSaving, true);

  const failedState = await saveAttempt.completion;

  assert.equal(failedState.isSaving, false);
  assert.equal(failedState.saveMessage, null);
  assert.equal(failedState.errorMessage, "frame save failed");
  assert.equal(failedState.draft.bubbles[0]?.textEdited, "failed draft");
});

test("frame review page actions update draft state and persist through save callbacks", async () => {
  const states = [];
  const calls = [];
  const page = await loadFrameReviewPage({
    api: {
      getFrames: async () => [
        {
          frameId: "frame-001",
          image: "images/001.png",
          ocrFile: "ocr/001.json",
          bubbles: [
            {
              id: "bubble-a",
              text: "raw line",
              bbox: { x: 0, y: 0, w: 10, h: 10 },
              order: 0,
              confidence: 0.9,
              language: "ja",
            },
          ],
          reviewedBubbles: [],
        },
      ],
    },
    projectId: "demo-001",
    frameId: "frame-001",
  });

  let currentState = page;
  const actions = createFrameReviewPageActions({
    api: {
      updateFrameReview: async (projectId, frameId, payload) => {
        calls.push({ projectId, frameId, payload });
        return {
          frameId,
          image: "images/001.png",
          ocrFile: "ocr/001.json",
          bubbles: [],
          reviewedBubbles: [
            {
              id: "review-a",
              sourceBubbleId: "bubble-a",
              textOriginal: "raw line",
              textEdited: "saved line",
              order: 1,
              kind: "narration",
              speaker: "Narrator",
            },
          ],
        };
      },
    },
    projectId: "demo-001",
    frameId: "frame-001",
    getState: () => currentState,
    onStateChange: (nextState) => {
      currentState = nextState;
      states.push(nextState);
    },
  });

  actions.onBubbleTextEditedChange("bubble-a", "draft line");
  actions.onBubbleOrderChange("bubble-a", "1");
  actions.onBubbleKindChange("bubble-a", "narration");
  actions.onBubbleSpeakerChange("bubble-a", "Narrator");

  assert.equal(currentState.draft.bubbles[0]?.textEdited, "draft line");
  assert.equal(currentState.draft.bubbles[0]?.order, 1);
  assert.equal(currentState.draft.bubbles[0]?.kind, "narration");
  assert.equal(currentState.draft.bubbles[0]?.speaker, "Narrator");

  await actions.onSave();

  assert.equal(states.at(-1)?.saveMessage, "Frame review saved.");
  assert.equal(states.at(-1)?.draft.bubbles[0]?.textEdited, "saved line");
  assert.deepEqual(calls, [
    {
      projectId: "demo-001",
      frameId: "frame-001",
      payload: {
        reviewedBubbles: [
          {
            sourceBubbleId: "bubble-a",
            textEdited: "draft line",
            order: 1,
            kind: "narration",
            speaker: "Narrator",
          },
        ],
        skip: false,
      },
    },
  ]);
});

test("frame review page keeps newer local edits when an earlier save completes", async () => {
  let resolveSave;
  const page = await loadFrameReviewPage({
    api: {
      getFrames: async () => [
        {
          frameId: "frame-001",
          image: "images/001.png",
          ocrFile: "ocr/001.json",
          bubbles: [
            {
              id: "bubble-a",
              text: "raw line",
              bbox: { x: 0, y: 0, w: 10, h: 10 },
              order: 0,
              confidence: 0.9,
              language: "ja",
            },
          ],
          reviewedBubbles: [],
        },
      ],
    },
    projectId: "demo-001",
    frameId: "frame-001",
  });

  let currentState = page;
  const actions = createFrameReviewPageActions({
    api: {
      updateFrameReview: async () =>
        await new Promise((resolve) => {
          resolveSave = resolve;
        }),
    },
    projectId: "demo-001",
    frameId: "frame-001",
    getState: () => currentState,
    onStateChange: (nextState) => {
      currentState = nextState;
    },
  });

  actions.onBubbleTextEditedChange("bubble-a", "save me");
  const savePromise = actions.onSave();

  assert.equal(currentState.isSaving, true);

  actions.onBubbleTextEditedChange("bubble-a", "newer local draft");

  resolveSave({
    frameId: "frame-001",
    image: "images/001.png",
    ocrFile: "ocr/001.json",
    bubbles: [
      {
        id: "bubble-a",
        text: "raw line",
        bbox: { x: 0, y: 0, w: 10, h: 10 },
        order: 0,
        confidence: 0.9,
        language: "ja",
      },
    ],
    reviewedBubbles: [
      {
        id: "review-a",
        sourceBubbleId: "bubble-a",
        textOriginal: "raw line",
        textEdited: "saved on server",
        order: 0,
        kind: "dialogue",
        speaker: "Hero",
      },
    ],
  });

  await savePromise;

  assert.equal(currentState.isSaving, false);
  assert.equal(currentState.frame.reviewedBubbles[0]?.textEdited, "saved on server");
  assert.equal(currentState.draft.bubbles[0]?.textEdited, "newer local draft");
});

test("frame review page keeps newer raw whitespace edits when an earlier save completes", async () => {
  let resolveSave;
  const page = await loadFrameReviewPage({
    api: {
      getFrames: async () => [
        {
          frameId: "frame-001",
          image: "images/001.png",
          ocrFile: "ocr/001.json",
          bubbles: [
            {
              id: "bubble-a",
              text: "raw line",
              bbox: { x: 0, y: 0, w: 10, h: 10 },
              order: 0,
              confidence: 0.9,
              language: "ja",
            },
          ],
          reviewedBubbles: [],
        },
      ],
    },
    projectId: "demo-001",
    frameId: "frame-001",
  });

  let currentState = page;
  const actions = createFrameReviewPageActions({
    api: {
      updateFrameReview: async () =>
        await new Promise((resolve) => {
          resolveSave = resolve;
        }),
    },
    projectId: "demo-001",
    frameId: "frame-001",
    getState: () => currentState,
    onStateChange: (nextState) => {
      currentState = nextState;
    },
  });

  actions.onBubbleTextEditedChange("bubble-a", "trim me");
  const savePromise = actions.onSave();

  actions.onBubbleTextEditedChange("bubble-a", "trim me ");

  resolveSave({
    frameId: "frame-001",
    image: "images/001.png",
    ocrFile: "ocr/001.json",
    bubbles: [
      {
        id: "bubble-a",
        text: "raw line",
        bbox: { x: 0, y: 0, w: 10, h: 10 },
        order: 0,
        confidence: 0.9,
        language: "ja",
      },
    ],
    reviewedBubbles: [
      {
        id: "review-a",
        sourceBubbleId: "bubble-a",
        textOriginal: "raw line",
        textEdited: "saved on server",
        order: 0,
        kind: "dialogue",
        speaker: undefined,
      },
    ],
  });

  await savePromise;

  assert.equal(currentState.frame.reviewedBubbles[0]?.textEdited, "saved on server");
  assert.equal(currentState.draft.bubbles[0]?.textEdited, "trim me ");
});

test("frame review page keeps newer local edits when an earlier save fails", async () => {
  let rejectSave;
  const page = await loadFrameReviewPage({
    api: {
      getFrames: async () => [
        {
          frameId: "frame-001",
          image: "images/001.png",
          ocrFile: "ocr/001.json",
          bubbles: [
            {
              id: "bubble-a",
              text: "raw line",
              bbox: { x: 0, y: 0, w: 10, h: 10 },
              order: 0,
              confidence: 0.9,
              language: "ja",
            },
          ],
          reviewedBubbles: [],
        },
      ],
    },
    projectId: "demo-001",
    frameId: "frame-001",
  });

  let currentState = page;
  const actions = createFrameReviewPageActions({
    api: {
      updateFrameReview: async () =>
        await new Promise((_, reject) => {
          rejectSave = reject;
        }),
    },
    projectId: "demo-001",
    frameId: "frame-001",
    getState: () => currentState,
    onStateChange: (nextState) => {
      currentState = nextState;
    },
  });

  actions.onBubbleTextEditedChange("bubble-a", "save me");
  const savePromise = actions.onSave();

  assert.equal(currentState.isSaving, true);

  actions.onBubbleTextEditedChange("bubble-a", "newer local draft");
  rejectSave(new Error("frame save failed"));

  await savePromise;

  assert.equal(currentState.isSaving, false);
  assert.equal(currentState.errorMessage, "frame save failed");
  assert.equal(currentState.saveMessage, null);
  assert.equal(currentState.draft.bubbles[0]?.textEdited, "newer local draft");
});

test("frame review page renders input and save callbacks when actions are provided", () => {
  const events = [];
  const tree = FrameReviewPage({
    frame: { frameId: "frame-001" },
    draft: {
      frameId: "frame-001",
      bubbles: [
        {
          sourceBubbleId: "bubble-a",
          textEdited: "draft line",
          order: 1,
          kind: "narration",
          speaker: "Narrator",
        },
      ],
    },
    actions: {
      onBubbleTextEditedChange: (bubbleId, value) => events.push(["text", bubbleId, value]),
      onBubbleOrderChange: (bubbleId, value) => events.push(["order", bubbleId, value]),
      onBubbleKindChange: (bubbleId, value) => events.push(["kind", bubbleId, value]),
      onBubbleSpeakerChange: (bubbleId, value) => events.push(["speaker", bubbleId, value]),
      onSave: () => events.push(["save"]),
    },
  });

  const textarea = findElement(
    tree,
    (node) => node.type === "textarea" && node.props?.name === "textEdited-bubble-a"
  );
  const orderInput = findElement(
    tree,
    (node) => node.type === "input" && node.props?.name === "order-bubble-a"
  );
  const kindSelect = findElement(
    tree,
    (node) => node.type === "select" && node.props?.name === "kind-bubble-a"
  );
  const speakerInput = findElement(
    tree,
    (node) => node.type === "input" && node.props?.name === "speaker-bubble-a"
  );
  const saveButton = findElement(tree, (node) => node.type === "button");

  assert.equal(textarea.props.value, "draft line");
  assert.equal(textarea.props.defaultValue, undefined);
  assert.equal(orderInput.props.value, 1);
  assert.equal(orderInput.props.defaultValue, undefined);
  assert.equal(kindSelect.props.value, "narration");
  assert.equal(kindSelect.props.defaultValue, undefined);
  assert.equal(speakerInput.props.value, "Narrator");
  assert.equal(speakerInput.props.defaultValue, undefined);

  textarea.props.onChange({ target: { value: "edited in ui" } });
  orderInput.props.onChange({ target: { value: "3" } });
  kindSelect.props.onChange({ target: { value: "dialogue" } });
  speakerInput.props.onChange({ target: { value: "Hero" } });
  saveButton.props.onClick();

  assert.deepEqual(events, [
    ["text", "bubble-a", "edited in ui"],
    ["order", "bubble-a", "3"],
    ["kind", "bubble-a", "dialogue"],
    ["speaker", "bubble-a", "Hero"],
    ["save"],
  ]);
});

test("frame review page renders invalid bubble order values as an empty input", () => {
  const tree = FrameReviewPage({
    frame: { frameId: "frame-001" },
    draft: {
      frameId: "frame-001",
      bubbles: [
        {
          sourceBubbleId: "bubble-a",
          textEdited: "draft line",
          order: Number.NaN,
          kind: "dialogue",
          speaker: "Hero",
        },
      ],
    },
    validationErrors: {
      "bubble-a": {
        order: "Order must be a non-negative integer.",
      },
    },
  });

  const orderInput = findElement(
    tree,
    (node) => node.type === "input" && node.props?.name === "order-bubble-a"
  );

  assert.equal(orderInput.props.value, "");
});
