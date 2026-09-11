// Diagonal amber/black hazard-tape bar -- the one deliberate warm
// intrusion into an otherwise cold system, reserved for danger/critical
// signal (a high-severity finding, a failed verdict, a system alert).
export function HazardStripe({ className = "" }: { className?: string }) {
  return <span aria-hidden="true" className={`hazard-stripe block ${className}`} />;
}
