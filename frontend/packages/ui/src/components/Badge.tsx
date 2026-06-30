import { Text, View } from "react-native";

type BadgeVariant = "default" | "success" | "warning" | "danger" | "info";

interface BadgeProps {
  label: string;
  variant?: BadgeVariant;
}

const variantClasses: Record<BadgeVariant, { container: string; text: string }> = {
  default: { container: "bg-gray-100", text: "text-gray-600" },
  success: { container: "bg-emerald-100", text: "text-emerald-700" },
  warning: { container: "bg-amber-100", text: "text-amber-700" },
  danger: { container: "bg-red-100", text: "text-red-700" },
  info: { container: "bg-indigo-100", text: "text-indigo-700" },
};

const STATUS_VARIANT_MAP: Record<string, BadgeVariant> = {
  open: "info",
  under_review: "warning",
  planned: "success",
  in_progress: "success",
  shipped: "success",
  declined: "danger",
  duplicate: "default",
};

export function Badge({ label, variant }: BadgeProps) {
  const resolved = variant ?? STATUS_VARIANT_MAP[label] ?? "default";
  const { container, text } = variantClasses[resolved];
  return (
    <View className={`px-2 py-0.5 rounded-full ${container}`}>
      <Text className={`text-xs font-medium ${text}`}>
        {label.replace(/_/g, " ")}
      </Text>
    </View>
  );
}
