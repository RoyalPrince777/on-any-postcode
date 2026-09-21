# SMI real-reply motion bridge v0.2 — no-guess lock

Private candidate for binding bounded character cues to the audio clock of an
actual SMI reply. It is not imported by the live page.

## No-guess rule

The bridge no longer converts letters, words or browser `SpeechSynthesis`
boundary fragments into mouth shapes. It accepts only an integrity-bound
viseme timeline declared as derived from decoded audio. The audio SHA-256,
duration, clock source and canonical timeline hash must agree. Timeline cues
must be ordered, bounded by the audio duration, free of reply text, above the
confidence floor, and begin and end in silence. Text-predicted timelines and
approval claims fail closed.

Playback starts only on an observed `playing` event with the declared audio
clock. Every cue is selected from that timeline using the monotonically
advancing played-audio clock. Clock reversal, overrun or drift above 80 ms
stops the candidate and invalidates its epoch. Human STOP also invalidates the
epoch and blocks stale callbacks until an explicit Human reset.

The bridge retains no reply text or audio. It never marks production, Founder
Final, accurate lip-sync or physical Android STOP as proven.

## Evidence boundary

This contract prevents the previous text-to-mouth guess. It does **not** prove
that a real aligner produced the declared timeline, that audio was audible,
that the approved character moved correctly, or that Android STOP completed
under 50 ms. Those require a real SMI audio generator/alignment receipt, live
browser observation, physical Android evidence and Founder Final. Until then,
the bridge remains private and non-production.
