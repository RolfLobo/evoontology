<p align="center">
  English | <a href="versioning.zh-CN.md">简体中文</a>
</p>

# Version Naming and Switching

## Naming

| Type | Name | Example |
| --- | --- | --- |
| Published version | `ontology_vN`, with monotonically increasing N | `ontology_v0` initially; `ontology_v1` after the first acceptance |
| Candidate | `vN-cK`, identifying its source version and sequence | `v0-c1` is the first candidate evolved from v0 |

Acceptance maps `vN-cK` to `ontology_vN+1`.

Readers remain compatible with the legacy `semantic_vN` name. New versions and accepted versions use `ontology_vN` only.

Before the formal gate, a Candidate is stored in `versions/vN-cK/` and must not modify `active.json`. Validate this inactive version with semantic MCP `validate_semantics` and `version` set to `vN-cK`.

## Switching

Version switching is a step in the evolve skill that changes the `active.json` pointer; there is no separate command. Runtime `store.py` is naming-agnostic: it reads the version field and loads `versions/<name>/` without validating the naming pattern.

- Accept: `accept_evolution` publishes the Candidate as the next `ontology_vN+1` without overwriting an existing published version, switches `active.json`, and advances the checkpoint.
- Reject: the Parent remains active. The Candidate and `run_N` round record remain for audit, the next round continues in the same run, and the checkpoint does not advance.
- Incomplete: the active version and checkpoint remain unchanged.
