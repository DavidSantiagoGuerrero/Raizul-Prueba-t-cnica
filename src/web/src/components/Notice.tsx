export interface NoticeState {
  type: "success" | "error";
  text: string;
}

export default function Notice({ notice }: { notice: NoticeState | null }) {
  if (!notice) return null;
  return (
    <div className={`notice notice-${notice.type}`} role={notice.type === "error" ? "alert" : "status"}>
      <strong>{notice.type === "success" ? "Listo: " : "No se pudo completar: "}</strong>
      {notice.text}
    </div>
  );
}