import { Badge, Button, Card, Input } from "@metacto/ui";
import type { Comment } from "@metacto/api-client";
import { useState } from "react";
import {
  ActivityIndicator,
  Pressable,
  ScrollView,
  Text,
  View,
} from "react-native";
import { useAuth } from "../context/AuthContext";
import { useComments, useDeleteComment, usePostComment } from "../hooks/useComments";
import { useFeatureRequest, useVote } from "../hooks/useFeatureRequests";

interface DetailScreenProps {
  id: string;
  onBack: () => void;
  onAuthRequired: () => void;
}

function CommentItem({
  comment,
  canDelete,
  onDelete,
}: {
  comment: Comment;
  canDelete: boolean;
  onDelete: (id: string) => void;
}) {
  return (
    <View className="py-3 border-b border-gray-100">
      <View className="flex-row items-center justify-between mb-1">
        <Text className="text-xs text-gray-400">
          {new Date(comment.created_at).toLocaleDateString()}
        </Text>
        {canDelete && !comment.is_deleted ? (
          <Pressable onPress={() => onDelete(comment.id)}>
            <Text className="text-xs text-red-400">Delete</Text>
          </Pressable>
        ) : null}
      </View>
      <Text
        className={`text-sm ${comment.is_deleted || comment.is_hidden ? "text-gray-400 italic" : "text-gray-800"}`}
      >
        {comment.body}
      </Text>
    </View>
  );
}

export function DetailScreen({ id, onBack, onAuthRequired }: DetailScreenProps) {
  const { accessToken, isAuthenticated } = useAuth();
  const [commentBody, setCommentBody] = useState("");

  const { data: fr, isLoading: frLoading } = useFeatureRequest(id);
  const { data: commentsPage, isLoading: cmtLoading } = useComments(id);
  const vote = useVote(accessToken);
  const postComment = usePostComment(id, accessToken);
  const deleteComment = useDeleteComment(id, accessToken);

  if (frLoading) {
    return (
      <View className="flex-1 items-center justify-center bg-gray-50">
        <ActivityIndicator size="large" color="#4F46E5" />
      </View>
    );
  }

  if (!fr) {
    return (
      <View className="flex-1 items-center justify-center bg-gray-50 px-6 gap-4">
        <Text className="text-gray-500">Request not found.</Text>
        <Button label="Back" onPress={onBack} variant="outline" />
      </View>
    );
  }

  const handleVote = () => {
    if (!isAuthenticated) { onAuthRequired(); return; }
    vote.mutate({ id: fr.id, hasVoted: fr.viewer_has_voted });
  };

  const handleComment = () => {
    if (!isAuthenticated) { onAuthRequired(); return; }
    if (!commentBody.trim()) return;
    postComment.mutate(commentBody, { onSuccess: () => setCommentBody("") });
  };

  return (
    <View className="flex-1 bg-gray-50">
      {/* Nav bar */}
      <View className="bg-white border-b border-gray-200 px-4 pt-12 pb-3 flex-row items-center gap-3">
        <Pressable onPress={onBack} className="p-1">
          <Text className="text-indigo-600 font-medium">← Back</Text>
        </Pressable>
      </View>

      <ScrollView contentContainerClassName="p-4 gap-4 pb-10">
        {/* Main card */}
        <Card>
          <View className="flex-row items-start justify-between gap-3">
            <Text className="text-lg font-bold text-gray-900 flex-1">{fr.title}</Text>
            <Badge label={fr.status} />
          </View>

          {fr.description ? (
            <Text className="text-gray-600 mt-2 text-sm leading-relaxed">
              {fr.description}
            </Text>
          ) : null}

          <View className="flex-row items-center mt-4 gap-3">
            {/* Vote button */}
            <Pressable
              onPress={handleVote}
              disabled={vote.isPending}
              className={[
                "flex-row items-center gap-1.5 px-4 py-2 rounded-full border",
                fr.viewer_has_voted
                  ? "bg-indigo-600 border-indigo-600"
                  : "bg-white border-gray-300",
              ].join(" ")}
            >
              <Text
                className={`font-bold text-base ${fr.viewer_has_voted ? "text-white" : "text-gray-500"}`}
              >
                ▲
              </Text>
              <Text
                className={`font-semibold text-sm ${fr.viewer_has_voted ? "text-white" : "text-gray-700"}`}
              >
                {fr.vote_count}
              </Text>
            </Pressable>

            <Text className="text-xs text-gray-400">
              {new Date(fr.created_at).toLocaleDateString()}
            </Text>
          </View>
        </Card>

        {/* Comments section */}
        <Card>
          <Text className="font-semibold text-gray-900 mb-3">
            Comments ({commentsPage?.total ?? 0})
          </Text>

          {cmtLoading ? (
            <ActivityIndicator color="#4F46E5" />
          ) : (
            commentsPage?.items.map((c) => (
              <CommentItem
                key={c.id}
                comment={c}
                canDelete={isAuthenticated}
                onDelete={(cid) => deleteComment.mutate(cid)}
              />
            ))
          )}

          {/* Post comment */}
          <View className="mt-4 gap-2">
            <Input
              placeholder={isAuthenticated ? "Add a comment…" : "Log in to comment"}
              value={commentBody}
              onChangeText={setCommentBody}
              multiline
              numberOfLines={3}
            />
            <Button
              label={postComment.isPending ? "Posting…" : "Post Comment"}
              onPress={handleComment}
              disabled={!commentBody.trim() || postComment.isPending}
              loading={postComment.isPending}
            />
          </View>
        </Card>
      </ScrollView>
    </View>
  );
}
