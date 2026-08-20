import baselineJson from "../public/data/baseline_table.json";
import cohortJson from "../public/data/cohort_summary.json";
import exposureJson from "../public/data/exposure_response.json";
import interactionJson from "../public/data/interaction_tests.json";
import manifestJson from "../public/data/manifest.json";
import provenanceJson from "../public/data/provenance_manifest.json";
import sensitivityJson from "../public/data/sensitivity.json";
import type {
  BaselineTable,
  CohortSummary,
  ExposureResponse,
  InteractionTests,
  Manifest,
  ProvenanceManifest,
  Sensitivity,
} from "./types";

export const manifest = manifestJson as unknown as Manifest;
export const cohortSummary = cohortJson as unknown as CohortSummary;
export const baselineTable = baselineJson as unknown as BaselineTable;
export const exposureResponse = exposureJson as unknown as ExposureResponse;
export const interactionTests = interactionJson as unknown as InteractionTests;
export const sensitivity = sensitivityJson as unknown as Sensitivity;
export const provenanceManifest = provenanceJson as unknown as ProvenanceManifest;
