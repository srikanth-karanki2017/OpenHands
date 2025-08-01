import React from "react";
import { useTranslation } from "react-i18next";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { I18nKey } from "#/i18n/declaration";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "#/components/ui/dialog";
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "#/components/ui/form";
import { Input } from "#/components/ui/input";
import { Button } from "#/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "#/components/ui/select";
import { Checkbox } from "#/components/ui/checkbox";
import { WebhookConfig, WebhookEventType } from "#/types/webhook";
import { useCreateWebhook } from "#/hooks/mutation/use-create-webhook";
import { useUpdateWebhook } from "#/hooks/mutation/use-update-webhook";

// Form schema for webhook configuration
const formSchema = z.object({
  name: z.string().min(1, "Name is required"),
  url: z.string().url("Must be a valid URL"),
  events: z.array(z.string()).min(1, "At least one event must be selected"),
  repository: z.string().optional(),
  secret: z.string().optional(),
  status: z.enum(["active", "inactive"]).default("active"),
});

type FormValues = z.infer<typeof formSchema>;

interface WebhookFormProps {
  webhook: WebhookConfig | null;
  onClose: () => void;
}

/**
 * WebhookForm component for creating and editing webhook configurations.
 */
export function WebhookForm({ webhook, onClose }: WebhookFormProps) {
  const { t } = useTranslation();
  const createWebhook = useCreateWebhook();
  const updateWebhook = useUpdateWebhook();

  // Available webhook event types
  const eventTypes = [
    { id: "all", label: t(I18nKey.WEBHOOK$ALL_EVENTS) },
    { id: "pull_request", label: t(I18nKey.WEBHOOK$PULL_REQUEST_EVENTS) },
    { id: "push", label: t(I18nKey.WEBHOOK$PUSH_EVENTS) },
    { id: "issue", label: t(I18nKey.WEBHOOK$ISSUE_EVENTS) },
    { id: "comment", label: t(I18nKey.WEBHOOK$COMMENT_EVENTS) },
  ];

  // Initialize form with existing webhook data or defaults
  const form = useForm<FormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: webhook
      ? {
          name: webhook.name,
          url: webhook.url.toString(),
          events: webhook.events.map((e) => e.toString()),
          repository: webhook.repository || "",
          secret: "", // Don't populate secret for security reasons
          status: webhook.status,
        }
      : {
          name: "",
          url: "",
          events: ["all"],
          repository: "",
          secret: "",
          status: "active",
        },
  });

  const onSubmit = async (values: FormValues) => {
    try {
      if (webhook) {
        // Update existing webhook
        await updateWebhook.mutateAsync({
          webhook_id: webhook.webhook_id,
          ...values,
        });
      } else {
        // Create new webhook
        await createWebhook.mutateAsync(values);
      }
      onClose();
    } catch (error) {
      console.error("Error saving webhook:", error);
    }
  };

  return (
    <Dialog open={true} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>
            {webhook
              ? t(I18nKey.WEBHOOK$EDIT_WEBHOOK)
              : t(I18nKey.WEBHOOK$ADD_WEBHOOK)}
          </DialogTitle>
          <DialogDescription>
            {t(I18nKey.WEBHOOK$WEBHOOK_FORM_DESCRIPTION)}
          </DialogDescription>
        </DialogHeader>

        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <FormField
              control={form.control}
              name="name"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>{t(I18nKey.WEBHOOK$NAME)}</FormLabel>
                  <FormControl>
                    <Input placeholder={t(I18nKey.WEBHOOK$NAME_PLACEHOLDER)} {...field} />
                  </FormControl>
                  <FormDescription>
                    {t(I18nKey.WEBHOOK$NAME_DESCRIPTION)}
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="url"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>{t(I18nKey.WEBHOOK$URL)}</FormLabel>
                  <FormControl>
                    <Input
                      placeholder="https://example.com/webhook"
                      {...field}
                    />
                  </FormControl>
                  <FormDescription>
                    {t(I18nKey.WEBHOOK$URL_DESCRIPTION)}
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="events"
              render={() => (
                <FormItem>
                  <div className="mb-4">
                    <FormLabel>{t(I18nKey.WEBHOOK$EVENTS)}</FormLabel>
                    <FormDescription>
                      {t(I18nKey.WEBHOOK$EVENTS_DESCRIPTION)}
                    </FormDescription>
                  </div>
                  {eventTypes.map((event) => (
                    <FormField
                      key={event.id}
                      control={form.control}
                      name="events"
                      render={({ field }) => {
                        return (
                          <FormItem
                            key={event.id}
                            className="flex flex-row items-start space-x-3 space-y-0"
                          >
                            <FormControl>
                              <Checkbox
                                checked={field.value?.includes(event.id)}
                                onCheckedChange={(checked) => {
                                  return checked
                                    ? field.onChange([...field.value, event.id])
                                    : field.onChange(
                                        field.value?.filter(
                                          (value) => value !== event.id
                                        )
                                      );
                                }}
                              />
                            </FormControl>
                            <FormLabel className="font-normal">
                              {event.label}
                            </FormLabel>
                          </FormItem>
                        );
                      }}
                    />
                  ))}
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="repository"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>{t(I18nKey.WEBHOOK$REPOSITORY)}</FormLabel>
                  <FormControl>
                    <Input
                      placeholder="owner/repo"
                      {...field}
                      value={field.value || ""}
                    />
                  </FormControl>
                  <FormDescription>
                    {t(I18nKey.WEBHOOK$REPOSITORY_DESCRIPTION)}
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="secret"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>{t(I18nKey.WEBHOOK$SECRET)}</FormLabel>
                  <FormControl>
                    <Input
                      type="password"
                      placeholder={
                        webhook
                          ? t(I18nKey.WEBHOOK$SECRET_PLACEHOLDER_EDIT)
                          : t(I18nKey.WEBHOOK$SECRET_PLACEHOLDER_NEW)
                      }
                      {...field}
                      value={field.value || ""}
                    />
                  </FormControl>
                  <FormDescription>
                    {t(I18nKey.WEBHOOK$SECRET_DESCRIPTION)}
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="status"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>{t(I18nKey.WEBHOOK$STATUS)}</FormLabel>
                  <Select
                    onValueChange={field.onChange}
                    defaultValue={field.value}
                  >
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue placeholder={t(I18nKey.WEBHOOK$SELECT_STATUS)} />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      <SelectItem value="active">
                        {t(I18nKey.WEBHOOK$ACTIVE)}
                      </SelectItem>
                      <SelectItem value="inactive">
                        {t(I18nKey.WEBHOOK$INACTIVE)}
                      </SelectItem>
                    </SelectContent>
                  </Select>
                  <FormDescription>
                    {t(I18nKey.WEBHOOK$STATUS_DESCRIPTION)}
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={onClose}
              >
                {t(I18nKey.COMMON$CANCEL)}
              </Button>
              <Button
                type="submit"
                disabled={createWebhook.isPending || updateWebhook.isPending}
              >
                {(createWebhook.isPending || updateWebhook.isPending) && (
                  <span className="loading loading-spinner loading-xs mr-2"></span>
                )}
                {webhook
                  ? t(I18nKey.COMMON$SAVE)
                  : t(I18nKey.COMMON$CREATE)}
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}