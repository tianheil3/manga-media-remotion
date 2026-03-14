import { z } from "zod";

export const sceneSchema = z.object({
  id: z.string().min(1),
  type: z.enum(["narration", "dialogue", "silent"]),
  image: z.string().min(1),
  subtitleText: z.string().optional(),
  audio: z.string().optional(),
  durationMs: z.number().int().positive(),
  speaker: z.string().min(1).optional(),
  stylePreset: z.enum(["default", "fast", "dramatic", "calm"]),
  cameraMotion: z.enum(["none", "pan", "zoom-in", "zoom-out"]).optional(),
  transition: z.enum(["cut", "fade", "slide"]).optional(),
});

export type Scene = z.infer<typeof sceneSchema>;
