import { Badge, Button, Card } from "@metacto/ui";
import type { FeatureRequest, SortOption } from "@metacto/api-client";
import { useState } from "react";
import { ActivityIndicator, FlatList, Pressable, Text, View } from "react-native";
import { useFeatureRequests } from "../hooks/useFeatureRequests";

const SORTS: { label: string; value: SortOption }[] = [
  { label: "Top", value: "top" },
  { label: "Hot", value: "hot" },
  { label: "New", value: "new" },
];

interface FeedScreenProps {
  onSelectRequest: (id: string) => void;
  onSubmit: () => void;
}

function RequestCard({
  item,
  onPress,
}: {
  item: FeatureRequest;
  onPress: () => void;
}) {
  return (
    <Pressable onPress={onPress} className="active:opacity-70">
      <Card className="mb-3">
        <View className="flex-row items-start justify-between gap-3">
          <View className="flex-1">
            <Text className="text-base font-semibold text-gray-900" numberOfLines={2}>
              {item.title}
            </Text>
            {item.description ? (
              <Text className="text-sm text-gray-500 mt-1" numberOfLines={2}>
                {item.description}
              </Text>
            ) : null}
          </View>
          <View className="items-center min-w-[48px]">
            <Text className="text-lg font-bold text-indigo-600">{item.vote_count}</Text>
            <Text className="text-xs text-gray-400">votes</Text>
          </View>
        </View>
        <View className="flex-row items-center mt-3 gap-2">
          <Badge label={item.status} />
          <Text className="text-xs text-gray-400 ml-auto">
            {new Date(item.created_at).toLocaleDateString()}
          </Text>
        </View>
      </Card>
    </Pressable>
  );
}

export function FeedScreen({ onSelectRequest, onSubmit }: FeedScreenProps) {
  const [sort, setSort] = useState<SortOption>("top");
  const { data, isLoading, isError, refetch } = useFeatureRequests(sort);

  return (
    <View className="flex-1 bg-gray-50">
      {/* Header */}
      <View className="bg-white border-b border-gray-200 px-4 pt-12 pb-3">
        <View className="flex-row items-center justify-between mb-3">
          <Text className="text-xl font-bold text-gray-900">Feature Requests</Text>
          <Button label="+ Submit" onPress={onSubmit} size="sm" />
        </View>

        {/* Sort selector */}
        <View className="flex-row gap-2">
          {SORTS.map((s) => (
            <Pressable
              key={s.value}
              onPress={() => setSort(s.value)}
              className={[
                "px-3 py-1.5 rounded-full border",
                sort === s.value
                  ? "bg-indigo-600 border-indigo-600"
                  : "bg-white border-gray-300",
              ].join(" ")}
            >
              <Text
                className={`text-sm font-medium ${sort === s.value ? "text-white" : "text-gray-600"}`}
              >
                {s.label}
              </Text>
            </Pressable>
          ))}
        </View>
      </View>

      {/* Content */}
      {isLoading ? (
        <View className="flex-1 items-center justify-center">
          <ActivityIndicator size="large" color="#4F46E5" />
        </View>
      ) : isError ? (
        <View className="flex-1 items-center justify-center px-6 gap-4">
          <Text className="text-gray-500 text-center">Failed to load requests.</Text>
          <Button label="Retry" onPress={() => refetch()} variant="outline" />
        </View>
      ) : (
        <FlatList
          data={data?.items}
          keyExtractor={(item) => item.id}
          renderItem={({ item }) => (
            <RequestCard item={item} onPress={() => onSelectRequest(item.id)} />
          )}
          contentContainerClassName="px-4 pt-4 pb-8"
          ListEmptyComponent={
            <View className="items-center py-16">
              <Text className="text-gray-400 text-base">No feature requests yet.</Text>
              <Text className="text-gray-400 text-sm mt-1">Be the first to submit one!</Text>
            </View>
          }
          onRefresh={() => refetch()}
          refreshing={isLoading}
        />
      )}
    </View>
  );
}
