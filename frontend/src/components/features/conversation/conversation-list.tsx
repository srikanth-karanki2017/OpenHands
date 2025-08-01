import React, { useState } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import { formatDistanceToNow } from "date-fns";
import { I18nKey } from "#/i18n/declaration";
import { Card, CardContent } from "#/components/ui/card";
import { Button } from "#/components/ui/button";
import { formatDate } from "#/utils/date";

// Mock data for conversation history
// This will be replaced with actual API calls in the future
const mockConversations = [
  {
    id: "conv-1",
    title: "Fix authentication bug in login form",
    lastMessage: "The issue was in the validation logic...",
    createdAt: new Date(Date.now() - 1000 * 60 * 60 * 2), // 2 hours ago
    updatedAt: new Date(Date.now() - 1000 * 60 * 30), // 30 minutes ago
  },
  {
    id: "conv-2",
    title: "Implement new feature for dashboard",
    lastMessage: "I've created the components and added tests...",
    createdAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 2), // 2 days ago
    updatedAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 2), // 2 days ago
  },
  {
    id: "conv-3",
    title: "Refactor database queries for better performance",
    lastMessage: "The optimized queries reduced load time by 40%...",
    createdAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 5), // 5 days ago
    updatedAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 5), // 5 days ago
  },
];

/**
 * Component to display a list of past conversations
 */
export function ConversationList() {
  const { t } = useTranslation();
  const [conversations] = useState(mockConversations);

  if (conversations.length === 0) {
    return (
      <div className="text-center py-10">
        <p className="text-muted-foreground mb-4">
          {t(I18nKey.CONVERSATION$NO_CONVERSATIONS)}
        </p>
        <Button asChild>
          <Link to="/">{t(I18nKey.CONVERSATION$START_NEW_CONVERSATION)}</Link>
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {conversations.map((conversation) => (
        <Card key={conversation.id} className="hover:bg-accent/5 transition-colors">
          <CardContent className="p-4">
            <Link
              to={`/conversation/${conversation.id}`}
              className="block"
            >
              <div className="flex justify-between items-start">
                <div>
                  <h3 className="font-medium text-lg">{conversation.title}</h3>
                  <p className="text-muted-foreground text-sm line-clamp-1 mt-1">
                    {conversation.lastMessage}
                  </p>
                </div>
                <div className="text-right text-sm text-muted-foreground">
                  <div title={formatDate(conversation.updatedAt)}>
                    {formatDistanceToNow(conversation.updatedAt, { addSuffix: true })}
                  </div>
                  <div className="mt-1">
                    {t(I18nKey.CONVERSATION$CREATED)}: {formatDate(conversation.createdAt, "short")}
                  </div>
                </div>
              </div>
            </Link>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}