(function(root,factory){
  const api=factory();
  if(typeof module!=="undefined"&&module.exports)module.exports=api;
  if(root)root.OAP_SMI_LIVE_STATE=api;
})(typeof globalThis!=="undefined"?globalThis:this,function(){
  "use strict";

  function initialState(){
    return {
      state:"ready",
      live:false,
      stopped:false,
      paused:false,
      listening:false,
      thinking:false,
      speaking:false,
      epoch:0,
    };
  }

  function normalize(current){
    return {...initialState(),...(current||{})};
  }

  function transition(current,event){
    const s=normalize(current);
    const type=String(event?.type||"");
    const next={...s};

    if(type==="STOP"){
      return {
        ...next,
        state:"stopped",
        live:false,
        stopped:true,
        paused:false,
        listening:false,
        thinking:false,
        speaking:false,
        epoch:s.epoch+1,
      };
    }

    if(type==="RESUME_FROM_STOP"){
      return {
        ...next,
        state:"ready",
        stopped:false,
        paused:false,
        listening:false,
        thinking:false,
        speaking:false,
        epoch:s.epoch+1,
      };
    }

    if(s.stopped)return next;

    if(type==="LIVE_ON"){
      return {...next,live:true,state:"ready",epoch:s.epoch+1};
    }

    if(type==="LIVE_OFF"){
      return {
        ...next,
        state:"ready",
        live:false,
        paused:false,
        listening:false,
        thinking:false,
        speaking:false,
        epoch:s.epoch+1,
      };
    }

    if(type==="PAUSE"){
      return {
        ...next,
        state:"paused",
        paused:true,
        listening:false,
      };
    }

    if(type==="RESUME"){
      const resumedState=next.speaking?"speaking":next.thinking?"thinking":next.listening?"listening":"ready";
      return {...next,state:resumedState,paused:false};
    }

    if(type==="LISTEN_START"){
      if(next.paused||next.thinking||next.speaking||next.listening)return next;
      return {...next,state:"listening",listening:true};
    }

    if(type==="LISTEN_END"){
      return {
        ...next,
        state:next.paused?"paused":"ready",
        listening:false,
      };
    }

    if(type==="THINK_START"){
      if(next.paused||next.speaking)return next;
      return {
        ...next,
        state:"thinking",
        listening:false,
        thinking:true,
      };
    }

    if(type==="THINK_END"){
      return {
        ...next,
        state:next.paused?"paused":"ready",
        thinking:false,
      };
    }

    if(type==="SPEAK_START"){
      if(next.paused||next.listening)return next;
      return {
        ...next,
        state:"speaking",
        thinking:false,
        speaking:true,
      };
    }

    if(type==="SPEAK_END"){
      return {
        ...next,
        state:next.paused?"paused":"ready",
        speaking:false,
      };
    }

    return next;
  }

  function canListen(state){
    const s=normalize(state);
    return !s.stopped&&!s.paused&&!s.listening&&!s.thinking&&!s.speaking;
  }

  function token(state){
    const s=normalize(state);
    return s.epoch;
  }

  function tokenIsCurrent(state,value){
    const s=normalize(state);
    return s.epoch===value&&!s.stopped;
  }

  return {
    version:"2.0",
    initialState,
    transition,
    canListen,
    token,
    tokenIsCurrent,
  };
});
