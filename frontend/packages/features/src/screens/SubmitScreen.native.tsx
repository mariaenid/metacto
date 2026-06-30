import { Button, Card, Input } from "@metacto/ui";
import { useState } from "react";
import { KeyboardAvoidingView, Platform, ScrollView, Text, View } from "react-native";
import { useAuth } from "../context/AuthContext";
import { useSubmitFeatureRequest } from "../hooks/useFeatureRequests";

interface SubmitScreenProps {
  onSuccess: () => void;
  onBack: () => void;
  onAuthRequired: () => void;
}

export function SubmitScreen({ onSuccess, onBack, onAuthRequired }: SubmitScreenProps) {
  const { accessToken, isAuthenticated } = useAuth();
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [titleError, setTitleError] = useState("");

  const submit = useSubmitFeatureRequest(accessToken);

  const handleSubmit = () => {
    if (!isAuthenticated) { onAuthRequired(); return; }

    if (title.trim().length < 5) {
      setTitleError("Title must be at least 5 characters.");
      return;
    }
    setTitleError("");

    submit.mutate(
      { title: title.trim(), description: description.trim() },
      { onSuccess: () => { onSuccess(); } },
    );
  };

  return (
    <KeyboardAvoidingView
      className="flex-1 bg-gray-50"
      behavior={Platform.OS === "ios" ? "padding" : "height"}
    >
      {/* Nav */}
      <View className="bg-white border-b border-gray-200 px-4 pt-12 pb-3">
        <Text className="text-indigo-600 font-medium" onPress={onBack}>
          ← Back
        </Text>
        <Text className="text-xl font-bold text-gray-900 mt-2">Submit Feature Request</Text>
      </View>

      <ScrollView contentContainerClassName="p-4 gap-4 pb-10">
        <Card>
          <View className="gap-4">
            <Input
              label="Title *"
              value={title}
              onChangeText={setTitle}
              placeholder="Describe the feature in one line"
              error={titleError}
            />

            <Input
              label="Description"
              value={description}
              onChangeText={setDescription}
              placeholder="Explain the problem this solves and any relevant context…"
              multiline
              numberOfLines={6}
            />

            {submit.isError ? (
              <View className="bg-red-50 rounded-lg p-3">
                <Text className="text-red-600 text-sm">
                  {(submit.error as Error)?.message ?? "Submission failed. Please try again."}
                </Text>
              </View>
            ) : null}

            <Button
              label={submit.isPending ? "Submitting…" : "Submit Request"}
              onPress={handleSubmit}
              disabled={submit.isPending}
              loading={submit.isPending}
            />
          </View>
        </Card>

        <Text className="text-xs text-gray-400 text-center">
          You must be logged in and have a verified email to submit.
        </Text>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}
