# CR-077: a fit's checkpoint holds the optimizer state

- **Requested by / date:** owner, 2026-11-12 ("for training also save the optimizer state")
- **Status:** signed off (2026-11-12), implemented (unreleased)

## Why
A fit's `checkpoint.pt` holds the kept epoch's weights but not the Adam optimizer's state (its moment estimates and step counts). Without it a fit cannot be continued where it stopped: `init_from` starts from the weights with a fresh optimizer, which behaves differently in its first steps.

## What changes
- `ponzi-models train` writes `optimizer_state`, the optimizer's `state_dict()`, into `checkpoint.pt` beside `state_dict`, at the same moment: every improvement of the val loss (or every epoch under `keep_last_epoch`). It is the state at the kept epoch, the one the weights are from, not at the last epoch.
- Nothing reads it yet: `init_from` still loads the weights alone, and `export` reads only the weights and meta. Continuing a fit with it is a separate request.

## Do results change?
No. Saving reads the optimizer's state and does not change it or any random state, so the weights, the history and the card's metrics are the same. The checkpoint's bytes do change (it is about three times larger: Adam keeps two moments per parameter), so `checkpoint_sha256` on a new fit's card differs from what the same fit had before. The exported TorchScript artifact, and so its registry digest, is unchanged.

## Tests
`test_training_fit.py`: the checkpoint's `optimizer_state` loads into a new Adam over the model's parameters, holds a state for every parameter, and its learning rate is the training spec's.

## Version
Library: `ponzi-models` minor (the checkpoint gains a key; old checkpoints still load everywhere). Standard: no change.
