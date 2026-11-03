/* SMI hybrid presentation preference: one existing character/brain, no second renderer.
 * This module selects a presentation request only; it cannot certify runtime motion.
 */
(function(root,factory){
  "use strict";
  const api=factory();
  if(typeof module!=="undefined"&&module.exports)module.exports=api;
  if(root)root.OAP_SMI_HYBRID_PRESENTATION=api;
})(typeof globalThis!=="undefined"?globalThis:this,function(){
  "use strict";
  const MODES=Object.freeze(["realistic3d","animated_cartoon"]);
  function create(options){
    const opts=options||{};
    let mode="realistic3d", stopped=false;
    function select(requested){
      if(stopped)return snapshot();
      if(!MODES.includes(requested))return snapshot();
      mode=requested;
      return snapshot();
    }
    function snapshot(){
      return Object.freeze({
        mode,availableModes:MODES,
        rendererOwner:"smi_source_pixel_motion",
        brainOwner:"smi",stopped,
        visualRuntimeVerified:false,
        physicalDeviceVerified:false,
        productionApproved:false
      });
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
  return Object.freeze({version:"0.1",modes:MODES,create});
});
