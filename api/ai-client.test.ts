import { describe, expect, it } from "vitest";
import { AiTransient, AiUnavailable, classifyAiError, mapAiError } from "./ai-client";

describe("AI failure classification", () => {
  it("recognizes the gateway's real quota-exhaustion response", () => {
    const error = mapAiError(403, { error: { type: "access_terminated_error" } }, "");
    expect(error).toBeInstanceOf(AiUnavailable);
    expect(error.message).toContain("额度耗尽");
  });

  it("does not downgrade a raw 403 response body to a content rejection", () => {
    const responseBody = JSON.stringify({ error: { type: "access_terminated_error", message: "quota exhausted" } });
    const error = classifyAiError({ status: 403, responseBody });
    expect(error).toBeInstanceOf(AiUnavailable);
  });

  it("classifies unstructured network failures as transient without retrying", () => {
    expect(classifyAiError(new Error("connection reset"))).toBeInstanceOf(AiTransient);
  });
});
