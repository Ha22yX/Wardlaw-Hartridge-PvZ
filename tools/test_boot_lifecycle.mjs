// Exercise the shipped adapter with isolated DOM primitives; no audible game.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

function makeApp() {
  const events = new Map(), elements = new Map();
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
      focus() {this.focused = true;}, blur() {this.focused = false;},
      closest(selector) {return selector.includes('#' + id) ? this : null;},
    });
    return elements.get(id);
  };
  class Media {play() {return Promise.resolve();} pause() {}}
  const document = {
    getElementById: byId, hasFocus: () => true, hidden: false,
    querySelectorAll: () => [], addEventListener(type, fn) {on('document', type, fn);},
  };
  const window = {addEventListener(type, fn) {on('window', type, fn);}};
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
  return {window, byId, emit, receive: (kind, data) => window.pvzReceive(kind, JSON.stringify(data))};
}

const app = makeApp();
const {byId, emit, receive, window} = app;
assert.equal(emit('canvas', 'pointerdown').stopped, true);
assert.equal(emit('canvas', 'touchstart').prevented, true);
assert.equal(emit('canvas', 'keydown', {key: '9'}).stopped, true);
assert.equal(emit('start-button', 'keydown', {key: '9'}).stopped, true);
assert.equal(emit('start-button', 'keydown', {key: 'Enter'}).stopped, undefined);
receive('ready', true);
assert.equal(byId('boot-screen').hidden, false, 'ready cannot bypass sound gesture');
emit('start-button', 'click');
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
