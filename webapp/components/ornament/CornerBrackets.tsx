// Corner-bracket frame -- the "⌐ L ⌐ J" marks from the reference boards,
// used to imply a panel is an instrument readout rather than a plain
// box. Wraps children; brackets are absolutely positioned so they don't
// affect layout. `inset` pushes them slightly outside the content edge,
// matching the reference's habit of letting brackets float just past
// the panel they frame.
export function CornerBrackets({
  children,
  className = "",
  armLength = 10,
  inset = -6,
}: {
  children: React.ReactNode;
  className?: string;
  armLength?: number;
  inset?: number;
}) {
  const arm = "absolute border-current";
  const style = { width: armLength, height: armLength };
  return (
    <div className={`relative ${className}`}>
      <span
        className={`${arm} border-l border-t`}
        style={{ ...style, top: inset, left: inset }}
        aria-hidden="true"
      />
      <span
        className={`${arm} border-r border-t`}
        style={{ ...style, top: inset, right: inset }}
        aria-hidden="true"
      />
      <span
        className={`${arm} border-l border-b`}
        style={{ ...style, bottom: inset, left: inset }}
        aria-hidden="true"
      />
      <span
        className={`${arm} border-r border-b`}
        style={{ ...style, bottom: inset, right: inset }}
        aria-hidden="true"
      />
      {children}
    </div>
  );
}
