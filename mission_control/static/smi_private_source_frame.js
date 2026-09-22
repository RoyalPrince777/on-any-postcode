/* Private pixel frame compositor, never a live rig or alignment proof.
 * Uses original decoded pixels + reviewed-mask candidates in the Founder tab.
 * No invented hidden pixels, audio guesses, storage, network or telemetry.
 */
(function(root,factory){
  "use strict";
  const api=factory();
  if(typeof module!=="undefined"&&module.exports)module.exports=api;
  if(root)root.OAP_SMI_PRIVATE_SOURCE_FRAME=api;
})(typeof globalThis!=="undefined"?globalThis:this,function(){
  "use strict";
  const NAMES=Object.freeze(["eyes","head","breathing","mouth_visemes",
    "face","hands","upper_body"]);
  const MOVE=new Set(["eyes","head","breathing","hands","upper_body"]);
  const MAX_PIXELS=16000000;
  const NO_APPROVAL=Object.freeze({motion_proven:false,
    speech_sync_proven:false,human_authority_approved:false,
    hidden_regions_reconstructed:false,attached_to_live_page:false});
  function create({source,masks,width,height,sourceVerified,layerOrder}={}){
    if(sourceVerified!==true||!Number.isSafeInteger(width)
      ||!Number.isSafeInteger(height)||width<1||height<1
      ||width*height>MAX_PIXELS
      ||!(source instanceof Uint8ClampedArray)
      ||source.length!==width*height*4
      ||!Array.isArray(layerOrder)||layerOrder.length!==7
      ||new Set(layerOrder).size!==7
      ||NAMES.some(name=>!layerOrder.includes(name))
      ||!masks||typeof masks!=="object"
      ||Object.keys(masks).length!==7
      ||NAMES.some(name=>!(masks[name] instanceof Uint8ClampedArray)
        ||masks[name].length!==source.length)){
      throw Error("verified_private_source_and_seven_masks_required");
    }
    const pixels=new Map();
    for(const name of NAMES){
      const mask=masks[name],selected=[];
      for(let p=0;p<width*height;p++){
        const i=p*4,a=mask[i+3];
        if(a!==0&&(mask[i]!==255||mask[i+1]!==255||mask[i+2]!==255)){
          throw Error("white_alpha_mask_only");
        }
        if(a>=128)selected.push(p);
      }
      if(!selected.length)throw Error("empty_private_source_mask");
      pixels.set(name,selected);
    }
    let epoch=0,stopped=false;
    function stop(){
      epoch+=1;stopped=true;
      return Object.freeze({epoch,stopped});
    }
    function restart(humanAction){
      if(humanAction!==true||!stopped)return Object.freeze({epoch,stopped});
      epoch+=1;stopped=false;
      return Object.freeze({epoch,stopped});
    }
    function frame({translations={},expectedEpoch=epoch}={}){
      if(stopped||expectedEpoch!==epoch)return null;
      if(!translations||typeof translations!=="object"
        ||Array.isArray(translations)
        ||Object.keys(translations).some(k=>!NAMES.includes(k))){
        throw Error("private_frame_offsets_invalid");
      }
      for(const [name,value] of Object.entries(translations)){
        if(!MOVE.has(name)||!Array.isArray(value)||value.length!==2
          ||value.some(n=>!Number.isInteger(n)||Math.abs(n)>2)){
          throw Error("unapproved_or_unbounded_offset");
        }
      }
      const out=new Uint8ClampedArray(source.length);
      for(const name of layerOrder){
        const [dx,dy]=translations[name]||[0,0];
        for(const p of pixels.get(name)){
          const x=p%width+dx,y=Math.floor(p/width)+dy;
          if(x<0||x>=width||y<0||y>=height)continue;
          const from=p*4,to=(y*width+x)*4;
          out[to]=source[from];out[to+1]=source[from+1];
          out[to+2]=source[from+2];out[to+3]=255;
        }
      }
      return Object.freeze({width,height,rgba:out,epoch,...NO_APPROVAL});
    }
    return Object.freeze({frame,stop,restart,
      snapshot:()=>Object.freeze({epoch,stopped,...NO_APPROVAL})});
  }
  return Object.freeze({NAMES,create});
});
