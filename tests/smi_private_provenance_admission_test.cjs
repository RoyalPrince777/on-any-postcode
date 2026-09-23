"use strict";
const assert=require("node:assert/strict");
const {admitWithProvenance,verifyGeometryPayload}=require("../mission_control/smi_private_provenance_admission.js");
const {ORIGINAL_JPG_SHA256}=require("../mission_control/smi_private_source_provenance.js");
const originalJpgBytes=Uint8Array.from([255,216,255,217]);
const sourceRgba=new Uint8ClampedArray([10,20,30,255]);
const maskRgba=new Uint8ClampedArray([255,255,255,255]);
const geometryRgba=new Uint8ClampedArray([10,20,30,255]);
// No fixture is entitled to pass the pinned original's SHA-256 gate.
// The checked full-canvas pixels and digest payload must be identical.
assert.equal(verifyGeometryPayload(Uint8Array.from(geometryRgba),geometryRgba),true);
assert.equal(verifyGeometryPayload(Uint8Array.from([10,20,31,255]),geometryRgba),false);
assert.equal(verifyGeometryPayload(Uint8Array.from([10,20,30]),geometryRgba),false);
assert.equal(verifyGeometryPayload(new Uint8Array(0),geometryRgba),false);
assert.equal(verifyGeometryPayload(null,geometryRgba),false);
assert.equal(verifyGeometryPayload(Uint8Array.from(geometryRgba),null),false);
const larger=Uint8Array.from([99,10,20,30,255,77]);
assert.equal(verifyGeometryPayload(larger.subarray(1,5),geometryRgba),true);
const args={sourceSha256:ORIGINAL_JPG_SHA256,originalJpgBytes,
 sourceRgba,maskRgba,geometryRgba,width:1,height:1};
assert.equal(admitWithProvenance(args),null);
assert.equal(admitWithProvenance({...args,originalJpgBytes:null}),null);
assert.equal(admitWithProvenance({...args,sourceSha256:"a".repeat(64)}),null);
assert.equal(admitWithProvenance({...args,geometryRgba:new Uint8ClampedArray([10,20,31,255])}),null);
assert.equal(admitWithProvenance({...args,maskRgba:new Uint8ClampedArray(4)}),null);
assert.equal(admitWithProvenance({...args,width:2}),null);
assert.equal(admitWithProvenance(),null);
console.log("SMI_PRIVATE_PROVENANCE_ADMISSION_REJECTS_UNVERIFIED_PASS");
