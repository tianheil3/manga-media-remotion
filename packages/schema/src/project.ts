import { z } from "zod";

export const projectSchema = z.object({
  id: z.string().min(1),
  title: z.string().min(1),
  sourceLanguage: z.enum(["ja", "zh", "en"]),
  imageDir: z.string().min(1),
  createdAt: z.string().datetime(),
  updatedAt: z.string().datetime(),
});

export type Project = z.infer<typeof projectSchema>;
