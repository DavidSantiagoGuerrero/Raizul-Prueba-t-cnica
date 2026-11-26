import { useState, type FormEvent } from "react";
import { createProducer, ApiError, type Producer } from "../services/api";
import Notice, { type NoticeState } from "./Notice";
import "../styles/Forms.css";

export default function ProducerForm({ onCreated }: { onCreated: (p: Producer) => void }) {
  const [documentNumber, setDocumentNumber] = useState("");
  const [fullName, setFullName] = useState("");
  const [municipality, setMunicipality] = useState("");
  const [loading, setLoading] = useState(false);
  const [notice, setNotice] = useState<NoticeState | null>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    setNotice(null);
    try {
      const producer = await createProducer({
        document_number: documentNumber.trim(),
        full_name: fullName.trim(),
        municipality: municipality.trim(),
      });
      setNotice({ type: "success", text: `Productor "${producer.full_name}" creado correctamente.` });
      setDocumentNumber("");
      setFullName("");
      setMunicipality("");
      onCreated(producer);
    } catch (err) {
      const apiErr = err as ApiError;
      const text =
        apiErr.status === 409
          ? `Ya existe un productor con el documento ${documentNumber.trim()}. Usa un número distinto.`
          : apiErr.message;
      setNotice({ type: "error", text });
    } finally {
      setLoading(false);
    }
  }

  return (
    <form className="form" onSubmit={handleSubmit}>
      <h2>Crear productor</h2>
      <label>
        Número de documento
        <input value={documentNumber} onChange={(e) => setDocumentNumber(e.target.value)} required />
      </label>
      <label>
        Nombre completo
        <input value={fullName} onChange={(e) => setFullName(e.target.value)} required />
      </label>
      <label>
        Municipio
        <input value={municipality} onChange={(e) => setMunicipality(e.target.value)} required />
      </label>
      <button type="submit" disabled={loading}>
        {loading ? "Guardando…" : "Crear productor"}
      </button>
      <Notice notice={notice} />
    </form>
  );
}