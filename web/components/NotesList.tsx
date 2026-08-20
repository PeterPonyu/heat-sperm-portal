export function NotesList({ notes }: { notes: string[] }) {
  if (!notes.length) return null;
  return (
    <ul className="notes">
      {notes.map((note) => (
        <li key={note}>{note}</li>
      ))}
    </ul>
  );
}
