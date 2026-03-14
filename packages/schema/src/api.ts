import { z } from "zod";

import { frameSchema, reviewedBubbleSchema } from "./frame.ts";
import { sceneSchema } from "./scene.ts";
import { voiceSchema } from "./voice.ts";

export const projectProgressSchema = z.object({
  images: z.boolean(),
  ocr: z.boolean(),
  review: z.boolean(),
  translation: z.boolean(),
  voice: z.boolean(),
  scenes: z.boolean(),
});

export const projectSummarySchema = z.object({
  id: z.string().min(1),
  title: z.string().min(1),
  progress: projectProgressSchema,
});

export const projectDetailSchema = projectSummarySchema.extend({
  counts: z.object({
    frames: z.number().int().nonnegative(),
    voices: z.number().int().nonnegative(),
    scenes: z.number().int().nonnegative(),
  }),
});

export const reviewBubbleInputSchema = reviewedBubbleSchema.omit({
  id: true,
  textOriginal: true,
});

export const frameReviewUpdateSchema = z.object({
  reviewedBubbles: z.array(reviewBubbleInputSchema),
  skip: z.boolean().default(false),
});

export const audioMetadataSchema = z.object({
  id: z.string().min(1),
  frameId: z.string().min(1),
  mode: voiceSchema.shape.mode,
  role: voiceSchema.shape.role,
  speaker: z.string().min(1).optional(),
  audioFile: z.string().min(1).optional(),
  durationMs: z.number().int().positive().optional(),
  replaceAudioPath: z.string().min(1),
  skipRecordingPath: z.string().min(1),
});

export const sceneReviewSchema = sceneSchema.extend({
  audioMetadata: audioMetadataSchema.nullish(),
});

export const sceneUpdateSchema = z.object({
  subtitleText: z.string().nullable().optional(),
  durationMs: z.number().int().positive(),
  stylePreset: sceneSchema.shape.stylePreset,
});

export const renderJobRequestSchema = z.object({
  kind: z.enum(["preview", "final"]),
});

export const renderJobSchema = z.object({
  id: z.string().min(1),
  projectId: z.string().min(1),
  kind: renderJobRequestSchema.shape.kind,
  status: z.enum(["queued", "running", "completed", "failed"]),
  outputFile: z.string().min(1),
  createdAt: z.string().datetime(),
  updatedAt: z.string().datetime(),
  statusPath: z.string().min(1),
});

export type ProjectProgress = z.infer<typeof projectProgressSchema>;
export type ProjectSummary = z.infer<typeof projectSummarySchema>;
export type ProjectDetail = z.infer<typeof projectDetailSchema>;
export type ReviewBubbleInput = z.infer<typeof reviewBubbleInputSchema>;
export type FrameReviewUpdate = z.infer<typeof frameReviewUpdateSchema>;
export type AudioMetadata = z.infer<typeof audioMetadataSchema>;
export type SceneReview = z.infer<typeof sceneReviewSchema>;
export type SceneUpdate = z.infer<typeof sceneUpdateSchema>;
export type RenderJobRequest = z.infer<typeof renderJobRequestSchema>;
export type RenderJob = z.infer<typeof renderJobSchema>;
