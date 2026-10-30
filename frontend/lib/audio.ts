import { generateBlobSASQueryParameters, BlobSASPermissions, StorageSharedKeyCredential } from "@azure/storage-blob";
import { cacheKey, cached } from "@/lib/cache";
import type { InternalLesson } from "@/lib/types";

function connectionParts(connection: string) {
  const entries = Object.fromEntries(connection.split(";").flatMap((part) => {
    const index = part.indexOf("=");
    return index === -1 ? [] : [[part.slice(0, index), part.slice(index + 1)]];
  }));
  if (!entries.AccountName || !entries.AccountKey) throw new Error("Azure connection string requires AccountName and AccountKey for private audio");
  return entries as { AccountName: string; AccountKey: string };
}

export async function audioUrl(lesson: InternalLesson) {
  if (!lesson.audio?.url) throw new Error("Audio is unavailable for this lesson");
  if (lesson.audio.isPublic) return lesson.audio.url;
  const minutes = Math.min(Math.max(Number(process.env.AUDIO_SAS_MINUTES) || 30, 5), 60);
  return cached(cacheKey("audio", lesson.lessonId), Math.max((minutes - 5) * 60, 60), async () => {
    const connection = process.env.AZURE_STORAGE_CONNECTION_STRING;
    if (!connection) throw new Error("AZURE_STORAGE_CONNECTION_STRING is not configured");
    const { AccountName, AccountKey } = connectionParts(connection);
    const containerName = lesson.audio?.container || process.env.AZURE_STORAGE_CONTAINER || "french-lessons";
    const expiresOn = new Date(Date.now() + minutes * 60_000);
    const sas = generateBlobSASQueryParameters({ containerName, blobName: lesson.audio!.blobPath, permissions: BlobSASPermissions.parse("r"), expiresOn }, new StorageSharedKeyCredential(AccountName, AccountKey)).toString();
    return `${lesson.audio!.url}?${sas}`;
  });
}
