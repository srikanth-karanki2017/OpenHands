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
        path: "conversation/:conversationId",
        element: <Conversation />,
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
            path: "git",
            element: <GitSettings />,
          },
          {
            path: "llm",
            element: <LlmSettings />,
          },
          {
            path: "app",
            element: <AppSettings />,
          },
          {
            path: "webhooks",
            element: <WebhookSettings />,
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
