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
  const normalizedProps = { ...(props ?? {}) };

  if (normalizedChildren.length === 1) {
    normalizedProps.children = normalizedChildren[0];
  } else if (normalizedChildren.length > 1) {
    normalizedProps.children = normalizedChildren;
  }

  return {
    type,
    props: normalizedProps,
  };
}

export function useState(initialValue) {
  const value = typeof initialValue === "function" ? initialValue() : initialValue;
  return [value, () => {}];
}

export function useEffect() {}

const React = {
  Fragment,
  createElement,
  useEffect,
  useState,
};

export default React;
