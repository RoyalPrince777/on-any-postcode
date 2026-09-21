/* Fail-closed evaluator for a Human-supplied physical Android motion receipt.
 * It cannot create, sign or approve receipts and never grants production.
 */
"use strict";
const crypto=require("node:crypto");
const APPROVED_SHA="f9503174f6f18b815f1c73e24faff3b4966c2e1fbae8d20a8d2bcc22e4a84a4b";
const LAYERS=Object.freeze(["eyes","head","breathing","mouth_visemes","face","hands","upper_body"]);
function reject(reasons){return Object.freeze({accepted:false,aegis75Ready:false,productionApproved:false,humanFinalApproved:false,reasons:Object.freeze(reasons)});}
function canonicalise(value){
  if(Array.isArray(value))return value.map(canonicalise);
  if(value&&typeof value==="object")return Object.fromEntries(Object.keys(value).sort().map(k=>[k,canonicalise(value[k])]));
  return value;
}
function evaluateAndroidReceipt(receipt,{nowMs=Date.now()}={}){
  const reasons=[];
  if(!receipt||typeof receipt!=="object"||Array.isArray(receipt))return reject(["receipt_missing"]);
  if(receipt.evidenceType!=="physical_android_human_test")reasons.push("physical_android_test_missing");
  if(receipt.platform!=="Android")reasons.push("platform_not_android");
  if(typeof receipt.deviceModel!=="string"||receipt.deviceModel.trim().length<2)reasons.push("device_model_missing");
  if(typeof receipt.androidVersion!=="string"||receipt.androidVersion.trim().length<1)reasons.push("android_version_missing");
  if(receipt.approvedSourceSha256!==APPROVED_SHA)reasons.push("source_sha_mismatch");
  if(!receipt.layerSha256||Object.keys(receipt.layerSha256).length!==LAYERS.length||LAYERS.some(x=>!(/^[a-f0-9]{64}$/).test(receipt.layerSha256[x]||"")))reasons.push("seven_layer_hashes_invalid");
  if(receipt.exactCharacterIntact!==true)reasons.push("exact_character_not_approved");
  if(receipt.playedAudioObserved!==true||!Number.isFinite(receipt.maxAudioClockDeltaMs)||receipt.maxAudioClockDeltaMs>80||receipt.maxAudioClockDeltaMs<0)reasons.push("played_audio_timing_unproven");
  if(receipt.motionStopped!==true||receipt.audioStopped!==true||!Number.isFinite(receipt.stopAcknowledgementMs)||receipt.stopAcknowledgementMs>50||receipt.stopAcknowledgementMs<0)reasons.push("immediate_stop_unproven");
  if(receipt.backgroundStopPassed!==true)reasons.push("background_stop_unproven");
  if(receipt.humanVisualApproved!==true)reasons.push("human_visual_approval_missing");
  if(receipt.productionApproved!==false||receipt.humanFinalApproved!==false)reasons.push("forbidden_approval_claim");
  const tested=Date.parse(receipt.testedAt||"");
  if(!Number.isFinite(tested)||tested>nowMs+300000||nowMs-tested>86400000)reasons.push("test_time_invalid_or_stale");
  if(typeof receipt.humanNote!=="string"||receipt.humanNote.trim().length<3)reasons.push("human_note_missing");
  if(reasons.length)return reject(reasons);
  const canonical=JSON.stringify(canonicalise(receipt));
  return Object.freeze({accepted:true,aegis75Ready:true,productionApproved:false,humanFinalApproved:false,
    receiptSha256:crypto.createHash("sha256").update(canonical).digest("hex"),reasons:Object.freeze([])});
}
module.exports=Object.freeze({APPROVED_SHA,LAYERS,evaluateAndroidReceipt});
