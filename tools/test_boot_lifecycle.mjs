// Exercise the shipped adapter with isolated DOM primitives; no audible game.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const html = fs.readFileSync(new URL('../dist/index.html', import.meta.url), 'utf8');
const css = fs.readFileSync(new URL('../dist/web.css', import.meta.url), 'utf8');
assert.match(html, /id="start-button">Start the game<\/button>/);
assert.match(html, /type="text\/plain" id="runtime-source"/);
assert.doesNotMatch(html, /<script[^>]+src="[^"]*pythons.js/);
assert.match(html, /id="boot-cover" src="custom-cover-v2.png"/);
assert.match(html, /<canvas[^>]*id="canvas"[^>]*inert/);
const initialMask = css.match(/#boot-screen::after\s*\{([^}]+)\}/)[1];
assert.match(initialMask, /display:\s*block/);
assert.match(initialMask, /inset:\s*0/);
assert.match(initialMask, /background:\s*#0009/);
assert.match(css, /#boot-screen\s*\{[^}]*position:\s*fixed[^}]*inset:\s*0/);

function makeApp() {
  const events = new Map(), elements = new Map(), scripts = [];
  const on = (target, type, fn) => {
    const key = target + ':' + type;
    events.set(key, [...(events.get(key) || []), fn]);
  };
  const byId = id => {
    if (!elements.has(id)) elements.set(id, {
      id, hidden: false, inert: id === 'canvas', value: 0, textContent: '',
      style: {setProperty() {}}, classList: {values: new Set(), add(v) {this.values.add(v);}},
      addEventListener(type, fn) {on(id, type, fn);},
      setAttribute(key, value) {this[key] = value;},
      getAttribute(key) {return this[key] || '';},
      focus() {this.focused = true;}, blur() {this.focused = false;},
      closest(selector) {return selector.includes('#' + id) ? this : null;},
    });
    return elements.get(id);
  };
  class Media {play() {return Promise.resolve();} pause() {}}
  const document = {
    getElementById: byId, hasFocus: () => true, hidden: false,
    createElement: type => byId('new-' + type),
    body: {appendChild: node => scripts.push(node)},
    querySelectorAll: () => [], addEventListener(type, fn) {on('document', type, fn);},
  };
  const window = {config: {ume_block: 1}, addEventListener(type, fn) {on('window', type, fn);}};
  const context = vm.createContext({window, document, HTMLMediaElement: Media,
    matchMedia: () => ({matches: false, addEventListener() {}}),
    AbortController, innerWidth: 800, innerHeight: 600,
    console: {error() {}}, location: {reload() {}}, setTimeout, clearTimeout});
  vm.runInContext(fs.readFileSync(new URL('../dist/web.js', import.meta.url), 'utf8'), context);
  const emit = (target, type, details = {}) => {
    const event = {target: byId(target), ...details,
      stopImmediatePropagation() {this.stopped = true;},
      preventDefault() {this.prevented = true;}};
    for (const fn of events.get('window:' + type) || []) {fn(event); if (event.stopped) break;}
    if (!event.stopped) for (const fn of events.get(target + ':' + type) || []) fn(event);
    return event;
  };
  return {window, byId, emit, scripts, receive: (kind, data) => window.pvzReceive(kind, JSON.stringify(data))};
}

const app = makeApp();
const {byId, emit, receive, window} = app;
assert.equal(app.scripts.length, 0, 'no runtime or game downloads before Start');
assert.equal(emit('canvas', 'pointerdown').stopped, true);
assert.equal(emit('canvas', 'touchstart').prevented, true);
assert.equal(emit('canvas', 'keydown', {key: '9'}).stopped, true);
assert.equal(emit('start-button', 'keydown', {key: '9'}).stopped, true);
assert.equal(emit('start-button', 'keydown', {key: 'Enter'}).stopped, undefined);
receive('ready', true);
assert.equal(byId('boot-screen').hidden, false, 'ready cannot bypass sound gesture');
emit('start-button', 'click');
assert.equal(app.scripts.length, 1);
assert.equal(app.scripts[0].src, 'runtime/pythons.js');
assert.equal(window.config.ume_block, 0, 'no second unlock gesture required');
emit('start-button', 'click');
assert.equal(app.scripts.length, 1, 'repeat clicks cannot boot another instance');
assert.equal(window.pvzStartRequested, true);
assert.equal(byId('boot-screen').classList.values.has('loading'), true);
assert.equal(byId('start-button').disabled, true);
assert.equal(byId('canvas').inert, true);
receive('status', '正在展开游戏素材…');
receive('progress', 35);
assert.equal(byId('boot-status').textContent, '正在展开游戏素材…');
assert.equal(byId('boot-percent').textContent, '35%');
receive('progress', 10);
assert.equal(byId('boot-progress').value, 35, 'no backward progress');
receive('progress', 100);
assert.equal(byId('boot-progress').value, 99, 'progress alone cannot unlock');
assert.equal(emit('canvas', 'click').stopped, true);
assert.equal(window.pvzDrain(), '[]', 'loading gestures never enter gameplay queue');
receive('ready', true);
assert.equal(byId('boot-progress').value, 100);
assert.equal(byId('boot-screen').hidden, true);
assert.equal(byId('canvas').inert, false);
assert.equal(byId('canvas').tabIndex, 0);
assert.equal(byId('canvas')['aria-busy'], 'false');
assert.equal(emit('canvas', 'keyup', {key: '9'}).stopped, undefined);
receive('failure', '测试失败');
assert.equal(byId('boot-screen').hidden, false);
assert.equal(byId('canvas').inert, true);
assert.equal(byId('retry-button').hidden, false);
receive('ready', true);
receive('status', 'late message');
assert.equal(byId('boot-screen').hidden, false, 'failure stays locked');
assert.match(byId('boot-status').textContent, /测试失败/);
assert.equal(emit('retry-button', 'click').stopped, undefined);

const fast = makeApp();
fast.receive('progress', 90); // cached preloading can finish before the click
fast.emit('start-button', 'click');
assert.equal(fast.byId('boot-percent').textContent, '90%');
assert.equal(fast.byId('boot-screen').hidden, false);
console.log('PASS loading progress, input lock, gesture gate, first-frame ready, failure/retry and cached preload');

// Test the actual vendored bootstrap's late-module lifecycle without the WASM.
const runtime = fs.readFileSync(new URL('../dist/runtime/pythons.js', import.meta.url), 'utf8');
const bootstrap = runtime.slice(runtime.indexOf('function auto_start(cfg)'),
  runtime.indexOf('globalThis.__canvas_resized'));
for (const readyState of ['complete', 'loading']) {
  const callbacks = [], listeners = [];
  const ctx = vm.createContext({
    module_name: 'pythons.js', vm: {script: {}}, console: {log() {}}, auto_conf() {},
    onload() {}, queueMicrotask: fn => callbacks.push(fn),
    window: {addEventListener: (...args) => listeners.push(args)},
    document: {readyState, getElementsByTagName: () => [
      {type: 'text/plain', src: '', text: '', dataset: {}},
      {type: 'module', src: 'https://pvz.rosebeg.com/runtime/pythons.js',
       text: '# Python entry', id: 'site', dataset: {python: 'python3.12', os: 'stdout,snd,gui'}}
    ]},
  });
  vm.runInContext(bootstrap + '\nauto_start();', ctx);
  assert.equal(callbacks.length, readyState === 'complete' ? 1 : 0);
  assert.equal(listeners.length, readyState === 'loading' ? 1 : 0);
  if (listeners.length) assert.equal(listeners[0][2].once, true);
}
console.log('PASS deferred runtime bootstrap before/after page load; exactly one instance');
