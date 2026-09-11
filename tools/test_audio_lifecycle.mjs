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
  deferPlay=false; pending=[]; failure=null;
  play() {
    this.paused=false;
    if (this.failure) return Promise.reject(this.failure);
    if (this.deferPlay) return new Promise((resolve, reject) => this.pending.push({resolve, reject}));
    return Promise.resolve();
  }
  pause() {
    this.paused=true;
    for (const {reject} of this.pending.splice(0)) reject(Object.assign(
      new Error('The play() request was interrupted by a call to pause().'), {name:'AbortError'}));
  }
  finishPlay() {for (const {resolve} of this.pending.splice(0)) resolve();}
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
emit('focus');
// Model rapid level music replacements. The native caller intentionally does
// not await play(), just as Pygbag does. Previously these reached its alert().
const unhandled = [];
const onUnhandled = reason => unhandled.push(reason);
process.on('unhandledRejection', onUnhandled);
const jumpingMusic = new Media();
jumpingMusic.deferPlay = true;
for (let i=0; i<100; i++) {
  void jumpingMusic.play();
  jumpingMusic.pause();
}
void jumpingMusic.play();
emit('blur'); // Cancel an in-flight play on backgrounding too.
await new Promise(resolve => setImmediate(resolve));
assert.deepEqual(unhandled, [], 'expected playback cancellations must never reach the runtime alert');
assert.equal(jumpingMusic.paused, true);
emit('focus');
jumpingMusic.finishPlay();
await Promise.resolve();
assert.equal(jumpingMusic.paused, false, 'the current track still resumes normally');
jumpingMusic.pause();
emit('blur');
emit('focus');
assert.equal(jumpingMusic.paused, true, 'stopped old music must not be resurrected');
const brokenMusic = new Media();
brokenMusic.failure = Object.assign(new Error('Invalid audio data'), {name:'NotSupportedError'});
await assert.rejects(brokenMusic.play(), error => error === brokenMusic.failure,
  'real playback errors must not be swallowed');
process.removeListener('unhandledRejection', onUnhandled);
console.log('PASS audio lifecycle, 100 rapid play/pause cancellations, background cancellation, current-track resume, real error propagation');
