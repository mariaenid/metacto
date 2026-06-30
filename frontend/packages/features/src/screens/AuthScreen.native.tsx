import { Button, Card, Input } from "@metacto/ui";
import { useState } from "react";
import { KeyboardAvoidingView, Platform, Pressable, ScrollView, Text, View } from "react-native";
import { useAuth } from "../context/AuthContext";

type Tab = "login" | "register";

interface AuthScreenProps {
  onSuccess: () => void;
  onBack?: () => void;
}

export function AuthScreen({ onSuccess, onBack }: AuthScreenProps) {
  const [tab, setTab] = useState<Tab>("login");
  const [email, setEmail] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [registered, setRegistered] = useState(false);

  const { login, register } = useAuth();

  const handleLogin = async () => {
    if (!email || !password) { setError("Email and password are required."); return; }
    setError(""); setLoading(true);
    try {
      await login(email, password);
      onSuccess();
    } catch (e) {
      setError((e as Error).message ?? "Login failed.");
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async () => {
    if (!email || !displayName || !password) {
      setError("All fields are required.");
      return;
    }
    if (password.length < 8) { setError("Password must be at least 8 characters."); return; }
    setError(""); setLoading(true);
    try {
      await register(email, displayName, password);
      setRegistered(true);
    } catch (e) {
      setError((e as Error).message ?? "Registration failed.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView
      className="flex-1 bg-gray-50"
      behavior={Platform.OS === "ios" ? "padding" : "height"}
    >
      {/* Nav */}
      {onBack ? (
        <View className="px-4 pt-12 pb-3">
          <Pressable onPress={onBack}>
            <Text className="text-indigo-600 font-medium">← Back</Text>
          </Pressable>
        </View>
      ) : null}

      <ScrollView
        contentContainerClassName="flex-1 p-6 justify-center"
        keyboardShouldPersistTaps="handled"
      >
        <Text className="text-3xl font-bold text-gray-900 text-center mb-2">
          metaCTO
        </Text>
        <Text className="text-gray-500 text-center mb-8">Feature Voting</Text>

        {/* Tab bar */}
        <View className="flex-row bg-gray-100 rounded-xl p-1 mb-6">
          {(["login", "register"] as Tab[]).map((t) => (
            <Pressable
              key={t}
              onPress={() => { setTab(t); setError(""); setRegistered(false); }}
              className={[
                "flex-1 py-2 rounded-lg items-center",
                tab === t ? "bg-white shadow-sm" : "",
              ].join(" ")}
            >
              <Text
                className={`font-semibold text-sm capitalize ${tab === t ? "text-gray-900" : "text-gray-500"}`}
              >
                {t}
              </Text>
            </Pressable>
          ))}
        </View>

        <Card>
          {registered ? (
            <View className="items-center gap-4 py-4">
              <Text className="text-4xl">✉️</Text>
              <Text className="text-lg font-semibold text-gray-900 text-center">
                Check your inbox
              </Text>
              <Text className="text-gray-500 text-sm text-center">
                We sent a verification link to {email}. Click it to activate your account, then log in.
              </Text>
              <Button
                label="Go to Login"
                onPress={() => { setTab("login"); setRegistered(false); }}
                variant="outline"
              />
            </View>
          ) : (
            <View className="gap-4">
              <Input
                label="Email"
                value={email}
                onChangeText={setEmail}
                placeholder="you@example.com"
                keyboardType="email-address"
                autoCapitalize="none"
              />

              {tab === "register" ? (
                <Input
                  label="Display name"
                  value={displayName}
                  onChangeText={setDisplayName}
                  placeholder="Your name"
                />
              ) : null}

              <Input
                label="Password"
                value={password}
                onChangeText={setPassword}
                placeholder="••••••••"
                secureTextEntry
              />

              {error ? (
                <View className="bg-red-50 rounded-lg p-3">
                  <Text className="text-red-600 text-sm">{error}</Text>
                </View>
              ) : null}

              <Button
                label={
                  loading
                    ? tab === "login" ? "Signing in…" : "Creating account…"
                    : tab === "login" ? "Sign In" : "Create Account"
                }
                onPress={tab === "login" ? handleLogin : handleRegister}
                loading={loading}
                disabled={loading}
              />
            </View>
          )}
        </Card>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}
