import { Alert, Platform, Pressable, StyleSheet, Text, View } from "react-native";
import * as FileSystem from "expo-file-system";
import * as MediaLibrary from "expo-media-library";
import { downloadUrl, type Job } from "../api/client";

type Props = { job: Job | null };

async function saveOnDevice(url: string, filename: string) {
  const { status } = await MediaLibrary.requestPermissionsAsync();
  if (status !== "granted") {
    Alert.alert("Permiso requerido", "Concede acceso a la biblioteca para guardar el MP3.");
    return;
  }
  const target = `${FileSystem.documentDirectory}${filename}`;
  const { uri } = await FileSystem.downloadAsync(url, target);
  await MediaLibrary.saveToLibraryAsync(uri);
  Alert.alert("Guardado", `${filename} guardado en tu biblioteca.`);
}

export function JobProgress({ job }: Props) {
  if (!job) return null;

  if (job.status === "error") {
    return (
      <View style={[styles.card, styles.cardError]}>
        <Text style={styles.errorText}>Error: {job.error ?? "desconocido"}</Text>
      </View>
    );
  }

  const isRunning = job.status === "queued" || job.status === "running";

  return (
    <View style={styles.card}>
      <Text style={styles.title}>
        Estado: {job.status} {isRunning ? `(${job.progress.toFixed(0)}%)` : ""}
      </Text>
      {job.current_title ? (
        <Text style={styles.subtitle}>Procesando: {job.current_title}</Text>
      ) : null}

      <View style={styles.progressOuter}>
        <View style={[styles.progressInner, { width: `${Math.min(100, job.progress)}%` }]} />
      </View>

      {job.files.length > 0 ? (
        <View style={styles.fileList}>
          <Text style={styles.title}>Archivos listos</Text>
          {job.files.map((f) => {
            const url = downloadUrl(job.id, f.index);
            const filename = `${f.title}.mp3`;
            const onPress = () => {
              if (Platform.OS === "web") {
                window.open(url, "_blank");
              } else {
                saveOnDevice(url, filename).catch((e) =>
                  Alert.alert("Error", String(e))
                );
              }
            };
            return (
              <Pressable key={f.index} onPress={onPress} style={styles.fileRow}>
                <Text style={styles.fileTitle} numberOfLines={1}>
                  {f.title}
                </Text>
                <Text style={styles.fileAction}>
                  {Platform.OS === "web" ? "Descargar" : "Guardar"}
                </Text>
              </Pressable>
            );
          })}
        </View>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    marginTop: 16,
    padding: 16,
    borderRadius: 10,
    backgroundColor: "#fff",
    borderWidth: 1,
    borderColor: "#eee",
    gap: 8,
  },
  cardError: { backgroundColor: "#fef2f2", borderColor: "#fecaca" },
  title: { fontSize: 14, fontWeight: "700", color: "#111" },
  subtitle: { fontSize: 13, color: "#555" },
  errorText: { color: "#991b1b", fontSize: 14 },
  progressOuter: {
    height: 8,
    borderRadius: 4,
    backgroundColor: "#eee",
    overflow: "hidden",
  },
  progressInner: { height: 8, backgroundColor: "#e11d48" },
  fileList: { marginTop: 12, gap: 6 },
  fileRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingVertical: 10,
    paddingHorizontal: 12,
    backgroundColor: "#f9fafb",
    borderRadius: 8,
  },
  fileTitle: { flex: 1, fontSize: 14, color: "#111", marginRight: 12 },
  fileAction: { color: "#e11d48", fontWeight: "700" },
});
