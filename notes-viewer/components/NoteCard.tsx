import type { Note } from "@/lib/notes";

export default function NoteCard({ note }: { note: Note }) {
  const time = new Date(note.date).toLocaleTimeString("en-US", {
    hour: "numeric",
    minute: "2-digit",
    timeZone: "UTC",
  });
  return (
    <article className={note.own ? "note" : "note restack"}>
      <div className="meta">
        <span>{note.date.slice(0, 10)}</span>
        <span>{time} UTC</span>
        {!note.own && (
          <span className="via">
            restacked from {note.author}
            {note.handle ? ` (@${note.handle})` : ""}
          </span>
        )}
      </div>
      {note.body ? (
        <div className="body">{note.body}</div>
      ) : (
        <div className="body empty">[image-only note — no text body]</div>
      )}
      <div className="stats">
        <span>♥ {note.reactions}</span>
        <span>↻ {note.restacks}</span>
        <span>💬 {note.replies}</span>
      </div>
    </article>
  );
}
