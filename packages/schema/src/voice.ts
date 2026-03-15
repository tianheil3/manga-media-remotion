import { z } from "zod";

export const voiceSchema = z.object({
  id: z.string().min(1),
  frameId: z.string().min(1),
  text: z.string(),
  mode: z.enum(["tts", "record", "skip"]),
  role: z.enum(["narrator", "character"]),
  speaker: z.string().min(1).nullish(),
  voicePreset: z.string().min(1).nullish(),
  audioFile: z.string().min(1).nullish(),
  transcript: z.string().min(1).nullish(),
  durationMs: z.number().int().positive().nullish(),
});

export type VoiceSegment = z.infer<typeof voiceSchema>;
