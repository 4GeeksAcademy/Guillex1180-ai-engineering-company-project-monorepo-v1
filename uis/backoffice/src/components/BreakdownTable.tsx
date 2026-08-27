interface BreakdownTableProps {
  title: string;
  data: Record<string, number>;
  showPercentage?: boolean;
  total?: number;
}

function formatPercentage(value: number, total: number): string {
  if (total <= 0) {
    return "0.0%";
  }
  return `${((value / total) * 100).toFixed(1)}%`;
}

export function BreakdownTable({ title, data, showPercentage = false, total = 0 }: BreakdownTableProps) {
  const entries = Object.entries(data);

  return (
    <section className="panel">
      <h2>{title}</h2>
      {entries.length === 0 ? (
        <p className="helper-text">Sin datos disponibles.</p>
      ) : (
        <table className="breakdown-table">
          <thead>
            <tr>
              <th scope="col">Tipo</th>
              <th scope="col">Cantidad</th>
              {showPercentage ? <th scope="col">Porcentaje</th> : null}
            </tr>
          </thead>
          <tbody>
            {entries.map(([key, value]) => (
              <tr key={key}>
                <th scope="row">{key}</th>
                <td>{value}</td>
                {showPercentage ? <td>{formatPercentage(value, total)}</td> : null}
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}
