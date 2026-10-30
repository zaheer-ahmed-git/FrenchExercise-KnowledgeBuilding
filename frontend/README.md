# French AI Listening frontend

Standalone Vercel application for the French AI listening lessons published by the repository's Python pipeline.

## Deploy

1. Import this repository into Vercel and set **Root Directory** to `frontend`.
2. Create an Upstash Redis database and add the variables listed in `.env.example` to Vercel.
3. Add the MongoDB and Azure connection settings as server-only Vercel environment variables.
4. Run `npm.cmd install`, then `npm.cmd run build` locally before deploying.

The frontend reads only `published` lessons. It does not publish, change, or delete lesson data.
