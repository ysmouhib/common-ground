// End-to-end checks against a running production build (npm run build && npm start,
// or the container image). Nothing is mocked: real HTTP, the real database, a real
// browser. Run with `npm run e2e`.
//
//   E2E_BASE_URL        where the server listens            (default http://127.0.0.1:3000)
//   E2E_REVIEWER_TOKEN  the server's REVIEWER_TOKEN         (required unless E2E_READ_ONLY=1)
//   E2E_EXPECT_LEAN     1: the server must have Lean, 0: it must not, unset: either is accepted
//   E2E_BROWSER         0 skips the browser part
//   E2E_READ_ONLY       1: the server was started without a reviewer token; check that
//                       nothing can be changed, with or without a token
//
// The abuse-limit checks send their traffic from 127.0.0.2 and 127.0.0.3, so the
// limits they trip do not lock out the address the other checks use. That needs the
// whole 127.0.0.0/8 block on the loopback interface, which Linux provides.
//
// The last check locks out the address the checks themselves run from, to see the
// message a locked-out reviewer gets. Restart the server before running them again.
import assert from "node:assert/strict";
import http from "node:http";
import https from "node:https";
import { createRequire } from "node:module";

const BASE = new URL(process.env.E2E_BASE_URL ?? "http://127.0.0.1:3000");
const TOKEN = process.env.E2E_REVIEWER_TOKEN ?? "";
const EXPECT_LEAN = process.env.E2E_EXPECT_LEAN;
const WITH_BROWSER = process.env.E2E_BROWSER !== "0";
const READ_ONLY = process.env.E2E_READ_ONLY === "1";
const STRICT = process.env.CI === "true"; // in CI nothing may be skipped
const WRONG_TOKEN = "e2e-wrong-token-that-is-long-enough-000";
const PREMISE = "A3"; // a premise of the advocate's certificate and of the combined one

if (!READ_ONLY && TOKEN.length < 24) {
  console.error("E2E_REVIEWER_TOKEN must be the server's reviewer token (at least 24 characters).");
  process.exit(2);
}

// ------------------------------------------------------------------ plumbing

function request(path, { method = "GET", headers = {}, body, from } = {}) {
  return new Promise((resolve, reject) => {
    const lib = BASE.protocol === "https:" ? https : http;
    const req = lib.request(
      // `path` is sent as written, so encoded traversal sequences reach the server untouched.
      { host: BASE.hostname, port: BASE.port, path, method, headers, localAddress: from, agent: false },
      (res) => {
        const chunks = [];
        res.on("data", (chunk) => chunks.push(chunk));
        res.on("end", () => resolve({ status: res.statusCode, headers: res.headers, text: Buffer.concat(chunks).toString("utf8") }));
      },
    );
    req.on("error", reject);
    req.setTimeout(180_000, () => req.destroy(new Error(`timeout: ${method} ${path}`)));
    if (body !== undefined) req.write(body);
    req.end();
  });
}

/** One tRPC call. Returns { status, data } on success and { status, code, message } on a tRPC error. */
async function call(procedure, { input, token, from, mutation = false } = {}) {
  const headers = {};
  if (token) headers.authorization = `Bearer ${token}`;
  let res;
  if (mutation) {
    headers["content-type"] = "application/json";
    res = await request(`/api/trpc/${procedure}`, { method: "POST", headers, from, body: JSON.stringify(input === undefined ? {} : { json: input }) });
  } else {
    res = await request(`/api/trpc/${procedure}`, { headers, from });
  }
  let parsed;
  try {
    parsed = JSON.parse(res.text);
  } catch {
    return { status: res.status, headers: res.headers, raw: res.text };
  }
  if (parsed.error) {
    const error = parsed.error.json ?? parsed.error;
    return { status: res.status, headers: res.headers, code: error.data?.code, message: error.message };
  }
  return { status: res.status, headers: res.headers, data: parsed.result?.data?.json };
}

const workspace = async (options = {}) => {
  const res = await call("workspace.get", options);
  assert.equal(res.status, 200, `workspace.get answered ${res.status}`);
  return res.data;
};

const review = (status, note, options = {}) =>
  call("workspace.setStatementStatus", { mutation: true, input: { statementId: PREMISE, status, note }, ...options });

let passed = 0;
const failures = [];
const skipped = [];

async function check(name, run) {
  try {
    await run();
    passed += 1;
    console.log(`  ok    ${name}`);
  } catch (error) {
    failures.push(name);
    console.log(`  FAIL  ${name}\n        ${String(error?.message ?? error).split("\n").join("\n        ")}`);
  }
}

/** Outside CI a check that cannot run here is reported as skipped; in CI that is a failure. */
function skip(name, reason, { allowedInCi = false } = {}) {
  if (STRICT && !allowedInCi) {
    failures.push(name);
    console.log(`  FAIL  ${name}: ${reason}`);
    return;
  }
  skipped.push(name);
  console.log(`  skip  ${name} (${reason})`);
}

function loadChromium() {
  try {
    return createRequire(import.meta.url)("playwright").chromium;
  } catch {
    return null;
  }
}

/** Can this machine send from the given loopback address? */
async function canSendFrom(address) {
  try {
    await request("/api/trpc/ping", { from: address });
    return true;
  } catch (error) {
    if (["EADDRNOTAVAIL", "EINVAL"].includes(error?.code)) return false;
    throw error;
  }
}

// ------------------------------------------------------------------ HTTP checks

async function pageAndHeaders() {
  console.log("\nPage and response headers");
  await check("the page is served with a policy that allows no inline or third-party script", async () => {
    const res = await request("/");
    assert.equal(res.status, 200);
    assert.match(res.headers["content-type"], /text\/html/);
    const csp = res.headers["content-security-policy"] ?? "";
    for (const directive of ["default-src 'self'", "script-src 'self'", "object-src 'none'", "frame-ancestors 'none'", "base-uri 'self'"]) {
      assert.ok(csp.includes(directive), `Content-Security-Policy lacks "${directive}": ${csp}`);
    }
    assert.doesNotMatch(csp, /script-src[^;]*(unsafe-inline|unsafe-eval|https?:|\*)/);
    assert.equal(res.headers["x-content-type-options"], "nosniff");
    assert.equal(res.headers["x-frame-options"], "DENY");
    assert.equal(res.headers["referrer-policy"], "no-referrer");
  });
  await check("API answers are never cached and carry the same policy", async () => {
    const res = await request("/api/trpc/ping");
    assert.equal(res.status, 200);
    assert.equal(res.headers["cache-control"], "no-store");
    assert.ok(res.headers["content-security-policy"]);
  });
  await check("an unknown API path is a 404, not the page", async () => {
    const res = await request("/api/does-not-exist");
    assert.equal(res.status, 404);
    assert.match(res.headers["content-type"], /application\/json/);
  });
  await check("encoded path traversal returns no file from outside the public folder", async () => {
    for (const path of ["/..%2f..%2fpackage.json", "/assets/..%2f..%2f..%2fpackage.json", "/%2e%2e/%2e%2e/etc/passwd", "/assets/%2e%2e%2f%2e%2e%2fboot.js", "/..%5c..%5cpackage.json"]) {
      const res = await request(path);
      assert.ok(!res.text.includes("root:x:0:0"), `${path} returned /etc/passwd`);
      assert.ok(!res.text.includes('"drizzle-orm"'), `${path} returned package.json`);
      assert.ok(!res.text.includes("REVIEWER_TOKEN"), `${path} returned server code`);
    }
  });
}

async function readAccess() {
  console.log("\nReading is public");
  await check("an anonymous visitor gets the whole worked example", async () => {
    const data = await workspace();
    assert.equal(data.statements.length, 15);
    assert.equal(data.evidence.length, 5);
    assert.equal(data.proofs.length, 5);
    assert.deepEqual(data.access, { reviewEnabled: true, isReviewer: false, lockedOut: false });
    for (const record of data.evidence) {
      assert.match(record.url, /^https:\/\//);
      assert.ok(record.excerpt.length > 20);
    }
  });
  await check("the database is in its seeded state: four active certificates, no dispute, positions compatible", async () => {
    const { analysis, proofs } = await workspace();
    assert.equal(analysis.disputedCount, 0, `a statement is disputed; restore it before running these checks`);
    assert.equal(analysis.activeProofCount, 4);
    assert.equal(analysis.positionsCompatible, true);
    assert.deepEqual(analysis.conflicts, []);
    assert.deepEqual(analysis.minimalConcessions, []);
    assert.equal(proofs.filter((proof) => proof.isNegativeControl).length, 1);
    assert.equal(proofs.find((proof) => proof.isNegativeControl).active, false);
  });
}

async function accessControl() {
  console.log("\nEverything that costs or changes something needs the reviewer token");
  const mutations = [
    ["workspace.setStatementStatus", { statementId: PREMISE, status: "disputed", note: "e2e anonymous attempt" }],
    ["proof.verify", { proofId: "proof-advocate" }],
    ["proof.verifyAll", undefined],
    ["ai.critiqueFormalization", { statementId: PREMISE }],
  ];
  for (const [procedure, input] of mutations) {
    await check(`${procedure} is refused without a token`, async () => {
      const res = await call(procedure, { mutation: true, input });
      assert.equal(res.status, 401);
      assert.equal(res.code, "UNAUTHORIZED");
    });
  }
  await check("the three encodings an HTML form can send are refused, even with the right token", async () => {
    // A page on another site can make a browser send these without asking the server first.
    const forms = [
      ["application/x-www-form-urlencoded", `statementId=${PREMISE}&status=disputed&note=e2e+form+post`],
      ["text/plain", JSON.stringify({ json: { statementId: PREMISE, status: "disputed", note: "e2e form post" } })],
      ["multipart/form-data; boundary=e2e", `--e2e\r\ncontent-disposition: form-data; name="statementId"\r\n\r\n${PREMISE}\r\n--e2e\r\ncontent-disposition: form-data; name="status"\r\n\r\ndisputed\r\n--e2e\r\ncontent-disposition: form-data; name="note"\r\n\r\ne2e form post\r\n--e2e--\r\n`],
    ];
    for (const [type, body] of forms) {
      const res = await request("/api/trpc/workspace.setStatementStatus", {
        method: "POST",
        headers: { "content-type": type, authorization: `Bearer ${TOKEN}` },
        body,
      });
      assert.ok([400, 415].includes(res.status), `${type} was answered with ${res.status}`);
    }
  });
  await check("nothing was changed by the refused requests", async () => {
    const { analysis, reviewEvents } = await workspace();
    assert.equal(analysis.disputedCount, 0);
    assert.ok(!reviewEvents.some((event) => /e2e (anonymous attempt|form post)/.test(event.note)));
  });
  await check("the right token is recognised", async () => {
    assert.equal((await workspace({ token: TOKEN })).access.isReviewer, true);
  });
}

async function reviewFlow() {
  console.log("\nA review decision changes what is certified");
  const stamp = `e2e ${new Date().toISOString()}`;
  let disputed = false;
  try {
    await check("disputing a premise suspends exactly the certificates that use it", async () => {
      const before = await workspace();
      const dependent = before.proofs.filter((proof) => proof.premiseIds.includes(PREMISE) && proof.active).map((proof) => proof.id);
      assert.ok(dependent.length >= 1, `no active certificate uses ${PREMISE}`);
      const res = await review("disputed", `${stamp} dispute`, { token: TOKEN });
      assert.equal(res.status, 200, res.message);
      disputed = true;
      const after = await workspace();
      assert.equal(after.statements.find((statement) => statement.id === PREMISE).approvalStatus, "disputed");
      assert.equal(after.analysis.disputedCount, 1);
      assert.equal(after.analysis.activeProofCount, before.analysis.activeProofCount - dependent.length);
      assert.equal(after.analysis.disagreementKind, "premises_under_review");
      for (const proof of after.proofs) {
        const expected = proof.isNegativeControl ? false : !dependent.includes(proof.id);
        assert.equal(proof.active, expected, `${proof.id} active=${proof.active}`);
        if (dependent.includes(proof.id)) assert.ok(proof.missingPremiseIds.includes(PREMISE));
      }
    });
    await check("the decision is recorded with the time it was made", async () => {
      const { reviewEvents } = await workspace();
      const event = reviewEvents.find((item) => item.note === `${stamp} dispute`);
      assert.ok(event, "no review event with this run's note");
      assert.equal(event.statementId, PREMISE);
      assert.equal(event.action, "disputed");
      const drift = Math.abs(Date.parse(event.createdAt) - Date.now());
      assert.ok(drift < 120_000, `recorded time is ${Math.round(drift / 1000)} s away from now (${event.createdAt})`);
    });
  } finally {
    if (disputed) {
      await check("approving it again restores them", async () => {
        const res = await review("approved", `${stamp} restore`, { token: TOKEN });
        assert.equal(res.status, 200, res.message);
        const { analysis } = await workspace();
        assert.equal(analysis.disputedCount, 0);
        assert.equal(analysis.activeProofCount, 4);
      });
    }
  }
  await check("malformed decisions are rejected and unknown statements are not found", async () => {
    assert.equal((await review("approved", "x", { token: TOKEN })).code, "BAD_REQUEST");
    assert.equal((await review("certified", "e2e invalid status", { token: TOKEN })).code, "BAD_REQUEST");
    const unknown = await call("workspace.setStatementStatus", { mutation: true, token: TOKEN, input: { statementId: "ZZ9", status: "approved", note: "e2e unknown statement" } });
    assert.equal(unknown.code, "NOT_FOUND");
  });
}

async function leanRuns() {
  console.log("\nLean");
  await check("a verification batch reports what Lean did, or that there is no Lean here; it never invents a result", async () => {
    const res = await call("proof.verifyAll", { mutation: true, token: TOKEN });
    assert.equal(res.status, 200, res.message);
    assert.equal(res.data.length, 5);
    const unfinished = res.data.filter((result) => result.timedOut).map((result) => result.proofId);
    assert.deepEqual(unfinished, [], "Lean did not finish these runs in time; a first run after a cold start can be slow, so run the checks again");
    const live = res.data.filter((result) => result.runtimeAvailable).length;
    assert.ok(live === 0 || live === 5, `${live} of 5 results claim a live run`);
    if (EXPECT_LEAN === "1") assert.equal(live, 5, "this server was expected to have Lean");
    if (EXPECT_LEAN === "0") assert.equal(live, 0, "this server was expected to have no Lean");
    const control = res.data.find((result) => result.proofId === "negative-overreach");
    if (live === 5) {
      for (const result of res.data) assert.equal(result.expectedOutcome, true, `${result.proofId}: unexpected outcome`);
      assert.equal(control.accepted, false, "Lean accepted the invalid inference");
      assert.equal(res.data.filter((result) => result.accepted).length, 4);
      console.log("        Lean ran: 4 proofs accepted, the negative control rejected");
    } else {
      for (const result of res.data) assert.equal(result.accepted, false);
      console.log("        no Lean on this server: stored certificates left unchanged");
    }
    const { analysis } = await workspace();
    assert.equal(analysis.activeProofCount, 4);
    assert.equal(analysis.negativeControlRejected, true);
  });
}

async function limits() {
  console.log("\nAbuse limits");
  await check("a batch of more than 10 calls is refused", async () => {
    const res = await request(`/api/trpc/${Array(11).fill("ping").join(",")}?batch=1&input=%7B%7D`);
    assert.equal(res.status, 400);
    const allowed = await request(`/api/trpc/${Array(10).fill("ping").join(",")}?batch=1&input=%7B%7D`);
    assert.equal(allowed.status, 200);
  });
  await check("a request body over 64 KB is refused", async () => {
    const res = await request("/api/trpc/workspace.setStatementStatus", {
      method: "POST",
      headers: { "content-type": "application/json", authorization: `Bearer ${TOKEN}` },
      body: JSON.stringify({ json: { statementId: PREMISE, status: "approved", note: "x".repeat(70_000) } }),
    });
    assert.equal(res.status, 413);
  });

  if (await canSendFrom("127.0.0.2")) {
    await check("ten wrong tokens lock a client out, on a public query too, and then even the right token is refused", async () => {
      for (let attempt = 0; attempt < 10; attempt += 1) {
        const data = await workspace({ token: WRONG_TOKEN, from: "127.0.0.2" });
        assert.equal(data.access.isReviewer, false);
      }
      const data = await workspace({ token: TOKEN, from: "127.0.0.2" });
      assert.deepEqual(data.access, { reviewEnabled: true, isReviewer: false, lockedOut: true });
      const res = await review("disputed", "e2e locked-out attempt", { token: TOKEN, from: "127.0.0.2" });
      assert.equal(res.status, 429);
      assert.equal(res.code, "TOO_MANY_REQUESTS");
      assert.equal((await workspace()).analysis.disputedCount, 0);
    });
    await check("the lockout is per client: another address still gets in with the right token", async () => {
      assert.equal((await workspace({ token: TOKEN })).access.isReviewer, true);
    });
  } else {
    skip("lockout checks", "cannot send from 127.0.0.2 on this machine");
  }

  if (await canSendFrom("127.0.0.3")) {
    await check("a client over 240 requests a minute gets 429 with Retry-After; other clients are unaffected", async () => {
      const statuses = [];
      let retryAfter;
      for (let round = 0; round < 10; round += 1) {
        const batch = await Promise.all(Array.from({ length: 25 }, () => request("/api/trpc/ping", { from: "127.0.0.3" })));
        for (const res of batch) {
          statuses.push(res.status);
          if (res.status === 429) retryAfter = res.headers["retry-after"];
        }
      }
      assert.ok(statuses.includes(429), "250 requests in a row were all accepted");
      assert.ok(statuses.filter((status) => status === 200).length <= 240);
      assert.ok(Number(retryAfter) >= 1, `Retry-After was ${retryAfter}`);
      assert.equal((await request("/api/trpc/ping")).status, 200);
    });
  } else {
    skip("rate-limit check", "cannot send from 127.0.0.3 on this machine");
  }
}

/** Runs last: it locks out the address every other check uses. */
async function lockedOutReviewer() {
  console.log("\nA locked-out reviewer is told why");
  await check("after ten wrong tokens the server refuses the right one from this address", async () => {
    for (let attempt = 0; attempt < 10; attempt += 1) await workspace({ token: WRONG_TOKEN });
    assert.deepEqual((await workspace({ token: TOKEN })).access, { reviewEnabled: true, isReviewer: false, lockedOut: true });
  });
  const chromium = WITH_BROWSER ? loadChromium() : null;
  if (!chromium) {
    skip("the lockout message in the browser", WITH_BROWSER ? "the playwright package is not installed" : "E2E_BROWSER=0", { allowedInCi: !WITH_BROWSER });
    return;
  }
  const browser = await chromium.launch();
  try {
    await check("the interface says so instead of calling the right token wrong, and keeps nothing", async () => {
      const page = await browser.newPage();
      await page.goto(BASE.href, { waitUntil: "networkidle" });
      await page.getByRole("button", { name: "Reviewer access" }).click();
      const alert = page.getByRole("dialog").getByRole("alert");
      await alert.waitFor();
      assert.match(await alert.innerText(), /^Too many wrong tokens/);
      await page.getByLabel("Reviewer token").fill(TOKEN);
      await page.getByRole("button", { name: "Unlock review" }).click();
      await page.getByRole("button", { name: "Unlock review" }).waitFor();
      assert.match(await alert.innerText(), /^Too many wrong tokens/);
      assert.equal(await page.evaluate(() => sessionStorage.getItem("common-ground.reviewer-token")), null);
      assert.equal(await page.getByRole("button", { name: "Reviewer: sign out" }).count(), 0);
    });
  } finally {
    await browser.close();
  }
}

// ------------------------------------------------------------------ a deployment without a token

async function readOnlyDeployment() {
  console.log("\nWithout a reviewer token the deployment is read-only");
  const tokens = [undefined, WRONG_TOKEN, TOKEN || "a-token-that-would-be-long-enough-0000"];
  await check("reading works and review is reported as switched off", async () => {
    const data = await workspace();
    assert.equal(data.statements.length, 15);
    assert.deepEqual(data.access, { reviewEnabled: false, isReviewer: false, lockedOut: false });
  });
  const mutations = [
    ["workspace.setStatementStatus", { statementId: PREMISE, status: "disputed", note: "e2e read-only attempt" }],
    ["proof.verify", { proofId: "proof-advocate" }],
    ["proof.verifyAll", undefined],
    ["ai.critiqueFormalization", { statementId: PREMISE }],
  ];
  for (const [procedure, input] of mutations) {
    await check(`${procedure} is refused whatever token is sent`, async () => {
      for (const token of tokens) {
        const res = await call(procedure, { mutation: true, input, token });
        assert.equal(res.status, 403);
        assert.equal(res.code, "FORBIDDEN");
      }
    });
  }
  await check("no token is ever accepted, so none can be guessed", async () => {
    for (const token of tokens.slice(1)) assert.equal((await workspace({ token })).access.isReviewer, false);
  });
  await check("nothing was changed", async () => {
    const { analysis, reviewEvents } = await workspace();
    assert.equal(analysis.disputedCount, 0);
    assert.ok(!reviewEvents.some((event) => event.note.includes("e2e read-only attempt")));
  });
  if (!WITH_BROWSER) return skip("read-only interface", "E2E_BROWSER=0", { allowedInCi: true });
  const chromium = loadChromium();
  if (!chromium) return skip("read-only interface", "the playwright package is not installed");
  const browser = await chromium.launch();
  try {
    await check("the interface says it is read-only and offers no way to sign in", async () => {
      const page = await browser.newPage();
      await page.goto(BASE.href, { waitUntil: "networkidle" });
      await page.getByText("Read-only deployment").waitFor();
      assert.equal(await page.getByRole("button", { name: "Reviewer access" }).count(), 0);
      await page.getByRole("button", { name: new RegExp(`^${PREMISE}\\b`) }).first().click();
      const dialog = page.getByRole("dialog");
      await dialog.getByText("This deployment is read-only").waitFor();
      for (const name of ["Approve", "Dispute", "Mark draft"]) {
        assert.equal(await dialog.getByRole("button", { name, exact: true }).isDisabled(), true, `${name} is enabled`);
      }
    });
  } finally {
    await browser.close();
  }
}

// ------------------------------------------------------------------ browser checks

async function browserChecks() {
  console.log("\nIn a browser, under the production Content-Security-Policy");
  const chromium = loadChromium();
  if (!chromium) return skip("browser checks", "the playwright package is not installed; E2E_BROWSER=0 silences this");
  const browser = await chromium.launch();
  const totals = async (page) => {
    const text = await page.getByRole("region", { name: "Workspace totals" }).innerText();
    const read = (label) => Number((text.match(new RegExp(`(\\d+)\\s*${label}`)) ?? [])[1]);
    return { active: read("Active certificates"), disputes: read("Open disputes") };
  };
  const openPremise = async (page) => {
    await page.getByRole("button", { name: new RegExp(`^${PREMISE}\\b`) }).first().click();
    const dialog = page.getByRole("dialog");
    await dialog.waitFor();
    return dialog;
  };
  try {
    const context = await browser.newContext({ viewport: { width: 1280, height: 900 } });
    const page = await context.newPage();
    const problems = [];
    page.on("console", (message) => {
      if (message.type() === "error") problems.push(`console error: ${message.text().slice(0, 300)}`);
    });
    page.on("pageerror", (error) => problems.push(`page error: ${String(error).slice(0, 300)}`));

    await check("the page renders the computed diagnosis with no script error and no policy violation", async () => {
      await page.goto(BASE.href, { waitUntil: "networkidle" });
      await page.getByRole("heading", { name: "A priority dispute, not a direct contradiction." }).waitFor();
      await page.getByText("Computed, not asserted").first().waitFor();
      assert.deepEqual(await totals(page), { active: 4, disputes: 0 });
      assert.deepEqual(problems, []);
    });
    await check("an anonymous visitor can read a statement but its review buttons are disabled", async () => {
      const dialog = await openPremise(page);
      for (const name of ["Approve", "Dispute", "Mark draft"]) {
        assert.equal(await dialog.getByRole("button", { name, exact: true }).isDisabled(), true, `${name} is enabled`);
      }
      await dialog.getByText("Unlock reviewer access").waitFor();
      await page.keyboard.press("Escape");
      await dialog.waitFor({ state: "hidden" });
    });
    await check("a wrong token is refused and not kept", async () => {
      await page.getByRole("button", { name: "Reviewer access" }).click();
      await page.getByLabel("Reviewer token").fill(WRONG_TOKEN);
      await page.getByRole("button", { name: "Unlock review" }).click();
      const alert = page.getByRole("alert");
      await alert.waitFor();
      assert.equal(await alert.innerText(), "That token was not accepted.");
      assert.equal(await page.evaluate(() => sessionStorage.getItem("common-ground.reviewer-token")), null);
    });
    await check("the right token unlocks review for this tab only", async () => {
      await page.getByLabel("Reviewer token").fill(TOKEN);
      await page.getByRole("button", { name: "Unlock review" }).click();
      await page.getByRole("button", { name: "Reviewer: sign out" }).waitFor();
      assert.equal(await page.evaluate(() => localStorage.length), 0, "something was written to localStorage");
      assert.equal((await context.cookies()).length, 0, "a cookie was set");
    });
    await check("disputing a premise in the interface suspends certificates, approving it restores them", async () => {
      let dialog = await openPremise(page);
      await dialog.getByLabel("Review note").fill("e2e browser: dispute");
      await dialog.getByRole("button", { name: "Dispute", exact: true }).click();
      await dialog.getByRole("status").filter({ hasText: "Review saved: disputed" }).waitFor();
      await page.keyboard.press("Escape");
      await dialog.waitFor({ state: "hidden" });
      await page.getByRole("region", { name: "Workspace totals" }).getByText("1", { exact: true }).first().waitFor();
      const during = await totals(page);
      assert.equal(during.disputes, 1);
      assert.ok(during.active < 4, `still ${during.active} active certificates`);

      dialog = await openPremise(page);
      await dialog.getByLabel("Review note").fill("e2e browser: restore");
      await dialog.getByRole("button", { name: "Approve", exact: true }).click();
      await dialog.getByRole("status").filter({ hasText: "Review saved: approved" }).waitFor();
      await page.keyboard.press("Escape");
      await dialog.waitFor({ state: "hidden" });
      await page.waitForFunction(() => /0\s*Open disputes/.test(document.querySelector('[aria-label="Workspace totals"]')?.textContent ?? ""));
      assert.deepEqual(await totals(page), { active: 4, disputes: 0 });
    });
    await check("signing out forgets the token", async () => {
      await page.getByRole("button", { name: "Reviewer: sign out" }).click();
      await page.getByRole("button", { name: "Reviewer access" }).waitFor();
      assert.equal(await page.evaluate(() => sessionStorage.getItem("common-ground.reviewer-token")), null);
    });
    await check("every view opens without an error", async () => {
      for (const name of ["Proof lab", "Evidence", "Method", "Debate"]) {
        await page.getByRole("navigation", { name: "Workspace views" }).getByRole("button", { name }).click();
        await page.locator("main").waitFor();
        assert.ok((await page.locator("main").innerText()).length > 200, `${name} view is empty`);
      }
      assert.deepEqual(problems, []);
    });
    await context.close();

    await check("the page fits a phone screen without sideways scrolling", async () => {
      const phone = await browser.newContext({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true });
      const small = await phone.newPage();
      await small.goto(BASE.href, { waitUntil: "networkidle" });
      await small.getByRole("region", { name: "Workspace totals" }).waitFor();
      const overflow = await small.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
      assert.ok(overflow <= 0, `the page is ${overflow}px wider than the screen`);
      await small.getByRole("button", { name: "Reviewer access" }).waitFor();
      await phone.close();
    });
  } finally {
    await browser.close();
    // Whatever happened above, leave the premise approved.
    const { statements } = await workspace();
    if (statements.find((statement) => statement.id === PREMISE).approvalStatus !== "approved") {
      await review("approved", "e2e cleanup", { token: TOKEN });
    }
  }
}

// ------------------------------------------------------------------ run

console.log(`End-to-end checks against ${BASE.href}`);
if (READ_ONLY) {
  await readOnlyDeployment();
} else {
  if ((await workspace({ token: TOKEN })).access.lockedOut) {
    console.error("This address is locked out on the server (a full run ends by locking it out). Restart the server first.");
    process.exit(2);
  }
  await pageAndHeaders();
  await readAccess();
  await accessControl();
  await reviewFlow();
  await leanRuns();
  if (WITH_BROWSER) await browserChecks();
  else skip("browser checks", "E2E_BROWSER=0", { allowedInCi: true });
  await limits(); // near the end: it deliberately trips the limits
  await lockedOutReviewer();
}

console.log(`\n${passed} passed, ${failures.length} failed, ${skipped.length} skipped`);
process.exit(failures.length ? 1 : 0);
