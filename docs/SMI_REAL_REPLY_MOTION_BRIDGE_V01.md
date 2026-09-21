# SMI real-reply motion bridge v0.1

Private candidate for binding bounded character cues to the browser's observed
SpeechSynthesis playback lifecycle for an actual streamed SMI response.

It rejects manual text, short or missing reply identities, absent Human start,
pre-start boundaries, reversed timestamps and every callback after Human STOP.
It retains no reply text or audio. Boundary fragments are classified in memory
and discarded. Every cue remains explicitly non-production and non-final.

This is not accurate phoneme alignment yet: browser boundary quality varies by
engine and device. It therefore remains an Aegis candidate, is not imported by
the live page, and cannot turn body language, Android proof or Founder Final
green by itself.
