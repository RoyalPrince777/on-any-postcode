/* Run with: node --test tests/js/test_smi_hybrid_presentation.cjs */
const test=require("node:test");
const assert=require("node:assert/strict");
const presentation=require("../../mission_control/static/smi_hybrid_presentation.js");
test("original Founder avatar is the fail-closed default",()=>{
 const control=presentation.create();
 assert.equal(control.snapshot().mode,"original_avatar");
 assert.equal(control.snapshot().sevenLayerRigPreserved,true);
 assert.equal(control.snapshot().rendererOwner,"smi_source_pixel_motion");
 assert.equal(control.snapshot().brainOwner,"smi");
 assert.equal(control.select("animated_cartoon").mode,"original_avatar");
 assert.equal(control.select("realistic3d").mode,"original_avatar");
 assert.equal(control.select("unknown").mode,"original_avatar");
 assert.equal(control.snapshot().productionApproved,false);
 assert.equal(control.snapshot().visualRuntimeVerified,false);
});
test("experimental selection requires explicit opt-in and remains unverified",()=>{
 const control=presentation.create({allowExperimentalStyles:true});
 assert.equal(control.select("animated_cartoon").mode,"animated_cartoon");
 assert.equal(control.snapshot().optionalStylesImplemented,false);
 assert.equal(control.select("original_avatar").mode,"original_avatar");
});
test("STOP latches selection until explicit human action",()=>{
 const control=presentation.create({allowExperimentalStyles:true});
 control.stop();
 assert.equal(control.select("animated_cartoon").mode,"original_avatar");
 control.resetAfterHumanAction(false);
 assert.equal(control.snapshot().stopped,true);
 control.resetAfterHumanAction(true);
 assert.equal(control.select("animated_cartoon").mode,"animated_cartoon");
});

test("canonical chat loads preference without replacing the original rig",()=>{
 const fs=require("node:fs");
 const path=require("node:path");
 const html=fs.readFileSync(path.join(__dirname,"../../mission_control/templates/ollama_chat.html"),"utf8");
 const rig=html.indexOf("smi_exact_character_rig.js");
 const presentationIndex=html.indexOf("smi_hybrid_presentation.js");
 const source=html.indexOf("smi_source_pixel_motion.js");
 assert.ok(rig>=0 && presentationIndex>rig && source>presentationIndex);
 assert.ok(html.includes("OAP_SMI_HYBRID_PRESENTATION.create()"));
 assert.ok(html.includes("OAP_SMI_SOURCE_PIXEL_MOTION.attach()"));
});
