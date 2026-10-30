import { Redis } from "@upstash/redis";

let client: Redis | null | undefined;

function redis() {
  if (client !== undefined) return client;
  const { UPSTASH_REDIS_REST_URL, UPSTASH_REDIS_REST_TOKEN } = process.env;
  client = UPSTASH_REDIS_REST_URL && UPSTASH_REDIS_REST_TOKEN ? Redis.fromEnv() : null;
  return client;
}

export function cacheKey(namespace: string, value: unknown) {
  return `french-listening:v1:${namespace}:${JSON.stringify(value)}`;
}

export async function cached<T>(key: string, ttlSeconds: number, loader: () => Promise<T>): Promise<T> {
  const store = redis();
  if (store) {
    try {
      const hit = await store.get<T>(key);
      if (hit !== null) return hit;
    } catch (error) {
      console.warn("Redis read failed; falling back to source", error);
    }
  }
  const value = await loader();
  if (store) {
    try { await store.set(key, value, { ex: ttlSeconds }); } catch (error) { console.warn("Redis write failed", error); }
  }
  return value;
}
