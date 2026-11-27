import {test} from "node:test";
import assert from "node:assert/strict";
import {Document, NodeIO} from "@gltf-transform/core";
import {roundTripLocalGlb, validateLocalGlb} from "./geometry.mjs";

async function triangle() {
  const doc = new Document();
  const buffer = doc.createBuffer();
  const pos = doc.createAccessor().setType("VEC3").setArray(new Float32Array([0,0,0,1,0,0,0,1,0])).setBuffer(buffer);
  const indices = doc.createAccessor().setType("SCALAR").setArray(new Uint16Array([0,1,2])).setBuffer(buffer);
  const prim = doc.createPrimitive().setAttribute("POSITION", pos).setIndices(indices);
  const mesh = doc.createMesh().addPrimitive(prim);
  doc.createScene().addChild(doc.createNode().setMesh(mesh));
  return new NodeIO().writeBinary(doc);
}
test("real Khronos validator and glTF Transform roundtrip preserves triangle", async () => {
  const input = await triangle();
  const result = await roundTripLocalGlb(input);
  assert.equal(result.before.errors, 0);
  assert.equal(result.after.errors, 0);
  assert.equal(result.runtime_verified, false);
  assert.equal(result.optimization_verified, false);
  const output = await new NodeIO().readBinary(result.output);
  const prim = output.getRoot().listMeshes()[0].listPrimitives()[0];
  assert.deepEqual([...prim.getAttribute("POSITION").getArray()], [0,0,0,1,0,0,0,1,0]);
  assert.deepEqual([...prim.getIndices().getArray()], [0,1,2]);
});
test("malformed input rejected", async () => {
  await assert.rejects(validateLocalGlb(new Uint8Array(20)), /header_invalid/);
});
test("external asset and unknown extension rejected before library execution", async () => {
  for (const extra of [{images:[{uri:"https://example.invalid/a.png"}]},{extensionsUsed:["UNKNOWN_extension"]}]) {
    const text = JSON.stringify({asset:{version:"2.0"},...extra});
    const json = Buffer.from(text+" ".repeat((4-Buffer.byteLength(text)%4)%4));
    const bytes = Buffer.alloc(20+json.length);
    bytes.write("glTF"); bytes.writeUInt32LE(2,4); bytes.writeUInt32LE(bytes.length,8);
    bytes.writeUInt32LE(json.length,12); bytes.write("JSON",16); json.copy(bytes,20);
    await assert.rejects(validateLocalGlb(bytes), /external_or_extension_blocked/);
  }
});


test("original shelter asset passes Khronos validation and round-trip", async () => {
  const {readFile} = await import("node:fs/promises");
  const input = await readFile(new URL("./assets/oap_bus_shelter.glb", import.meta.url));
  const result = await roundTripLocalGlb(input);
  assert.equal(result.before.sha256, "541bb74f2c1a411c0c0a57c0d814044b699c52f9c7df38060b966f7ff8b3f964");
  assert.equal(result.before.errors, 0);
  assert.equal(result.after.errors, 0);
  const doc = await new NodeIO().readBinary(result.output);
  assert.equal(doc.getRoot().listNodes().length, 14);
  assert.equal(doc.getRoot().listMaterials().length, 5);
  assert.equal(doc.getRoot().listNodes().reduce((n, node) => n + node.getMesh().listPrimitives().reduce((sum, primitive) => sum + primitive.getIndices().getCount()/3, 0), 0), 168);
  assert.equal(result.runtime_verified, false);
});
