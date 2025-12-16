import 'dotenv/config';

type Backend = {
  name: string;
  host: string;   // container hostname
  port: string;   // container port
};

const BACKENDS: Backend[] = [
  { name: 'auth', host: 'iip_api_auth', port: process.env.PORT_AUTH! },
  { name: 'core', host: 'iip_api_core', port: process.env.PORT_CORE! },
  { name: 'agent', host: 'iip_api_ia_agent', port: process.env.PORT_IA_AGENT! },
];

const CLIENTS = [
  { name: 'apiBrowser', client: 'svelte-query', targetDir: 'src/lib/api/browser' },
  { name: 'apiNode', client: 'axios', targetDir: 'src/lib/api/node' },
];

const config = Object.fromEntries(
  CLIENTS.flatMap(({ name: clientType, client, targetDir }) =>
    BACKENDS.map(backend => [
      `${clientType}${backend.name.charAt(0).toUpperCase() + backend.name.slice(1)}`,
      {
        input: {
          target: `http://${backend.host}:${backend.port}/node/openapi.json`,
        },
        output: {
          mode: 'tags-split',
          target: `${targetDir}/endpoints/${backend.name}`,
          schemas: `${targetDir}/schemas/${backend.name}`,
          client,
          esm: true,
          override: {
            mutator: { path: 'src/lib/api/Fetcher.ts', name: 'Fetcher' },
          },
          hooks: { afterAllFilesWrite: 'prettier --write' },
        },
      },
    ])
  )
);

export default config;
