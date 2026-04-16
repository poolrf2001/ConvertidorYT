import { useState } from "react";
import {
  Pressable,
  StyleSheet,
  Switch,
  Text,
  TextInput,
  View,
} from "react-native";
import type { Quality } from "../api/client";

type Props = {
  disabled: boolean;
  onSubmit: (input: { url: string; quality: Quality; playlist: boolean }) => void;
};

const QUALITIES: Quality[] = ["128", "192", "320"];

export function ConverterForm({ disabled, onSubmit }: Props) {
  const [url, setUrl] = useState("");
  const [quality, setQuality] = useState<Quality>("192");
  const [playlist, setPlaylist] = useState(false);

  const canSubmit = !disabled && url.trim().length > 0;

  return (
    <View style={styles.container}>
      <Text style={styles.label}>URL de YouTube</Text>
      <TextInput
        value={url}
        onChangeText={setUrl}
        placeholder="https://www.youtube.com/watch?v=..."
        autoCapitalize="none"
        autoCorrect={false}
        editable={!disabled}
        style={styles.input}
      />

      <Text style={styles.label}>Calidad (kbps)</Text>
      <View style={styles.row}>
        {QUALITIES.map((q) => (
          <Pressable
            key={q}
            onPress={() => setQuality(q)}
            style={[styles.chip, quality === q && styles.chipActive]}
          >
            <Text style={[styles.chipText, quality === q && styles.chipTextActive]}>
              {q}
            </Text>
          </Pressable>
        ))}
      </View>

      <View style={styles.switchRow}>
        <Text style={styles.label}>Descargar playlist completa</Text>
        <Switch value={playlist} onValueChange={setPlaylist} disabled={disabled} />
      </View>

      <Pressable
        onPress={() => canSubmit && onSubmit({ url: url.trim(), quality, playlist })}
        disabled={!canSubmit}
        style={[styles.button, !canSubmit && styles.buttonDisabled]}
      >
        <Text style={styles.buttonText}>Convertir a MP3</Text>
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { gap: 12 },
  label: { fontSize: 14, fontWeight: "600", color: "#333" },
  input: {
    borderWidth: 1,
    borderColor: "#ccc",
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 10,
    fontSize: 16,
    backgroundColor: "#fff",
  },
  row: { flexDirection: "row", gap: 8 },
  chip: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: "#ccc",
  },
  chipActive: { backgroundColor: "#e11d48", borderColor: "#e11d48" },
  chipText: { color: "#333", fontWeight: "500" },
  chipTextActive: { color: "#fff" },
  switchRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginTop: 4,
  },
  button: {
    marginTop: 8,
    backgroundColor: "#e11d48",
    paddingVertical: 14,
    borderRadius: 8,
    alignItems: "center",
  },
  buttonDisabled: { backgroundColor: "#aaa" },
  buttonText: { color: "#fff", fontSize: 16, fontWeight: "700" },
});
