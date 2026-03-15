import React from "react";

import { App } from "../App.tsx";
import { buildReviewAppSearch, readInitialReviewAppConfig, sanitizeReviewAppConfig } from "./config.ts";
import { loadReviewShell } from "./runtime.ts";

const h = React.createElement;

export function ReviewApp({
  env = globalThis?.window?.__MANGA_REVIEW_ENV__ ?? {},
  location = globalThis?.window?.location ?? { pathname: "/", search: "" },
  history = globalThis?.window?.history ?? null,
}) {
  const initialConfig = readInitialReviewAppConfig({ env, search: location.search });
  const [config, setConfig] = React.useState(initialConfig);
  const [requestedConfig, setRequestedConfig] = React.useState(
    initialConfig.projectId ? initialConfig : null
  );
  const [status, setStatus] = React.useState(initialConfig.projectId ? "loading" : "idle");
  const [errorMessage, setErrorMessage] = React.useState(null);
  const [shellData, setShellData] = React.useState(null);

  React.useEffect(() => {
    if (!requestedConfig) {
      setShellData(null);
      return;
    }

    let cancelled = false;
    setStatus("loading");
    setErrorMessage(null);

    loadReviewShell({ config: requestedConfig })
      .then((loaded) => {
        if (cancelled) {
          return;
        }

        setShellData(loaded);
        setStatus("loaded");
      })
      .catch((error) => {
        if (cancelled) {
          return;
        }

        setShellData(null);
        setStatus("error");
        setErrorMessage(error instanceof Error ? error.message : String(error));
      });

    return () => {
      cancelled = true;
    };
  }, [requestedConfig]);

  React.useEffect(() => {
    if (!history?.replaceState || !location?.pathname) {
      return;
    }

    const nextSearch = buildReviewAppSearch(requestedConfig ?? {});
    history.replaceState(null, "", `${location.pathname}${nextSearch}`);
  }, [config, history, location.pathname, requestedConfig]);

  const shellElement = shellData ? h(App, shellData) : null;

  return h(ReviewAppView, {
    config,
    status,
    errorMessage,
    shellElement,
    onConfigChange(patch) {
      setConfig((current) =>
        sanitizeReviewAppConfig({
          ...current,
          ...patch,
        })
      );
    },
    onSubmit(event) {
      event?.preventDefault?.();

      const nextConfig = sanitizeReviewAppConfig(config);
      setConfig(nextConfig);

      if (!nextConfig.projectId) {
        setRequestedConfig(null);
        setShellData(null);
        setStatus("error");
        setErrorMessage("Project ID is required.");
        return;
      }

      setRequestedConfig(nextConfig);
    },
  });
}

export function ReviewAppView({
  config,
  status = "idle",
  errorMessage = null,
  shellElement = null,
  onConfigChange = () => {},
  onSubmit = () => {},
}) {
  return h(
    "main",
    { className: "review-runtime", "data-review-runtime": status },
    h(
      "section",
      { className: "review-runtime-controls" },
      h("h1", null, "Review app"),
      h(
        "form",
        { onSubmit },
        h("label", { htmlFor: "api-base-url" }, "API base URL"),
        h("input", {
          id: "api-base-url",
          name: "apiBaseUrl",
          type: "text",
          value: config.apiBaseUrl,
          placeholder: "http://127.0.0.1:8000",
          onChange(event) {
            onConfigChange({ apiBaseUrl: event.target.value });
          },
        }),
        h("label", { htmlFor: "project-id" }, "Project ID"),
        h("input", {
          id: "project-id",
          name: "projectId",
          type: "text",
          value: config.projectId,
          placeholder: "demo-001",
          onChange(event) {
            onConfigChange({ projectId: event.target.value });
          },
        }),
        h("label", { htmlFor: "frame-id" }, "Initial frame ID"),
        h("input", {
          id: "frame-id",
          name: "frameId",
          type: "text",
          value: config.frameId,
          placeholder: "frame-001",
          onChange(event) {
            onConfigChange({ frameId: event.target.value });
          },
        }),
        h("label", { htmlFor: "active-job-id" }, "Active render job ID"),
        h("input", {
          id: "active-job-id",
          name: "activeJobId",
          type: "text",
          value: config.activeJobId,
          placeholder: "render-preview-001",
          onChange(event) {
            onConfigChange({ activeJobId: event.target.value });
          },
        }),
        h("button", { type: "submit" }, "Load project")
      ),
      h(
        "p",
        { "data-review-runtime-state": status },
        renderRuntimeMessage(status, errorMessage)
      )
    ),
    shellElement
      ? h(
          "section",
          { className: "review-runtime-shell", "data-review-shell-root": "true" },
          shellElement
        )
      : null
  );
}

function renderRuntimeMessage(status, errorMessage) {
  if (status === "loading") {
    return "Loading project review shell...";
  }

  if (status === "error") {
    return errorMessage ?? "Project load failed.";
  }

  if (status === "loaded") {
    return "Project review shell loaded.";
  }

  return "Enter a project ID to load the review app.";
}
