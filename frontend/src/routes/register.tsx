import React, { useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, useNavigate } from "react-router-dom";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { I18nKey } from "#/i18n/declaration";
import { Button } from "#/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "#/components/ui/card";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "#/components/ui/form";
import { Input } from "#/components/ui/input";
import { useRegister } from "#/hooks/mutation/use-register";
import { useAuth } from "#/hooks/use-auth";
import AllHandsLogo from "#/assets/branding/all-hands-logo.svg?react";

// Form schema for registration
const formSchema = z
  .object({
    username: z
      .string()
      .min(3, "Username must be at least 3 characters")
      .max(50, "Username must be less than 50 characters"),
    email: z.string().email("Invalid email address"),
    password: z
      .string()
      .min(8, "Password must be at least 8 characters"),
    confirmPassword: z.string(),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: "Passwords do not match",
    path: ["confirmPassword"],
  });

type FormValues = z.infer<typeof formSchema>;

/**
 * Registration page component
 */
export default function Register() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const register = useRegister();
  const { isAuthenticated } = useAuth();
  const [error, setError] = useState<string | null>(null);

  // Redirect if already authenticated
  if (isAuthenticated) {
    navigate("/");
    return null;
  }

  // Initialize form
  const form = useForm<FormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      username: "",
      email: "",
      password: "",
      confirmPassword: "",
    },
  });

  const onSubmit = async (values: FormValues) => {
    setError(null);
    try {
      await register.mutateAsync({
        username: values.username,
        email: values.email,
        password: values.password,
      });
      navigate("/login", { state: { registered: true } });
    } catch (err: any) {
      setError(
        err.response?.data?.detail ||
        t(I18nKey.AUTH$REGISTRATION_FAILED)
      );
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-background">
      <div className="w-full max-w-md p-4">
        <Card>
          <CardHeader className="space-y-1 flex flex-col items-center">
            <AllHandsLogo width={68} height={46} className="mb-4" />
            <CardTitle className="text-2xl">
              {t(I18nKey.AUTH$CREATE_ACCOUNT)}
            </CardTitle>
            <CardDescription>
              {t(I18nKey.AUTH$ENTER_DETAILS_TO_REGISTER)}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {error && (
              <div className="p-3 text-sm bg-destructive/10 text-destructive rounded-md">
                {error}
              </div>
            )}
            <Form {...form}>
              <form
                onSubmit={form.handleSubmit(onSubmit)}
                className="space-y-4"
              >
                <FormField
                  control={form.control}
                  name="username"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>{t(I18nKey.AUTH$USERNAME)}</FormLabel>
                      <FormControl>
                        <Input
                          placeholder={t(I18nKey.AUTH$USERNAME_PLACEHOLDER)}
                          {...field}
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="email"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>{t(I18nKey.AUTH$EMAIL)}</FormLabel>
                      <FormControl>
                        <Input
                          type="email"
                          placeholder={t(I18nKey.AUTH$EMAIL_PLACEHOLDER)}
                          {...field}
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="password"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>{t(I18nKey.AUTH$PASSWORD)}</FormLabel>
                      <FormControl>
                        <Input
                          type="password"
                          placeholder={t(I18nKey.AUTH$PASSWORD_PLACEHOLDER)}
                          {...field}
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="confirmPassword"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>{t(I18nKey.AUTH$CONFIRM_PASSWORD)}</FormLabel>
                      <FormControl>
                        <Input
                          type="password"
                          placeholder={t(I18nKey.AUTH$CONFIRM_PASSWORD_PLACEHOLDER)}
                          {...field}
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <Button
                  type="submit"
                  className="w-full"
                  disabled={register.isPending}
                >
                  {register.isPending ? (
                    <span className="loading loading-spinner loading-xs mr-2"></span>
                  ) : null}
                  {t(I18nKey.AUTH$REGISTER)}
                </Button>
              </form>
            </Form>
          </CardContent>
          <CardFooter className="flex flex-col space-y-4">
            <div className="text-sm text-center text-muted-foreground">
              {t(I18nKey.AUTH$ALREADY_HAVE_ACCOUNT)}{" "}
              <Link
                to="/login"
                className="text-primary underline hover:text-primary/80"
              >
                {t(I18nKey.AUTH$LOGIN)}
              </Link>
            </div>
          </CardFooter>
        </Card>
      </div>
    </div>
  );
}
