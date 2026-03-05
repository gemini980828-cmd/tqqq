type DashboardSnapshot = {
  header?: unknown;
  position_change?: unknown;
  reason?: unknown;
  market_summary?: unknown;
  ops_log?: unknown;
};

export default function Dashboard({ snapshot }: { snapshot?: DashboardSnapshot }) {
  return <pre>{JSON.stringify(snapshot ?? {}, null, 2)}</pre>;
}
