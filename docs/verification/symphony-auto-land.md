# Symphony Auto-Land Verification

Use this checklist to verify the full Symphony landing flow in a safe temporary git repository before relying on it against the real remote.

## Safe End-to-End Checklist

1. Create a safe temporary git repository and a temporary bare `origin`.
2. Copy or clone the repository into that temporary location so `scripts/verify-strict.sh` and `scripts/land.sh` are available.
3. Point the temporary clone at the temporary bare `origin` instead of the production remote.
4. Run `npm install` in the temporary clone so the Node workspace tests can resolve their dependencies.
5. Create a feature branch with at least two commits so the squash-merge result is observable.
6. Run `bash scripts/verify-strict.sh --print-commands` and confirm the command list matches the expected strict validation suite.
7. If the local environment is prepared for the full suite, run `bash scripts/verify-strict.sh`.
8. Move the simulated issue into `Merging`, then run `bash scripts/land.sh <feature-branch>`.
9. Confirm local `main` and `origin/main` advance by one squash commit rather than preserving the feature-branch commit chain.
10. Confirm the success output appears only after the push completes and treat the issue as `Done` only after push succeeds.
11. If validation, fetch, merge, or push fails, record the blocker and return the issue to `Rework` instead of continuing to add scope during `Merging`.

## Example Temporary Repo Flow

```bash
tmp_root="$(mktemp -d)"
git init --bare "$tmp_root/origin.git"
git clone . "$tmp_root/repo"
cd "$tmp_root/repo"
git remote rename origin upstream || true
git remote add origin "$tmp_root/origin.git"
npm install
git push -u origin main
git checkout -b tianheilene/tia-16-auto-land
printf 'one\n' > notes.txt
git add notes.txt
git commit -m 'feat: add notes'
printf 'one\ntwo\n' > notes.txt
git add notes.txt
git commit -m 'feat: expand notes'
bash scripts/land.sh tianheilene/tia-16-auto-land
git log --oneline --decorate -2 main
```

Expected result:

- `main` has one new land commit for the branch.
- `origin/main` matches local `main`.
- Symphony should consider the issue eligible for `Done` only after push succeeds.
