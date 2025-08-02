import React, { useState } from "react";
import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "#/components/ui/tabs";
import { PageHeader } from "#/components/shared/page-header";
import { WebhookList } from "#/components/features/settings/webhook-settings/webhook-list";
import { WebhookLogs } from "#/components/features/settings/webhook-settings/webhook-logs";

/**
 * Webhook Settings page component.
 *
 * This page allows users to manage their webhook configurations and view webhook logs.
 */
export default function WebhookSettings() {
  const { t } = useTranslation();
  const [activeTab, setActiveTab] = useState("webhooks");

  return (
    <div className="container max-w-6xl mx-auto py-6 space-y-6">
      <PageHeader
        title={t(I18nKey.WEBHOOK$WEBHOOK_MANAGEMENT)}
        description={t(I18nKey.WEBHOOK$MANAGE_YOUR_WEBHOOKS)}
      />

      <Tabs
        defaultValue="webhooks"
        value={activeTab}
        onValueChange={setActiveTab}
        className="space-y-4 w-full"
      >
        <TabsList>
          <TabsTrigger value="webhooks">
            {t(I18nKey.WEBHOOK$MY_WEBHOOKS)}
          </TabsTrigger>
          <TabsTrigger value="logs">
            {t(I18nKey.WEBHOOK$WEBHOOK_LOGS)}
          </TabsTrigger>
        </TabsList>

        <TabsContent value="webhooks" className="space-y-4">
          <WebhookList />
        </TabsContent>

        <TabsContent value="logs" className="space-y-4">
          <WebhookLogs />
        </TabsContent>
      </Tabs>
    </div>
  );
}
