import React from "react";
import { createBrowserRouter } from "react-router-dom";
import MultiUserRootLayout from "./routes/multi-user-root-layout";
import Login from "./routes/login";
import Register from "./routes/register";
import Profile from "./routes/profile";
import WebhookSettings from "./routes/webhook-settings";

// Import existing routes
import Home from "./routes/home";
import Settings from "./routes/settings";
import Conversation from "./routes/conversation";
import ConversationHistory from "./routes/conversation-history";
import GitSettings from "./routes/git-settings";
import LlmSettings from "./routes/llm-settings";
import AppSettings from "./routes/app-settings";
import MicroagentManagement from "./routes/microagent-management";
import TermsOfService from "./routes/terms-of-service";
import McpSettings from "./routes/mcp-settings";
import SecretsSettings from "./routes/secrets-settings";
import UserSettings from "./routes/user-settings";
import ApiKeys from "./routes/api-keys";
import Billing from "./routes/billing";
import AcceptTos from "./routes/accept-tos";

// Import conversation tab routes
import ChangesTab from "./routes/changes-tab";
import BrowserTab from "./routes/browser-tab";
import JupyterTab from "./routes/jupyter-tab";
import ServedTab from "./routes/served-tab";
import TerminalTab from "./routes/terminal-tab";
import VscodeTab from "./routes/vscode-tab";

/**
 * Router configuration for the multi-user version of OpenHands
 */
export const router = createBrowserRouter([
  {
    path: "/",
    element: <MultiUserRootLayout />,
    children: [
      {
        index: true,
        element: <Home />,
      },
      {
        path: "login",
        element: <Login />,
      },
      {
        path: "register",
        element: <Register />,
      },
      {
        path: "profile",
        element: <Profile />,
      },
      {
        path: "accept-tos",
        element: <AcceptTos />,
      },
      {
        path: "conversations/:conversationId",
        element: <Conversation />,
        children: [
          {
            index: true,
            element: <ChangesTab />,
          },
          {
            path: "browser",
            element: <BrowserTab />,
          },
          {
            path: "jupyter",
            element: <JupyterTab />,
          },
          {
            path: "served",
            element: <ServedTab />,
          },
          {
            path: "terminal",
            element: <TerminalTab />,
          },
          {
            path: "vscode",
            element: <VscodeTab />,
          },
        ],
      },
      {
        path: "conversation-history",
        element: <ConversationHistory />,
      },
      {
        path: "settings",
        element: <Settings />,
        children: [
          {
            index: true,
            element: <LlmSettings />,
          },
          {
            path: "llm",
            element: <LlmSettings />,
          },
          {
            path: "git",
            element: <GitSettings />,
          },
          {
            path: "mcp",
            element: <McpSettings />,
          },
          {
            path: "user",
            element: <UserSettings />,
          },
          {
            path: "integrations",
            element: <GitSettings />,
          },
          {
            path: "app",
            element: <AppSettings />,
          },
          {
            path: "billing",
            element: <Billing />,
          },
          {
            path: "secrets",
            element: <SecretsSettings />,
          },
          {
            path: "webhooks",
            element: <WebhookSettings />,
          },
          {
            path: "api-keys",
            element: <ApiKeys />,
          },
        ],
      },
      {
        path: "microagent-management",
        element: <MicroagentManagement />,
      },
      {
        path: "terms-of-service",
        element: <TermsOfService />,
      },
    ],
  },
]);
