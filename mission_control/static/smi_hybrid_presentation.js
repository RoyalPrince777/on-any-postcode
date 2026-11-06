/* SMI presentation preference: preserve the Founder's approved source-pixel avatar.
 * No new renderer, character assets, speech engine, or production claim.
 */
(function(root,factory){
  "use strict";
  const api=factory();
  if(typeof module!=="undefined"&&module.exports)module.exports=api;
  if(root)root.OAP_SMI_HYBRID_PRESENTATION=api;
})(typeof globalThis!=="undefined"?globalThis:this,function(){
  "use strict";
  const ORIGINAL="original_avatar";
  const MODES=Object.freeze([ORIGINAL,"realistic3d","animated_cartoon"]);
  function create(options){
    const opts=options||{};
    let mode=ORIGINAL,stopped=false;
    function snapshot(){
      return Object.freeze({
        mode,availableModes:MODES,defaultMode:ORIGINAL,
        rendererOwner:"smi_source_pixel_motion",brainOwner:"smi",stopped,
        sevenLayerRigPreserved:true,
        optionalStylesImplemented:false,
        visualRuntimeVerified:false,physicalDeviceVerified:false,
        productionApproved:false
      });
    }
    function select(requested){
      if(stopped||!MODES.includes(requested))return snapshot();
      // Experimental modes are not activated without an explicit supported renderer.
      if(requested!==ORIGINAL&&opts.allowExperimentalStyles!==true)return snapshot();
      mode=requested;
      return snapshot();
    }
    function stop(){
      stopped=true;
      try{opts.onStop?.();}catch(_error){/* STOP remains latched */}
      return snapshot();
    }
    function resetAfterHumanAction(approved){
      if(approved===true&&stopped)stopped=false;
      return snapshot();
    }
    return Object.freeze({select,snapshot,stop,resetAfterHumanAction});
  }
  return Object.freeze({version:"0.2",modes:MODES,create});
});
