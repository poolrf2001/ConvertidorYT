import { useEffect, useRef, useState } from "react";
import { Platform, SafeAreaView, ScrollView, StyleSheet, Text, View } from "react-native";
import { StatusBar } from "expo-status-bar";

import { ConverterForm } from "./components/ConverterForm";
import { JobProgress } from "./components/JobProgress";
import { fetchJob, startJob, type Job, type Quality } from "./api/client";

function setupPwa() {
  if (Platform.OS !== "web" || typeof document === "undefined") return;
  if (!document.querySelector('link[rel="manifest"]')) {
    const link = document.createElement("link");
    link.rel = "manifest";
    link.href = "/manifest.webmanifest";
    document.head.appendChild(link);
  }
  if (!document.querySelector('meta[name="theme-color"]')) {
    const meta = document.createElement("meta");
    meta.name = "theme-color";
    meta.content = "#e11d48";
    document.head.appendChild(meta);
  }
  if ("serviceWorker" in navigator) {
    navigator.serviceWorker.register("/sw.js").catch(() => {});
  }
}

export default function App() {
  const [job, setJob] = useState<Job | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    setupPwa();
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, []);

  const handleSubmit = async (input: {
    url: string;
    quality: Quality;
    playlist: boolean;
  }) => {
    setSubmitting(true);
    setJob(null);
    if (pollRef.current) clearInterval(pollRef.current);
    try {
      const { job_id } = await startJob(input);
      const tick = async () => {
        try {
          const latest = await fetchJob(job_id);
          setJob(latest);
          if (latest.status === "done" || latest.status === "error") {
            if (pollRef.current) clearInterval(pollRef.current);
            pollRef.current = null;
            setSubmitting(false);
          }
        } catch (e) {
          if (pollRef.current) clearInterval(pollRef.current);
          pollRef.current = null;
          setSubmitting(false);
          setJob({
            id: job_id,
            status: "error",
            progress: 0,
            current_title: "",
            error: String(e),
            files: [],
          });
        }
      };
      await tick();
      pollRef.current = setInterval(tick, 1000);
    } catch (e) {
      setSubmitting(false);
      setJob({
        id: "",
        status: "error",
        progress: 0,
        current_title: "",
        error: String(e),
        files: [],
      });
    }
  };

  return (
    <SafeAreaView style={styles.safe}>
      <StatusBar style="dark" />
      <ScrollView contentContainerStyle={styles.container}>
        <View style={styles.header}>
          <Text style={styles.title}>ConvertidorYT</Text>
          <Text style={styles.subtitle}>
            YouTube → MP3 con selección de calidad, metadatos ID3 y soporte de playlists.
          </Text>
        </View>

        <ConverterForm disabled={submitting} onSubmit={handleSubmit} />
        <JobProgress job={job} />

        <Text style={styles.legal}>
          Uso personal/educativo. Respeta los términos de servicio de YouTube y los
          derechos de autor.
        </Text>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: "#f5f5f7" },
  container: {
    maxWidth: 640,
    width: "100%",
    alignSelf: "center",
    padding: 20,
    paddingBottom: 40,
  },
  header: { marginBottom: 20, gap: 6 },
  title: { fontSize: 28, fontWeight: "800", color: "#111" },
  subtitle: { fontSize: 14, color: "#555" },
  legal: { marginTop: 24, fontSize: 12, color: "#777", textAlign: "center" },
});
