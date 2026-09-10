// Execute only the actual audio adapter against isolated browser primitives.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
const events = new Map();
const window = {pvzStartRequested:false, addEventListener(name, handler) {
  events.set(name, [...(events.get(name)||[]), handler]);
}};
class Media {
  paused=true; ended=false;
  play() {this.paused=false; return Promise.resolve();}
  pause() {this.paused=true;}
}
class Context {
  state='suspended';
  addEventListener() {}
  suspend() {this.state='suspended'; return Promise.resolve();}
  resume() {this.state='running'; return Promise.resolve();}
}
window.AudioContext = Context;
const document = {hidden:false, hasFocus:()=>true, addEventListener:window.addEventListener};
const source = fs.readFileSync(new URL('../dist/web.js', import.meta.url), 'utf8');
const context = vm.createContext({window, document, HTMLMediaElement:Media,
  byId:()=>({open:false}), signal:undefined, Set, Proxy, Promise});
const start = source.indexOf('let pageFocused');
const end = source.indexOf('function fitGame()');
vm.runInContext(source.slice(start, end), context);
const emit = name => {for (const handler of events.get(name)||[]) handler();};
const music = new Media();
const audio = new window.AudioContext();
await music.play();
assert.equal(music.paused, true, 'no audio before sound gesture');
window.pvzStartRequested=true;
emit('focus');
assert.equal(music.paused, false);
assert.equal(audio.state, 'running');
emit('blur');
assert.equal(music.paused, true, 'blur pauses music even before hasFocus changes');
assert.equal(audio.state, 'suspended');
await music.play();
assert.equal(music.paused, true, 'background play cannot restart music');
emit('focus');
assert.equal(music.paused, false);
document.hidden=true;
emit('visibilitychange');
assert.equal(music.paused, true);
assert.equal(audio.state, 'suspended');
music.pause();
document.hidden=false;
emit('visibilitychange');
assert.equal(music.paused, true, 'explicit stop is not undone on return');
await music.play();
emit('pagehide');
assert.equal(music.paused, true);
assert.equal(audio.state, 'suspended');
console.log('PASS sound gesture, blur, hidden page, blocked background playback, resume and page exit');
