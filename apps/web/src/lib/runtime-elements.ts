type ElementType = string | ((...args: any[]) => unknown);
type ElementProps = Record<string, unknown> | null | undefined;

function normalizeChildren(children: unknown[]) {
  if (children.length === 0) {
    return undefined;
  }

  if (children.length === 1) {
    return children[0];
  }

  return children;
}

function fallbackCreateElement(type: ElementType, props: ElementProps, ...children: unknown[]) {
  return {
    type,
    props: {
      ...(props ?? {}),
      children: normalizeChildren(children),
    },
  };
}

let createElement = fallbackCreateElement;

try {
  const reactModule = await import("react");
  createElement = reactModule.default.createElement;
} catch {
  createElement = fallbackCreateElement;
}

export const h = createElement;
