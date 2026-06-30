import { ActivityIndicator, Pressable, Text } from "react-native";
import { colors } from "../theme";

interface ButtonProps {
  label: string;
  onPress: () => void;
  variant?: "primary" | "outline" | "ghost";
  size?: "sm" | "md" | "lg";
  disabled?: boolean;
  loading?: boolean;
  className?: string;
}

const variantClasses = {
  primary: "bg-indigo-600 active:bg-indigo-700",
  outline: "border border-indigo-600 bg-transparent active:bg-indigo-50",
  ghost: "bg-transparent active:bg-gray-100",
};

const labelClasses = {
  primary: "text-white font-semibold",
  outline: "text-indigo-600 font-semibold",
  ghost: "text-gray-600 font-medium",
};

const sizeClasses = {
  sm: "px-3 py-1.5",
  md: "px-4 py-2.5",
  lg: "px-6 py-3",
};

const labelSizeClasses = {
  sm: "text-sm",
  md: "text-sm",
  lg: "text-base",
};

export function Button({
  label,
  onPress,
  variant = "primary",
  size = "md",
  disabled,
  loading,
  className = "",
}: ButtonProps) {
  return (
    <Pressable
      onPress={onPress}
      disabled={disabled || loading}
      className={[
        "rounded-xl flex-row items-center justify-center",
        variantClasses[variant],
        sizeClasses[size],
        disabled || loading ? "opacity-50" : "",
        className,
      ]
        .filter(Boolean)
        .join(" ")}
    >
      {loading ? (
        <ActivityIndicator
          size="small"
          color={variant === "primary" ? colors.textInverse : colors.primary}
          className="mr-2"
        />
      ) : null}
      <Text className={[labelClasses[variant], labelSizeClasses[size]].join(" ")}>
        {label}
      </Text>
    </Pressable>
  );
}
