/* Run with: node --test tests/js/test_smi_hybrid_presentation.cjs */
const test=require("node:test");
const assert=require("node:assert/strict");
const presentation=require("../../mission_control/static/smi_hybrid_presentation.js");
test("hybrid presentation selection preserves canonical owners",()=>{
 const control=presentation.create();
 assert.equal(control.snapshot().mode,"realistic3d");
 assert.equal(control.select("animated_cartoon").mode,"animated_cartoon");
 assert.equal(control.snapshot().brainOwner,"smi");
 assert.equal(control.snapshot().rendererOwner,"smi_source_pixel_motion");
 assert.equal(control.select("unknown").mode,"animated_cartoon");
 assert.equal(control.snapshot().productionApproved,false);
 assert.equal(control.snapshot().visualRuntimeVerified,false);
});
test("STOP latches mode and only explicit human reset reopens it",()=>{
 const control=presentation.create();
 control.stop();
 assert.equal(control.select("animated_cartoon").mode,"realistic3d");
 control.resetAfterHumanAction(false);
 assert.equal(control.snapshot().stopped,true);
 control.resetAfterHumanAction(true);
 assert.equal(control.select("animated_cartoon").mode,"animated_cartoon");
});
