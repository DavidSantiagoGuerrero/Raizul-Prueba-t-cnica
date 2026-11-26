export const API_URL = import.meta.env.VITE_API_URL ?? "/api";

export interface Producer {
  id: number | string;
  document_number: string;
  full_name: string;
  municipality: string;
  created_at: string;
}

export interface ProducerInput {
  document_number: string;
  full_name: string;
  municipality: string;
}

export interface FarmFeature {
  type: "Feature";
  geometry: { type: "Polygon"; coordinates: number[][][] };
  properties: { name: string; area_ha: number };
}

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

// Convierte la respuesta de error de FastAPI ({detail: string | [{loc,msg}]}) en texto legible.
async function readError(res: Response): Promise<string> {
  let detail: unknown;
  try {
    detail = (await res.json()).detail;
  } catch {
    /* sin cuerpo JSON */
  }
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((d: { loc?: (string | number)[]; msg?: string }) => {
        const field = d.loc?.filter((p) => p !== "body").join(".");
        return field ? `${field}: ${d.msg}` : d.msg;
      })
      .join("; ");
  }
  return `Error ${res.status} del servidor.`;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${API_URL}${path}`, init);
  } catch {
    throw new ApiError(0, "No se pudo conectar con el servidor. Verifica que la API esté en ejecución.");
  }
  if (!res.ok) throw new ApiError(res.status, await readError(res));
  return res.json() as Promise<T>;
}

export const listProducers = () => request<Producer[]>("/producers");

export const createProducer = (data: ProducerInput) =>
  request<Producer>("/producers", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });

export const uploadFarm = (producerId: number | string, name: string, file: File) => {
  const body = new FormData();
  body.append("name", name);
  body.append("file", file);
  return request<Partial<FarmFeature>>(`/producers/${producerId}/farm`, { method: "POST", body });
};

export const getFarm = (producerId: number | string) =>
  request<FarmFeature>(`/producers/${producerId}/farm`);