type ElementType = string | ((...args: any[]) => unknown);
type ElementProps = Record<string, unknown> | null | undefined;

function fallbackCreateElement(type: ElementType, props: ElementProps, ...children: unknown[]) {
  return {
    type,
    props: {
      ...(props ?? {}),
      children,
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
