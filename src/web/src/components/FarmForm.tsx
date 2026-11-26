import { useState, type FormEvent } from "react";
import { uploadFarm, type Producer } from "../services/api";
import Notice, { type NoticeState } from "./Notice";
import "../styles/Forms.css";

export default function FarmForm({ producers }: { producers: Producer[] }) {
  const [producerId, setProducerId] = useState("");
  const [name, setName] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [fileKey, setFileKey] = useState(0); // para limpiar el input file
  const [loading, setLoading] = useState(false);
  const [notice, setNotice] = useState<NoticeState | null>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!file) {
      setNotice({ type: "error", text: "Selecciona un archivo .geojson." });
      return;
    }
    if (!/\.(geo)?json$/i.test(file.name)) {
      setNotice({ type: "error", text: "El archivo debe tener extensión .geojson (o .json)." });
      return;
    }
    setLoading(true);
    setNotice(null);
    try {
      const farm = await uploadFarm(producerId, name.trim(), file);
      const area = farm.properties?.area_ha;
      setNotice({
        type: "success",
        text:
          `Finca "${name.trim()}" guardada.` +
          (area !== undefined ? ` Área calculada: ${area.toLocaleString("es-CO")} ha.` : ""),
      });
      setName("");
      setFile(null);
      setFileKey((k) => k + 1);
    } catch (err) {
      setNotice({ type: "error", text: (err as Error).message });
    } finally {
      setLoading(false);
    }
  }

  return (
    <form className="form" onSubmit={handleSubmit}>
      <h2>Subir finca</h2>
      <label>
        Productor
        <select value={producerId} onChange={(e) => setProducerId(e.target.value)} required>
          <option value="" disabled>
            {producers.length ? "Selecciona un productor" : "No hay productores aún"}
          </option>
          {producers.map((p) => (
            <option key={p.id} value={p.id}>
              {p.full_name} ({p.document_number})
            </option>
          ))}
        </select>
      </label>
      <label>
        Nombre de la finca
        <input value={name} onChange={(e) => setName(e.target.value)} required />
      </label>
      <label>
        Polígono (.geojson)
        <input
          key={fileKey}
          type="file"
          accept=".geojson,.json,application/geo+json,application/json"
          onChange={(e) => setFile(e.target.files?.[0] ?? null)}
          required
        />
      </label>
      <button type="submit" disabled={loading || !producers.length}>
        {loading ? "Subiendo…" : "Subir finca"}
      </button>
      <Notice notice={notice} />
    </form>
  );
}