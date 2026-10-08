# Piano keyboard update-depth regression

## Root cause

`PianoKeyboard` has an effect that derives `currentKeyMap` from `timelineNotes`. Its callers on Studio learn, practice, and perform screens commonly omit `timelineNotes`. A destructuring default of `[]` created a new array on every render, so the effect dependency changed on every render and called `setCurrentKeyMap` again indefinitely.

The empty defaults are now module-level stable references. MIDI and keyboard listeners remain inside the mount effect and are not recreated by this change.

## Reproduction

1. Start the frontend with `cd frontend && npm run dev -- --host 0.0.0.0`.
2. Open `/studio/<song-id>` or authenticate and open `/learn`.
3. Before the fix, the browser console repeatedly reported `Maximum update depth exceeded` and the Vite terminal accumulated the same error.
4. After the fix, reload the route and confirm no update-depth errors occur during at least two seconds of idle rendering and while switching Studio tabs.

The Google Identity origin warning on `/login` is separate configuration noise and is not an update-depth loop.