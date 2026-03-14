import { z } from "zod";

const bboxSchema = z.object({
  x: z.number(),
  y: z.number(),
  w: z.number().nonnegative(),
  h: z.number().nonnegative(),
});

export const ocrBubbleSchema = z.object({
  id: z.string().min(1),
  text: z.string(),
  bbox: bboxSchema,
  order: z.number().int().nonnegative(),
  confidence: z.number().min(0).max(1),
  language: z.enum(["ja", "zh", "en"]),
});

export const reviewedBubbleSchema = z.object({
  id: z.string().min(1),
  sourceBubbleId: z.string().min(1),
  textOriginal: z.string(),
  textEdited: z.string(),
  order: z.number().int().nonnegative(),
  kind: z.enum(["dialogue", "narration", "sfx", "ignore"]),
  speaker: z.string().min(1).optional(),
});

export const frameSchema = z.object({
  frameId: z.string().min(1),
  image: z.string().min(1),
  ocrFile: z.string().min(1),
  bubbles: z.array(ocrBubbleSchema),
  reviewedBubbles: z.array(reviewedBubbleSchema),
});

export type OcrBubble = z.infer<typeof ocrBubbleSchema>;
export type ReviewedBubble = z.infer<typeof reviewedBubbleSchema>;
export type Frame = z.infer<typeof frameSchema>;
