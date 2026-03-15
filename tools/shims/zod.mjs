class ZodType {
  constructor() {
    this._optional = false;
    this._nullable = false;
    this._hasDefault = false;
    this._defaultValue = undefined;
  }

  parse(value) {
    if (value === undefined) {
      if (this._hasDefault) {
        return this._defaultValue;
      }
      if (this._optional) {
        return undefined;
      }
      throw new TypeError("Expected value, received undefined");
    }

    if (value === null) {
      if (this._nullable) {
        return null;
      }
      throw new TypeError("Expected value, received null");
    }

    return this._parse(value);
  }

  optional() {
    return this._clone({ _optional: true });
  }

  nullable() {
    return this._clone({ _nullable: true });
  }

  nullish() {
    return this.nullable().optional();
  }

  default(value) {
    return this._clone({
      _defaultValue: value,
      _hasDefault: true,
    });
  }

  array() {
    return new ZodArray(this);
  }

  _clone(overrides = {}) {
    const clone = Object.assign(Object.create(Object.getPrototypeOf(this)), this);
    return Object.assign(clone, overrides);
  }
}

class ZodString extends ZodType {
  constructor() {
    super();
    this._min = null;
    this._datetime = false;
  }

  _parse(value) {
    if (typeof value !== "string") {
      throw new TypeError(`Expected string, received ${typeof value}`);
    }
    if (this._min !== null && value.length < this._min) {
      throw new RangeError(`Expected string length >= ${this._min}`);
    }
    if (this._datetime && Number.isNaN(Date.parse(value))) {
      throw new TypeError("Expected ISO datetime string");
    }
    return value;
  }

  min(length) {
    return this._clone({ _min: length });
  }

  datetime() {
    return this._clone({ _datetime: true });
  }
}

class ZodNumber extends ZodType {
  constructor() {
    super();
    this._checks = [];
  }

  _parse(value) {
    if (typeof value !== "number" || Number.isNaN(value)) {
      throw new TypeError(`Expected number, received ${typeof value}`);
    }
    for (const check of this._checks) {
      check(value);
    }
    return value;
  }

  _withCheck(check) {
    return this._clone({ _checks: [...this._checks, check] });
  }

  min(minimum) {
    return this._withCheck((value) => {
      if (value < minimum) {
        throw new RangeError(`Expected number >= ${minimum}`);
      }
    });
  }

  max(maximum) {
    return this._withCheck((value) => {
      if (value > maximum) {
        throw new RangeError(`Expected number <= ${maximum}`);
      }
    });
  }

  int() {
    return this._withCheck((value) => {
      if (!Number.isInteger(value)) {
        throw new TypeError("Expected integer");
      }
    });
  }

  nonnegative() {
    return this.min(0);
  }

  positive() {
    return this._withCheck((value) => {
      if (value <= 0) {
        throw new RangeError("Expected positive number");
      }
    });
  }
}

class ZodEnum extends ZodType {
  constructor(values) {
    super();
    this._values = [...values];
  }

  _parse(value) {
    if (!this._values.includes(value)) {
      throw new TypeError(`Expected one of ${this._values.join(", ")}`);
    }
    return value;
  }
}

class ZodBoolean extends ZodType {
  _parse(value) {
    if (typeof value !== "boolean") {
      throw new TypeError(`Expected boolean, received ${typeof value}`);
    }
    return value;
  }
}

class ZodArray extends ZodType {
  constructor(itemSchema) {
    super();
    this._itemSchema = itemSchema;
  }

  _parse(value) {
    if (!Array.isArray(value)) {
      throw new TypeError("Expected array");
    }

    return value.map((item) => this._itemSchema.parse(item));
  }
}

class ZodObject extends ZodType {
  constructor(shape) {
    super();
    this.shape = { ...shape };
  }

  _parse(value) {
    if (typeof value !== "object" || value === null || Array.isArray(value)) {
      throw new TypeError("Expected object");
    }

    const output = {};
    const errors = [];
    for (const [key, schema] of Object.entries(this.shape)) {
      let parsedValue;
      try {
        parsedValue = schema.parse(value[key]);
      } catch (error) {
        const message = error instanceof Error ? error.message : String(error);
        errors.push(`${key}: ${message}`);
        continue;
      }
      if (parsedValue !== undefined) {
        output[key] = parsedValue;
      }
    }

    if (errors.length > 0) {
      throw new TypeError(errors.join("; "));
    }
    return output;
  }

  extend(extraShape) {
    return new ZodObject({
      ...this.shape,
      ...extraShape,
    });
  }

  omit(keys) {
    const nextShape = { ...this.shape };
    for (const [key, shouldOmit] of Object.entries(keys)) {
      if (shouldOmit) {
        delete nextShape[key];
      }
    }
    return new ZodObject(nextShape);
  }
}

export const z = {
  boolean: () => new ZodBoolean(),
  string: () => new ZodString(),
  number: () => new ZodNumber(),
  enum: (values) => new ZodEnum(values),
  array: (schema) => new ZodArray(schema),
  object: (shape) => new ZodObject(shape),
};

export default { z };
