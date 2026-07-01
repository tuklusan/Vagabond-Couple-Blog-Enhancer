<!--
Copyright (c) 2026 Supratim Sanyal, SANYALnet Labs. All rights reserved.
Limited Source-Code Viewing License -- view-only. No execution, modification,
redistribution, production use, or AI/ML training. Full terms: see LICENSE
(repo root) or https://github.com/tuklusan/Vagabond-Couple-Blog-Enhancer/blob/master/LICENSE
-->

# Config/_SECRETS — API key files

This directory holds your API keys. The whole directory is **git-ignored except
this README**, so your keys are never committed.

You can supply keys **either** as files here **or** as environment variables
(env vars take priority — see the main project README). Create only the files for
the providers you use. Each file may contain **either** a bare key **or** a
`NAME=value` line.

**Minimum:** one writer provider + one reviewer provider. The cheapest working
setup is OpenRouter (free) + DeepSeek. DeepSeek alone can serve both the writer
and reviewer fallback roles.

---

## The four key files

### `openrouter-api-key.txt` — Writer (primary)
Get it at: <https://openrouter.ai/keys>
```
OPENROUTER_AI_API_KEY=sk-or-v1-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### `deepseek-api-key.txt` — Writer fallback + Reviewer fallback (universal)
Get it at: <https://platform.deepseek.com/api_keys>
```
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### `anthropic-api-key.txt` — Reviewer (primary, web-grounded fact-checking)
Get it at: <https://console.anthropic.com/settings/keys>
Requires a positive credit balance, or every call returns "credit balance too low".
```
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### `nvidia-api-key.txt` — Writer fallback (optional)
The env var is `NVIDIA_API_KEY_CODING` — a dedicated NVIDIA NIM key for the
writer's code/text generation fallback. The legacy filename `nvidia-api-keys.txt`
(plural) is still accepted.
Get it at: <https://build.nvidia.com/>  (Get API Key)
```
NVIDIA_API_KEY_CODING=nvapi-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

---

## Notes

- A bare-key file (just the key on one line, no `NAME=`) also works.
- **Do not commit real keys.** Only this README is tracked in `Config/_SECRETS/`;
  all `*.txt` / `*.json` files here stay ignored.
- Legacy Google/Blogger credential files (`client_secrets.json`,
  `blogger_token.json`, `google-api-client-id.txt`) are **not used** by the
  orchestrator and can be ignored or removed.
