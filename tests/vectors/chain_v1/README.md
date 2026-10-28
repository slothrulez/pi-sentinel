# Chain format v1 test vectors

- `inputs.json`: logical record payloads (pretty-printed, ASCII-escaped; not canonical).
- `record_N.canonical.json`: the exact canonical bytes for `inputs[N-1]` (UTF-8, no trailing newline).
- `expected.json`: `previous_hash` / `current_hash` for each record.

Reproduce the hashes without Python (Git Bash or Linux):

```sh
prev=0000000000000000000000000000000000000000000000000000000000000000
for i in 1 2 3; do
  prev=$( { cat record_$i.canonical.json; printf %s "$prev"; } | sha256sum | cut -d' ' -f1 )
  echo "$i $prev"
done
```

`.gitattributes` marks this directory `-text` so checkouts never convert line endings.
These files are frozen: changing them is a chain-format change and needs a new format version.
