/* SMI first-party WAV byte integrity gate, not a voice generator or aligner.
 * Refuses to bind a motion cue to an audio hash asserted without audio bytes.
 * Audio bytes are checked and discarded; no text, audio or telemetry retained.
 */
'use strict';
const crypto=require('node:crypto');
const motion=require('./smi_real_reply_motion_bridge.js');
const MAX_BYTES=32*1024*1024;
function inspectPcmWav(input){
  const fail=reason=>Object.freeze({accepted:false,reason});
  if(!(Buffer.isBuffer(input)||input instanceof Uint8Array))return fail('audio_bytes_missing');
  if(input.byteLength<44||input.byteLength>MAX_BYTES)return fail('audio_size_invalid');
  const bytes=Buffer.from(input.buffer,input.byteOffset,input.byteLength);
  if(bytes.toString('ascii',0,4)!=='RIFF'||bytes.toString('ascii',8,12)!=='WAVE')return fail('wav_header_invalid');
  if(bytes.readUInt32LE(4)!==bytes.length-8)return fail('wav_length_invalid');
  let pos=12,format=null,data=null;
  while(pos+8<=bytes.length){
    const name=bytes.toString('ascii',pos,pos+4),size=bytes.readUInt32LE(pos+4),start=pos+8,end=start+size;
    if(end>bytes.length)return fail('wav_chunk_invalid');
    if(name==='fmt '){
      if(format||size!==16)return fail('wav_format_invalid');
      format={type:bytes.readUInt16LE(start),channels:bytes.readUInt16LE(start+2),sampleRate:bytes.readUInt32LE(start+4),byteRate:bytes.readUInt32LE(start+8),blockAlign:bytes.readUInt16LE(start+12),bits:bytes.readUInt16LE(start+14)};
    }
    if(name==='data'){
      if(data)return fail('wav_multiple_data_chunks');
      data={start,length:size};
    }
    pos=end+(size%2);
  }
  if(pos!==bytes.length||!format||!data||data.length===0)return fail('wav_structure_invalid');
  if(format.type!==1||format.channels!==1||format.bits!==16||format.sampleRate<8000||format.sampleRate>48000||format.blockAlign!==2||format.byteRate!==format.sampleRate*2||data.length%2)return fail('unsupported_pcm_format');
  const durationMs=(data.length/2)/format.sampleRate*1000;
  if(durationMs<=0||durationMs>300000)return fail('audio_duration_invalid');
  let nonZero=false;
  for(let i=data.start;i<data.start+data.length;i+=2){if(bytes.readInt16LE(i)!==0){nonZero=true;break;}}
  if(!nonZero)return fail('silent_audio_not_reply_proof');
  return Object.freeze({accepted:true,audioSha256:crypto.createHash('sha256').update(bytes).digest('hex'),audioDurationMs:durationMs,sampleRate:format.sampleRate,channels:1,retainsAudio:false});
}
function createByteBoundReplyBridge({replyId,humanStart,audioWav,alignment}={}){
  const audio=inspectPcmWav(audioWav);
  if(!audio.accepted)return Object.freeze({accepted:false,reason:audio.reason});
  if(!alignment||alignment.audioSha256!==audio.audioSha256||typeof alignment.audioDurationMs!=='number'||Math.abs(alignment.audioDurationMs-audio.audioDurationMs)>1){
    return Object.freeze({accepted:false,reason:'actual_audio_alignment_mismatch'});
  }
  const bridge=motion.createRealReplyBridge({source:motion.SOURCE,replyId,humanStart,audioSha256:audio.audioSha256,alignment});
  if(!bridge.snapshot().admitted)return Object.freeze({accepted:false,reason:'alignment_contract_rejected'});
  return Object.freeze({accepted:true,bridge,audioSha256:audio.audioSha256,audioDurationMs:audio.audioDurationMs,retainsAudio:false,realSmiReplyProven:false,phonemeProven:false,livePageConnected:false,releaseApproved:false});
}
module.exports=Object.freeze({inspectPcmWav,createByteBoundReplyBridge});
