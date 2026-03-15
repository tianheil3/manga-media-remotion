import { Fragment } from "./react.mjs";

export function renderToStaticMarkup(node) {
  return renderNode(node);
}

function renderNode(node) {
  if (node === null || node === undefined || node === false || node === true) {
    return "";
  }

  if (Array.isArray(node)) {
    return node.map(renderNode).join("");
  }

  if (typeof node === "string" || typeof node === "number") {
    return escapeHtml(String(node));
  }

  if (typeof node.type === "function") {
    return renderNode(node.type(node.props ?? {}));
  }

  if (node.type === Fragment) {
    return renderChildren(node.props?.children);
  }

  if (typeof node.type !== "string") {
    throw new TypeError(`Unsupported React element type: ${String(node.type)}`);
  }

  const attributes = renderAttributes(node.props ?? {});
  const children = renderChildren(node.props?.children);

  return `<${node.type}${attributes}>${children}</${node.type}>`;
}

function renderChildren(children) {
  if (!children) {
    return "";
  }

  return renderNode(children);
}

function renderAttributes(props) {
  const attributes = [];

  for (const [name, value] of Object.entries(props)) {
    if (name === "children" || name === "key" || value === null || value === undefined) {
      continue;
    }
    if (typeof value === "function" || value === false) {
      continue;
    }

    const attributeName = name === "className" ? "class" : name;
    if (value === true) {
      attributes.push(` ${attributeName}`);
      continue;
    }

    attributes.push(` ${attributeName}="${escapeHtml(String(value))}"`);
  }

  return attributes.join("");
}

function escapeHtml(value) {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}
