const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const source=fs.readFileSync('app-web/beta-client.js','utf8');
test('session deadline settles a stalled provider and preserves successful values',async()=>{
 const code=source.slice(source.indexOf('function deadline('),source.indexOf('function updateGate('));
 const ctx={setTimeout,clearTimeout,Promise,Error};vm.createContext(ctx);vm.runInContext(code,ctx);
 assert.equal(await ctx.deadline(Promise.resolve('ok'),30),'ok');
 await assert.rejects(ctx.deadline(new Promise(()=>{}),5),/tardó demasiado/);
});
test('late authenticated response cannot unlock a cancelled restoration',async()=>{
 const code=source.slice(source.indexOf('async function refresh('),source.indexOf('function googleButton('));
 let resolve;const account=new Promise(r=>resolve=r);let changed=0;
 const ctx={authAttempt:1,api:()=>account,client:{auth:{getSession:async()=>({data:{session:{user:{user_metadata:{}}}}})}},deadline:p=>p,current:null,changed:()=>changed++,URL,String};
 vm.createContext(ctx);vm.runInContext(code,ctx);
 const pending=ctx.refresh(()=>false);resolve({email:'qa@example.invalid',favorites:[]});await pending;
 assert.equal(ctx.current,null);assert.equal(changed,0);
});
test('backend rejection cannot unlock an account from a stored token',async()=>{
 const code=source.slice(source.indexOf('async function refresh('),source.indexOf('function googleButton('));
 const ctx={authAttempt:1,api:async()=>{throw new Error('unauthorized')},current:null};vm.createContext(ctx);vm.runInContext(code,ctx);
 await assert.rejects(ctx.refresh(),/unauthorized/);assert.equal(ctx.current,null);
});

test('preference refresh cannot restore an account after sign-out',async()=>{
 const code=source.slice(source.indexOf('async function refresh('),source.indexOf('function googleButton('));
 let release;const response=new Promise(r=>release=r);
 const ctx={authAttempt:1,api:()=>response,client:{auth:{getSession:async()=>({data:{session:{user:{user_metadata:{}}}}})}},deadline:p=>p,current:null,changed:()=>{throw Error('stale refresh must not notify')},URL,String};
 vm.createContext(ctx);vm.runInContext(code,ctx);
 const pending=ctx.refresh();ctx.authAttempt++;release({email:'qa@example.invalid',favorites:[]});await pending;
 assert.equal(ctx.current,null);
});
test('session disappearing after backend response cannot unlock account',async()=>{
 const code=source.slice(source.indexOf('async function refresh('),source.indexOf('function googleButton('));
 const ctx={authAttempt:1,api:async()=>({email:'qa@example.invalid'}),client:{auth:{getSession:async()=>({data:{session:null}})}},deadline:p=>p,current:{email:'previous@example.invalid'},changed:()=>{},URL,String};
 vm.createContext(ctx);vm.runInContext(code,ctx);await ctx.refresh();assert.equal(ctx.current,null);assert.equal(ctx.authPhase,'anonymous');
});
