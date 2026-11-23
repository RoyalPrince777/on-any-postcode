/* Original-pixel private draft layer extraction. No image synthesis or motion.
 * Called only after the approved JPG's SHA-256 has been verified in the
 * Founder workbench. Binary alpha avoids inventing blend/hidden RGB values.
 */
(function(root,factory){
  "use strict";
  const api=factory();
  if(typeof module!=="undefined"&&module.exports)module.exports=api;
  if(root)root.OAP_SMI_SOURCE_PIXELS=api;
})(typeof globalThis!=="undefined"?globalThis:this,function(){
  "use strict";
  const MAX_PIXELS=16000000;
  function extract(original,mask,width,height){
    if(!Number.isSafeInteger(width)||!Number.isSafeInteger(height)
      ||width<1||height<1||width*height>MAX_PIXELS
      ||!(original instanceof Uint8ClampedArray)
      ||!(mask instanceof Uint8ClampedArray)
      ||original.length!==width*height*4||mask.length!==original.length){
      throw Error("source_or_mask_canvas_invalid");
    }
    let left=width,top=height,right=0,bottom=0,selected=0;
    for(let p=0;p<width*height;p++){
      const i=p*4,a=mask[i+3];
      if(a!==0&&(mask[i]!==255||mask[i+1]!==255||mask[i+2]!==255)){
        throw Error("mask_must_be_white_alpha");
      }
      if(a>=128){
        const x=p%width,y=Math.floor(p/width);
        left=Math.min(left,x);top=Math.min(top,y);
        right=Math.max(right,x+1);bottom=Math.max(bottom,y+1);
        selected++;
      }
    }
    if(!selected)throw Error("empty_original_pixel_layer");
    const w=right-left,h=bottom-top,out=new Uint8ClampedArray(w*h*4);
    for(let y=top;y<bottom;y++)for(let x=left;x<right;x++){
      const from=(y*width+x)*4,to=((y-top)*w+x-left)*4;
      if(mask[from+3]>=128){
        out[to]=original[from];out[to+1]=original[from+1];
        out[to+2]=original[from+2];out[to+3]=255;
      }
    }
    return {bbox_xyxy:[left,top,right,bottom],width:w,height:h,
      selected_pixels:selected,rgba:out,alpha_rule:"binary_threshold_128_draft"};
  }
  return Object.freeze({extract,MAX_PIXELS});
});
