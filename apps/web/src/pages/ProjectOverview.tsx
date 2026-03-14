import React from "react";

import { buildProjectWorkflowSummary } from "../lib/workflow.ts";

const h = React.createElement;

export function ProjectOverviewPage({ project }) {
  const summary = buildProjectWorkflowSummary(project);

  return h(
    "section",
    { className: "project-overview", "data-page": "project-overview" },
    h("h2", null, "Workflow overview"),
    h("p", null, project.title),
    h(
      "ul",
      { "data-workflow-sections": "true" },
      ...summary.sections.map((section) =>
        h(
          "li",
          {
            key: section.key,
            "data-stage": section.key,
            "data-stage-status": section.done ? "done" : "pending",
          },
          h("strong", null, section.label),
          " ",
          h("span", null, `${section.count} items`),
          " ",
          h("span", null, section.done ? "Done" : section.actionLabel)
        )
      )
    ),
    h(
      "aside",
      { "data-next-stage": summary.nextStage.key },
      h("h3", null, "Next stage"),
      h("p", null, summary.nextStage.actionLabel)
    )
  );
}
