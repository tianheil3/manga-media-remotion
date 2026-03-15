import test from "node:test";
import assert from "node:assert/strict";

import React from "react";
import { renderToStaticMarkup } from "react-dom/server";

test("react shim preserves single-child semantics on props.children", () => {
  const tree = React.createElement(
    "section",
    null,
    React.createElement("p", null, "only child")
  );

  assert.equal(Array.isArray(tree.props.children), false);
  assert.equal(tree.props.children.type, "p");
});

test("react shim preserves props.children when no variadic children are passed", () => {
  const tree = React.createElement("section", {
    children: React.createElement("p", null, "from props"),
  });

  assert.equal(Array.isArray(tree.props.children), false);
  assert.equal(tree.props.children.type, "p");
});

test("react shim supports useState and no-op useEffect during static rendering", () => {
  const markup = renderToStaticMarkup(
    React.createElement(function HookedComponent() {
      const [message] = React.useState("ready");
      React.useEffect(() => {
        throw new Error("useEffect should not run during static rendering");
      }, []);

      return React.createElement("p", null, message);
    })
  );

  assert.match(markup, /ready/);
});
