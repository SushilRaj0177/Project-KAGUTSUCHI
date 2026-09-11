// Corner-bracket frame -- the "⌐ L ⌐ J" marks from the reference boards,
// used to imply a panel is an instrument readout rather than a plain
// box. Wraps children; brackets are absolutely positioned so they don't
// affect layout. `inset` pushes them slightly outside the content edge,
// matching the reference's habit of letting brackets float just past
// the panel they frame.
//
// Carries the `.hud-button` interaction classes (see globals.css) by
// default: brackets extend and brighten to cyan on hover/focus, and the
// whole frame lifts slightly. A bordered box with zero response to the
// pointer is exactly the kind of thing that reads as "document" rather
// than "system" -- pass `interactive={false}` to opt out for a purely
// decorative frame.
export function CornerBrackets({
  children,
  className = "",
  armLength = 10,
  inset = -6,
  interactive = true,
}: {
  children: React.ReactNode;
  className?: string;
  armLength?: number;
  inset?: number;
  interactive?: boolean;
}) {
  const arm = `absolute border-current ${interactive ? "hud-bracket" : ""}`;
  const style = { width: armLength, height: armLength };
  return (
    <div className={`relative ${interactive ? "hud-button" : ""} ${className}`}>
      <span
        className={`${arm} hud-bracket-tl border-l border-t`}
        style={{ ...style, top: inset, left: inset }}
        aria-hidden="true"
      />
      <span
        className={`${arm} hud-bracket-tr border-r border-t`}
        style={{ ...style, top: inset, right: inset }}
        aria-hidden="true"
      />
      <span
        className={`${arm} hud-bracket-bl border-l border-b`}
        style={{ ...style, bottom: inset, left: inset }}
        aria-hidden="true"
      />
      <span
        className={`${arm} hud-bracket-br border-r border-b`}
        style={{ ...style, bottom: inset, right: inset }}
        aria-hidden="true"
      />
      {children}
    </div>
  );
}
