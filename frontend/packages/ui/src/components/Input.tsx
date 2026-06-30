import { Text, TextInput, View } from "react-native";

interface InputProps {
  label?: string;
  value: string;
  onChangeText: (text: string) => void;
  placeholder?: string;
  secureTextEntry?: boolean;
  multiline?: boolean;
  numberOfLines?: number;
  error?: string;
  autoCapitalize?: "none" | "sentences" | "words" | "characters";
  keyboardType?: "default" | "email-address" | "numeric";
  className?: string;
}

export function Input({
  label,
  value,
  onChangeText,
  placeholder,
  secureTextEntry,
  multiline,
  numberOfLines = 4,
  error,
  autoCapitalize = "sentences",
  keyboardType = "default",
  className = "",
}: InputProps) {
  return (
    <View className={`gap-1 ${className}`}>
      {label ? (
        <Text className="text-sm font-medium text-gray-700">{label}</Text>
      ) : null}
      <TextInput
        value={value}
        onChangeText={onChangeText}
        placeholder={placeholder}
        placeholderTextColor="#9CA3AF"
        secureTextEntry={secureTextEntry}
        multiline={multiline}
        numberOfLines={multiline ? numberOfLines : undefined}
        autoCapitalize={autoCapitalize}
        keyboardType={keyboardType}
        className={[
          "border rounded-xl px-3 py-2.5 text-sm text-gray-900 bg-white",
          error ? "border-red-400" : "border-gray-300",
          multiline ? "min-h-[96px]" : "",
        ]
          .filter(Boolean)
          .join(" ")}
        textAlignVertical={multiline ? "top" : "center"}
      />
      {error ? (
        <Text className="text-xs text-red-500">{error}</Text>
      ) : null}
    </View>
  );
}
