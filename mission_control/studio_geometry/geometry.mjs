// In-memory, owner-authorized asset processing helper. No routes or worker authority.
// Never read paths, fetch URIs, publish or install dependencies at runtime.
import {createHash} from "node:crypto";
import {NodeIO} from "@gltf-transform/core";
import validator from "gltf-validator";

const LIMIT = 32 * 1024 * 1024;
const JSON_LIMIT = 2 * 1024 * 1024;
const sha = bytes => createHash("sha256").update(bytes).digest("hex");

function localOnly(bytes) {
  if (!(bytes instanceof Uint8Array) || bytes.length < 20 || bytes.length > LIMIT)
    throw new Error("geometry_size_invalid");
  const view = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
  if (view.getUint32(0, true) !== 0x46546c67 || view.getUint32(4, true) !== 2 ||
      view.getUint32(8, true) !== bytes.length || view.getUint32(16, true) !== 0x4e4f534a)
    throw new Error("geometry_glb_header_invalid");
  const size = view.getUint32(12, true);
  if (size > JSON_LIMIT || size % 4 || size > bytes.length - 20)
    throw new Error("geometry_json_size_invalid");
  const doc = JSON.parse(new TextDecoder("utf-8", {fatal:true}).decode(bytes.subarray(20, 20+size)));
  if (!doc || typeof doc !== "object" || Array.isArray(doc) || doc.asset?.version !== "2.0")
    throw new Error("geometry_asset_invalid");
  // Reject all extensions in this bounded initial profile. Do not silently
  // drop materials, morph targets or extension data on a round trip.
  const stack = [doc];
  while (stack.length) {
    const item = stack.pop();
    if (item && typeof item === "object") {
      if (Object.keys(item).some(k => ["uri","extensions","extensionsused","extensionsrequired"].includes(k.toLowerCase())))
        throw new Error("geometry_external_or_extension_blocked");
      for (const value of Object.values(item)) if (value && typeof value === "object") stack.push(value);
    }
  }
}
async function checked(bytes) {
  localOnly(bytes);
  const report = await validator.validateBytes(bytes, {
    maxIssues: 64,
    externalResourceFunction: async () => {throw new Error("geometry_external_resource_blocked");}
  });
  if (report.issues?.numErrors !== 0 || report.issues?.truncated === true)
    throw new Error("geometry_khronos_validation_failed");
  return {errors: report.issues.numErrors, warnings: report.issues.numWarnings, sha256: sha(bytes), size_bytes: bytes.length};
}

export async function validateLocalGlb(input) {
  if (!(input instanceof Uint8Array) || input.byteLength > LIMIT) throw new Error("geometry_size_invalid");
  return {...await checked(Uint8Array.from(input)), runtime_verified:false, published:false};
}
export async function roundTripLocalGlb(input) {
  if (!(input instanceof Uint8Array) || input.byteLength > LIMIT) throw new Error("geometry_size_invalid");
  const bytes = Uint8Array.from(input);
  const before = await checked(bytes);
  const io = new NodeIO();
  const doc = await io.readBinary(bytes);
  const output = await io.writeBinary(doc);
  const after = await checked(output);
  return {output, before, after, schema_validated:true, optimization_verified:false,
          render_verified:false, runtime_verified:false, published:false, founder_final:true};
}
