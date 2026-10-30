/*
 * Registry-keeping tests for the dashboard card (plain Node, no npm packages):
 * `node tests/card/registry.test.mjs`.
 *
 * Another card or add-on may load the polyfill @webcomponents/scoped-custom-element-registry,
 * which replaces window.customElements with a new, empty registry. Home Assistant then
 * reports "Custom element doesn't exist". The card must register itself in whichever
 * registry is current, also long after startup. Each scenario runs the real card file in
 * a fresh VM context with a fake registry, fake events and a virtual clock.
 */
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import vm from "node:vm";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const CARD = path.join(here, "../../custom_components/water_leak_detection/frontend/water-leak-guard-card.js");
const SOURCE = fs.readFileSync(CARD, "utf8");
const TAGS = ["water-leak-guard-card", "water-leak-guard-card-editor"];

function fakeRegistry() {
  const defined = new Map();
  return {
    defined,
    get: (name) => defined.get(name),
    define(name, constructor) {
      defined.set(name, constructor);
    },
  };
}
const hasAll = (registry) => TAGS.every((tag) => registry.defined.has(tag));

/** Runs the card in a fresh context; returns handles to swap the registry and move time. */
function load(registry = fakeRegistry(), { warn = () => {} } = {}) {
  const timers = [];
  let now = 0;
  const handlers = new Map();
  const listen = (type, handler) => handlers.set(type, [...(handlers.get(type) || []), handler]);
  let unrefs = 0;
  class ShadowRoot { constructor() { this.innerHTML = ""; this.activeElement = null; } addEventListener() {} querySelectorAll() { return []; } }
  const context = {
    HTMLElement: class { attachShadow() { return new ShadowRoot(); } dispatchEvent() { return true; } appendChild() {} },
    CustomEvent: class { constructor(type, init) { this.type = type; this.detail = init?.detail; } },
    console: { info() {}, warn },
    document: { addEventListener: listen, removeEventListener() {}, visibilityState: "visible", createElement: () => ({}) },
    setTimeout(fn, ms) {
      timers.push({ at: now + ms, fn });
      return { unref() { unrefs++; } };
    },
    clearTimeout() {},
    customElements: registry,
  };
  context.window = context;
  context.window.addEventListener = listen;
  vm.runInNewContext(SOURCE, context, { filename: CARD });
  return {
    context,
    get unrefs() { return unrefs; },
    swap(next) { context.customElements = next; },
    advance(ms) {
      const end = now + ms;
      for (;;) {
        timers.sort((a, b) => a.at - b.at);
        if (!timers.length || timers[0].at > end) break;
        const next = timers.shift();
        now = next.at;
        next.fn();
      }
      now = end;
    },
    emit(type) { (handlers.get(type) || []).forEach((handler) => handler({ type })); },
  };
}

let count = 0;
const scenario = (name, run) => {
  run();
  count++;
  console.log(`ok - ${name}`);
};

scenario("registers card and editor at once in the current registry", () => {
  const registry = fakeRegistry();
  load(registry);
  assert.equal(hasAll(registry), true);
});

scenario("registers in a registry that is replaced shortly after startup", () => {
  const first = fakeRegistry();
  const page = load(first);
  const next = fakeRegistry();
  page.swap(next);
  assert.equal(next.defined.size, 0);
  page.advance(600);
  assert.equal(hasAll(next), true);
  TAGS.forEach((tag) => assert.equal(next.defined.get(tag), first.defined.get(tag)));
});

scenario("repairs a late replacement, long after startup (within 10 s)", () => {
  const page = load();
  page.advance(10 * 60 * 1000);
  const late = fakeRegistry();
  page.swap(late);
  page.advance(9_999);
  assert.equal(hasAll(late), true);
});

scenario("repairs every further replacement again", () => {
  const page = load();
  for (let round = 0; round < 3; round++) {
    const next = fakeRegistry();
    page.swap(next);
    page.advance(10_000);
    assert.equal(hasAll(next), true);
  }
});

scenario("registers at once on location-changed and visibility changes", () => {
  const page = load();
  page.advance(60_000);
  const first = fakeRegistry();
  page.swap(first);
  page.emit("location-changed");
  assert.equal(hasAll(first), true);
  const second = fakeRegistry();
  page.swap(second);
  page.emit("visibilitychange");
  assert.equal(hasAll(second), true);
  const third = fakeRegistry();
  page.swap(third);
  page.emit("load");
  assert.equal(hasAll(third), true);
});

scenario("leaves foreign entries in the new registry alone", () => {
  const page = load();
  const late = fakeRegistry();
  const foreign = class {};
  late.define("water-leak-guard-card", foreign);
  page.swap(late);
  page.advance(10_000);
  assert.equal(late.defined.get("water-leak-guard-card"), foreign);
  assert.equal(late.defined.has("water-leak-guard-card-editor"), true);
});

scenario("first loaded copy wins: an older registered class is kept and carried over, with one warning", () => {
  const registry = fakeRegistry();
  const older = class { static get cardVersion() { return "2.0.0"; } };
  registry.define("water-leak-guard-card", older);
  const warnings = [];
  const page = load(registry, { warn: (message) => warnings.push(message) });
  assert.equal(registry.defined.get("water-leak-guard-card"), older);
  assert.equal(warnings.length, 1);
  assert.match(warnings[0], /version 2\.0\.0 is already loaded/);
  const next = fakeRegistry();
  page.swap(next);
  page.advance(10_000);
  assert.equal(next.defined.get("water-leak-guard-card"), older);
  assert.equal(warnings.length, 1);
});

scenario("defines nothing again while the registry stays the same", () => {
  const registry = fakeRegistry();
  const page = load(registry);
  let defines = 0;
  const define = registry.define;
  registry.define = (...args) => {
    defines++;
    return define(...args);
  };
  page.advance(5 * 60 * 1000);
  assert.equal(defines, 0);
});

scenario("survives a registry that rejects define, and hands out unref'd timers", () => {
  const registry = fakeRegistry();
  registry.define = () => {
    throw new Error("already used");
  };
  const page = load(registry);
  page.advance(30_000);
  assert.ok(page.unrefs > 0);
});

scenario("costs next to nothing in steady state: one round every 10 s, two lookups each", () => {
  const registry = fakeRegistry();
  const page = load(registry);
  page.advance(60_000);
  let gets = 0;
  const get = registry.get;
  registry.get = (name) => {
    gets++;
    return get(name);
  };
  page.advance(60_000);
  assert.equal(gets, 6 * TAGS.length);
});

console.log(`${count} registry scenarios passed`);
