import { describe, expect, it } from "vitest";
import { ApiClientError } from "@rpg/bridge";

import { extractValidationErrorMap, getFieldErrors } from "./validationErrorMap";

describe("validationErrorMap", () => {
  it("maps structured field_errors to field messages", () => {
    const error = new ApiClientError(400, "Bad Request", {
      error: "VALIDATION_FAILED",
      message: {
        summary: "Validation failed",
        field_errors: {
          armor_class: [{ type: "int_parsing", msg: "Input should be a valid integer" }],
          "modifier_specs.0.value": [{ type: "int_parsing", msg: "Input should be a valid integer" }],
        },
      },
    });

    const map = extractValidationErrorMap(error);
    expect(map.armor_class).toEqual(["Input should be a valid integer"]);
    expect(map["modifier_specs.0.value"]).toEqual(["Input should be a valid integer"]);
  });

  it("returns root error for string validation messages", () => {
    const error = new ApiClientError(400, "Bad Request", {
      error: "VALIDATION_FAILED",
      message: "Something is invalid",
    });

    const map = extractValidationErrorMap(error);
    expect(map.__root__).toEqual(["Something is invalid"]);
  });

  it("ignores non-validation errors", () => {
    const error = new ApiClientError(409, "Conflict", {
      error: "VERSION_MISMATCH",
      message: "Version mismatch",
    });

    const map = extractValidationErrorMap(error);
    expect(map).toEqual({});
    expect(getFieldErrors(map, "armor_class")).toEqual([]);
  });
});
