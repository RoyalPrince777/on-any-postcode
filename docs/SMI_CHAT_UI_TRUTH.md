# SMI Chat UI truth states

Controls must report runtime truth.

Voice: permission required -> listening with elapsed seconds -> captured/edit or send, or blocked/unavailable.

Camera: permission required -> bounded capture -> captured, or blocked/unavailable.

Screen: chooser -> sharing/capturing one frame -> captured, or cancelled/blocked/unavailable.

Send/Stop remain owned by the canonical controller and the governed response stream. No UI state may imply production execution authority.
