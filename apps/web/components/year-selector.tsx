export function YearSelector({
  value,
  onChange,
}: {
  value: string;
  onChange: (year: string) => void;
}) {
  return (
    <label>
      Năm tuyển sinh
      <select value={value} onChange={(event) => onChange(event.target.value)}>
        {!["2024", "2025", "2026"].includes(value) && (
          <option value={value}>{value} — không hỗ trợ</option>
        )}
        <option value="2024">2024</option>
        <option value="2025">2025</option>
        <option value="2026">2026</option>
      </select>
    </label>
  );
}
