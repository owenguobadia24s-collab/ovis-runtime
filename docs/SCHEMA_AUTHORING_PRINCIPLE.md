Typed Python models are primary; JSON Schema is generated/exported, not hand-maintained separately unless required.
In-repo schema edits happen in Python model code first.
Exported JSON Schema artifacts are generated outputs, not the primary authoring source.
Generated schemas may be committed only if treated as derived artifacts, never as the primary authoring source.
