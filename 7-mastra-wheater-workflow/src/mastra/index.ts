import { Mastra } from "@mastra/core/mastra";
import { createLogger } from "@mastra/core/logger";
import { weatherWorkflow } from "./workflows";

export const mastra = new Mastra({
  workflows: { weatherWorkflow },

  logger: createLogger({
    name: "Mastra",
    level: "info",
  }),
});
