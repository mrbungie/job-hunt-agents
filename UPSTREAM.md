# Upstream

This portability work is based on `https://github.com/dominiquevienne/claude-job-hunt`.
The upstream remote remains `origin`; this checkout began from commit
`8ffefab0381eb3310577de04eae87bdd7a977574` as recorded by the implementation
handoff, then preserves later local history. The upstream license is MIT; see
`LICENSE` and retain the existing author attribution in Claude metadata.

To bring upstream changes into a portability branch:

```sh
git fetch origin
git merge origin/main
python3 -m unittest discover -s tests -v
```

Review any changed skill instructions for host-specific assumptions before
rebuilding packages.
