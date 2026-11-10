"use strict";
const assert=require("node:assert/strict");
const api=require("../mission_control/static/smi_organism_anatomy.js");
assert.equal(api.dimensions.length,13);
assert.equal(api.foundations.length,4);
assert.equal(api.upgrades.length,7);
assert.ok(api.systems.brain.includes("left-hemisphere"));
assert.ok(api.systems.brain.includes("right-hemisphere"));
assert.ok(api.systems.brain.includes("hippocampus"));
assert.ok(api.systems.cardiovascular.includes("heart"));
assert.equal(Object.keys(api.systems).length,16);
for(const part of ["scalp","left-eye","right-eye","left-hand","right-hand","left-foot","right-foot","nails"]){assert.ok(api.systems.external.includes(part),part);}
for(const part of ["longitudinal-fissure","corpus-callosum","thalamus","fornix","pituitary-gland","interventricular-foramen","foramen-of-luschka","spinal-cord"]){assert.ok(api.systems.brain.includes(part),part);}
for(const system of ["nervous","sensory","skeletal","muscular","cardiovascular","respiratory","digestive","urinary","endocrine","immune","reproductive","integumentary","cellular","support"]){assert.ok(api.systems[system].length>0,system);}
const now=1762191000000;
const m=api.create({clock:()=>now});
assert.equal(m.stateFor("brain","thalamus").state,"unknown");
assert.equal(m.observe({system:"brain",part:"not-a-part",state:"healthy",source:"test",observedAt:now}),false);
assert.equal(m.observe({system:"brain",part:"thalamus",state:"healthy"}),true);
assert.equal(m.stateFor("brain","thalamus").state,"unknown","no evidence cannot be healthy");
assert.equal(m.observe({system:"brain",part:"thalamus",state:"healthy",source:"runtime-receipt",observedAt:now}),true);
assert.equal(m.stateFor("brain","thalamus").state,"healthy");
assert.equal(m.observe({system:"brain",part:"thalamus",state:"critical",source:"runtime-receipt",observedAt:now}),true);
assert.equal(m.stateFor("brain","thalamus").state,"critical");
assert.equal(m.observe({system:"brain",part:"thalamus",state:"healthy",source:"runtime-receipt",observedAt:now-999999999}),true);
assert.equal(m.stateFor("brain","thalamus").state,"unknown","stale evidence must be unknown");
assert.equal(m.observe({system:"brain",part:"thalamus",state:"invented",source:"runtime-receipt",observedAt:now}),false);
assert.equal(m.setForm("xray"),true);
assert.equal(m.setForm("invalid"),false);
let called=0;const un=m.subscribe(()=>called++);m.observe({system:"brain",part:"pons",state:"busy",source:"chat",observedAt:now});un();assert.ok(called>=2);
m.stop();assert.equal(m.observe({system:"brain",part:"pons",state:"healthy",source:"chat",observedAt:now}),false);
assert.equal(m.reset(false),false);
assert.equal(m.reset(true),true);
assert.equal(m.getSnapshot().identity,"SMI");
let tick=now;
const expiry=api.create({clock:()=>tick});
assert.equal(expiry.observe({system:"cardiovascular",part:"heart",state:"healthy",source:"signed-health-receipt",observedAt:tick}),true);
assert.equal(expiry.stateFor("cardiovascular","heart").state,"healthy");
tick+=60001;
assert.equal(expiry.stateFor("cardiovascular","heart").state,"unknown","health reading must expire without another event");
assert.equal(expiry.getSnapshot().regions["cardiovascular:heart"].state,"unknown","aggregate snapshot must never retain expired healthy state");
assert.equal(expiry.getSnapshot().regions["cardiovascular:heart"].evidence,false,"expired aggregate evidence must be marked invalid");

console.log("SMI anatomy monitor contract: passed");
