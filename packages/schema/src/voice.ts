import { z } from "zod";

export const voiceSchema = z.object({
  id: z.string().min(1),
  frameId: z.string().min(1),
  text: z.string(),
  mode: z.enum(["tts", "record", "skip"]),
  role: z.enum(["narrator", "character"]),
  speaker: z.string().min(1).optional(),
  voicePreset: z.string().min(1).optional(),
  audioFile: z.string().min(1).optional(),
  transcript: z.string().min(1).optional(),
  durationMs: z.number().int().positive().optional(),
});

export type VoiceSegment = z.infer<typeof voiceSchema>;
