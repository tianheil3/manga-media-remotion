function flattenChildren(children, output) {
  for (const child of children) {
    if (Array.isArray(child)) {
      flattenChildren(child, output);
      continue;
    }

    output.push(child);
  }
}

export const Fragment = Symbol.for("react.fragment");

export function createElement(type, props, ...children) {
  const normalizedChildren = [];
  flattenChildren(children, normalizedChildren);

  return {
    type,
    props: {
      ...(props ?? {}),
      children: normalizedChildren,
    },
  };
}

const React = {
  Fragment,
  createElement,
};

export default React;
