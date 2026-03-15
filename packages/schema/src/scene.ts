import { z } from "zod";

export const sceneSchema = z.object({
  id: z.string().min(1),
  type: z.enum(["narration", "dialogue", "silent"]),
  image: z.string().min(1),
  subtitleText: z.string().nullish(),
  voiceId: z.string().min(1).nullish(),
  audio: z.string().nullish(),
  durationMs: z.number().int().positive(),
  speaker: z.string().min(1).nullish(),
  stylePreset: z.enum(["default", "fast", "dramatic", "calm"]),
  cameraMotion: z.enum(["none", "pan", "zoom-in", "zoom-out"]).nullish(),
  transition: z.enum(["cut", "fade", "slide"]).nullish(),
});

export type Scene = z.infer<typeof sceneSchema>;
