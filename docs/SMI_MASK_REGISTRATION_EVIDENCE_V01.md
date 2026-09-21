# SMI mask registration evidence v0.1

This offline gate checks that every required landmark is inside its named
exact-pixel private mask and that mask coverage stays within a conservative
per-layer bound. It rejects swapped labels, missing anchors and oversized
masks that could conceal a full-frame copy.

Passing proves only coordinate-to-mask registration. A coordinate can be
plausible while still being visually wrong, so anatomy, identity quality,
occlusion, motion, played-audio synchronisation and Human Authority approval
remain false. The rig stays inactive and emits no frames.

The AI-produced colour segmentation remains a proposal only. It is not stored
as a production layer, does not replace the approved artwork, and cannot pass
this gate without exact source-pixel extraction and human visual review.
