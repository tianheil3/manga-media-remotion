export function findElement(node, predicate) {
  if (Array.isArray(node)) {
    for (const child of node) {
      const match = findElement(child, predicate);
      if (match) {
        return match;
      }
    }

    return null;
  }

  if (!node || typeof node !== "object") {
    return null;
  }

  if (predicate(node)) {
    return node;
  }

  return findElement(node.props?.children, predicate);
}
