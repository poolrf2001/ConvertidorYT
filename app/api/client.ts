const API_URL = process.env.EXPO_PUBLIC_API_URL ?? "http://localhost:8000";

export type Quality = "128" | "192" | "320";

export type JobFile = {
  index: number;
  title: string;
  size_bytes: number;
};

export type Job = {
  id: string;
  status: "queued" | "running" | "done" | "error";
  progress: number;
  current_title: string;
  error: string | null;
  files: JobFile[];
};

export async function startJob(input: {
  url: string;
  quality: Quality;
  playlist: boolean;
}): Promise<{ job_id: string }> {
  const resp = await fetch(`${API_URL}/api/convert`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
  if (!resp.ok) {
    const detail = await resp.text();
    throw new Error(`Conversion request failed: ${detail}`);
  }
  return resp.json();
}

export async function fetchJob(jobId: string): Promise<Job> {
  const resp = await fetch(`${API_URL}/api/jobs/${jobId}`);
  if (!resp.ok) throw new Error("Failed to fetch job");
  return resp.json();
}

export function downloadUrl(jobId: string, fileIndex: number): string {
  return `${API_URL}/api/download/${jobId}/${fileIndex}`;
}
