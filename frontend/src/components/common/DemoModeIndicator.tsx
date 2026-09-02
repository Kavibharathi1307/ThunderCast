interface DemoModeIndicatorProps {
  demo?: boolean
  note?: string | null
}

/**
 * Placeholder for the demo/fallback indicator.
 *
 * The app now silently degrades to internal fallback data without surfacing
 * "DEMO MODE" messaging to end users; live data is highlighted instead via the
 * dedicated "LIVE WEATHER DATA" indicators elsewhere in the UI. This component
 * is kept as a no-op so call sites and internal data provenance stay intact.
 */
export default function DemoModeIndicator(_props: DemoModeIndicatorProps) {
  return null
}
