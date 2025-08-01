import React from "react";
import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import { PageHeader } from "#/components/shared/page-header";
import { ConversationList } from "#/components/features/conversation/conversation-list";

/**
 * Conversation history page component
 */
export default function ConversationHistory() {
  const { t } = useTranslation();

  return (
    <div className="container mx-auto py-6 space-y-6">
      <PageHeader
        title={t(I18nKey.CONVERSATION$CONVERSATION_HISTORY)}
        description={t(I18nKey.CONVERSATION$VIEW_PAST_CONVERSATIONS)}
      />
      <ConversationList />
    </div>
  );
}