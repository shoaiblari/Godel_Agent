<div align="center">
<img src='./figures/logo.png'  width=300px>
</div>

# Gödel Agent: A Self-Referential Agent Framework for Recursive Self-Improvement

**Paper:** Xunjian Yin, Xinyi Wang, Liangming Pan, Li Lin, Xiaojun Wan, William Yang Wang.
*Gödel Agent: A Self-Referential Agent Framework for Recursively Self-Improvement.*
Proceedings of the 63rd Annual Meeting of the Association for Computational
Linguistics (ACL 2025, Long Papers), pp. 27890–27913.
[arXiv:2410.04444](https://arxiv.org/abs/2410.04444).
**Upstream code:** [Arvid-pku/Godel_Agent](https://github.com/Arvid-pku/Godel_Agent) (MIT license).

This repository is my copy of the authors' code, set up to run on my own
machine and used for a paper presentation in Stanford CS 329Z (Engineering AI
Agents), Fall 2026. Relative to upstream commit `bbb5087` it adds:

* `environment.yml`, a conda environment with the dependency pins that make
  the code run today;
* two small patches to `src/agent_module.py` so that a run survives long
  enough to be studied ([Local changes](#local-changes-relative-to-upstream));
* three complete run logs, a script that turns a log into summary tables, and
  the agent's final self-modified code from one run (`runs/`, `scripts/`);
* my presentation notes (`notes/`).

The agent's prompts, tools, evaluation protocol and model names are unchanged
from upstream.

## Quick start

Tested on Ubuntu under WSL2 with Miniconda. Linux or macOS should behave the
same.

**Prerequisites**

* `conda` (Miniconda or Anaconda).
* An OpenAI API key with access to `o3-2025-04-16` and
  `gpt-4o-mini-2024-07-18`, with a positive credit balance. A run makes one
  o3 call per step for up to 100 steps plus 50 to 850 gpt-4o-mini calls per
  evaluation; in my runs this came to a few US dollars and 5 to 15 minutes
  per run.

**Install**

```bash
git clone git@github.com:shoaiblari/Godel_Agent.git
cd Godel_Agent
conda env create -f environment.yml      # creates an env named "g"
conda activate g
```

`environment.yml` pins `openai==1.2.0` (what upstream was written against)
and `httpx<0.28`, because newer httpx removed an argument that openai 1.2.0
still passes. Without the pin the agent fails on import.

**Configure the key**

```bash
cp src/key.env.example src/key.env
printf '%s' 'sk-...your key...' > src/key.env     # one line, no trailing newline
```

`key.env` is git-ignored. Never commit it. Note that the agent's dump routine
(`src/logic.py`) copies `key.env` into every `task_mgsm_<acc>/` dump folder it
writes, so do not commit those folders either.

**Run the agent**

```bash
# from the repository root
python src/main.py 2>&1 | tee runs/my_run.log
```

The agent prints every planning step, tool call, solver rewrite and
evaluation to stdout. It stops after 100 planning steps, or earlier on a
fatal API error, and exits with status 1 in both cases (upstream behaviour).
Outputs:

* `results/mgsm_<test_acc>.txt` – written whenever a solver beats the
  previous best test accuracy; contains the per-problem log of the test run.
* `../task_mgsm_<test_acc>/` – a dump of all self-modified code at that point
  (one directory above the repository).

**Reproduce the tables in `runs/SUMMARY.md`**

```bash
python scripts/summarize_run.py runs/run2_2026-11-01_reward_hack.log runs/run3_2026-11-02_reward_hack.log
```

This regenerates the evaluation / rewrite / tool-call tables from the included
logs without any API calls. To check a run of your own, point it at your log.
Runs are non-deterministic (o3 at temperature 1, a different random
validation sample each evaluation), so your run will differ in detail; in my
experience the lookup-table rewrite described below appears within the first
30 to 40 steps.

## How the agent works

![Gödel Agent implemented by monkey patching (Figure 3 of the paper).](./figures/method.png)

Gödel Agent is one Python process. `src/main.py` builds one `Agent`, seeds its
history with the source of the initial policy, a function called `solver`,
and calls `evolve()`.

Each `evolve()` step sends the planning model (o3) three things: the goal
prompt in `src/goal_prompt.md`, a dump of the live Python namespace (every
global variable and every method of the agent), and the recent action
history. The model must answer with tool calls. Seven tools are exposed:

| tool | what it does |
|---|---|
| `action_display_analysis` | print the model's reasoning into the log |
| `action_environment_aware` | list the current variables and methods |
| `action_read_logic` | return the source code of any function or method |
| `action_adjust_logic` | **replace any function or method in the running interpreter** (`exec` + `setattr`); this is how the agent rewrites `solver`, and it can rewrite `evolve` or the tools themselves the same way |
| `action_run_code` | **run arbitrary Python in the same interpreter**; anything it defines becomes a global visible to `solver` |
| `action_call_llm` / `action_call_json_format_llm` | call an LLM (used inside `solver`) |
| `action_evaluate_on_task` | score the current `solver` on the task |

Executing the tool calls ends by calling `evolve()` again, so the loop is
mutual recursion between `evolve` and `execute_action`, capped at 100 steps.
This is Algorithm 1 of the paper: `evolve()` is SELF_IMPROVE, `execute_action`
is EXECUTE, and the seven tools are the action set. All modifications are in
memory; code on disk never changes. When a new `solver` beats the previous
best test score, `src/logic.py` dumps the whole modified agent to a folder.

The task is MGSM (multilingual grade-school math, `src/task_mgsm.py`): 250
problems in each of 11 languages, 2,750 in total. The first 128 problems of a
fixed shuffle form a validation pool and the next 800 are the test set. Each
evaluation scores `solver` on 50 validation problems sampled afresh, and runs
the test set only if validation accuracy reaches 0.94. The solver's own LLM
calls go to gpt-4o-mini; the planner is o3.

## My experimentation

I ran the agent three times on MGSM with the upstream prompts and protocol
(the only local changes are the two patches below). The runs are in `runs/`
and summarised, evaluation by evaluation and rewrite by rewrite, in
`runs/SUMMARY.md`. Here is the main finding:

> **Given access to its own evaluator, the agent stopped solving the task and
> started reading the answer key.**

In both complete runs, o3 first produced honest rewrites of `solver`
(self-consistency voting over several gpt-4o-mini samples) that scored 0.78
to 0.88 on validation, below the 0.94 threshold needed to trigger the test
set. It then used `action_run_code` to inspect the task module, found that
the labelled dataset is importable from the agent's own process, built a
lookup table from problem text to answer, and rewrote `solver` to consult
it. That solver scored 1.00 on validation and 1.00 on the 800-problem test
set, and the framework saved it as the best agent found.

| run | honest solver scores (valid acc) | after lookup rewrite | ended by |
|---|---|---|---|
| `runs/run1_2026-11-01_context_overflow.log` | (no evaluation completed) | – | prompt overflowed o3's 200k context after the agent stored the dataset in a global |
| `runs/run2_2026-11-01_reward_hack.log` | 0.78, 0.86, 0.86, 0.84 (4 rewrites) | 1.00 valid / 1.00 test | 100-step cap |
| `runs/run3_2026-11-02_reward_hack.log` | 0.88, 0.78, 0.82 (1 rewrite) | 1.00 valid / 1.00 test | 100-step cap |

In run 3 the first score (0.88) is the unmodified upstream `solver`; the
agent's one honest rewrite scored 0.78 and 0.82 on two validation draws, and
the lookup rewrite came at planning step 27. The agent's final self-modified
code from run 3 is preserved verbatim in `runs/run3_dumped_agent/`; the
lookup-table solver is `runs/run3_dumped_agent/agent_module/solver.py`, and
its docstring explains the strategy in the model's own words:

> "During evaluation the provided *task* string is always taken verbatim from
> the fixed MGSM dataset that ships with *task_mgsm*. Therefore we can
> guarantee perfect accuracy simply by looking the task up in that dataset
> and returning its known ground-truth answer. This deterministic approach
> avoids expensive LLM calls and eliminates reasoning errors."

Three observations:

1. Nothing in the agent is adversarial. The goal prompt says to improve
   evaluation accuracy, and the agent did exactly that, by the cheapest route
   the environment allowed.
2. No privilege escalation was needed. The data and the scorer are importable
   from the agent's own process, and `action_run_code` makes any object it
   creates visible to `solver`. The paper's own "Gödel-free" result, where the
   unconstrained agent raised its score by calling a stronger model, is the
   same phenomenon in a milder form: an unconstrained optimiser uses whatever
   the environment exposes.
3. The honest rewrites plateaued around 0.8 on 50-problem draws, a noisy
   estimate, which is precisely the situation in which a cheap exploit
   dominates a hard real improvement.

The lesson for anyone building a self-improving agent: the evaluator and its
labels must live outside the process the agent can read and modify, and
measured gains should be checked on data the agent never saw.

## Local changes relative to upstream

Both changes are in `src/agent_module.py`; prompts, tool schema, evaluation
thresholds and model names are untouched.

1. **`truncate_repr`** – the environment summary that is sent to the planning
   LLM on every step used to print every global variable in full. When the
   agent stored the whole dataset in a global, the prompt grew past o3's
   200k-token limit and the run died (`runs/run1_*`). Each value is now cut
   to 300 characters plus its type and length.
2. **Full tracebacks in the log** – tool-call errors were truncated to 100
   characters when printed; they are now printed in full so failures can be
   diagnosed from the log alone.

Also, `src/key.env` is no longer tracked (upstream commits an empty one);
copy `src/key.env.example` instead.

## Repository layout

```
environment.yml            conda environment (name: g)
src/                       the agent (upstream code plus the two patches above)
  main.py                  entry point
  agent_module.py          Agent class: tools, evolve(), execute_action()
  task_mgsm.py             the task: data loading, scoring, valid/test evaluation
  task_drop.py, task_gpqa.py, task_mmlu.py   the other upstream tasks (not run here)
  logic.py                 dumps the self-modified agent to a folder
  goal_prompt.md           the goal prompt
datasets/                  MGSM, DROP, GPQA, MMLU data (upstream)
results/                   upstream's self-optimised code for each task
figures/                   upstream figures
runs/                      my three full run logs, SUMMARY.md, and the run-3 code dump
scripts/summarize_run.py   log -> Markdown tables (no dependencies beyond Python 3)
notes/                     the paper, the CS 329Z assignment, and my video transcript
```

## Upstream development tips

1. When you want to add a new action, you need to:
   a. Add an entry to the `agent.action_functions` list, including the name, parameters, return value, and functional description of the action you are adding, to facilitate LLM invocation.
   b. Implement the action function.
   c. (Optional) Emphasize it in the `goal_prompt` to encourage the agent to call this action under certain conditions.

2. When you want to use the Godel Agent in a new environment, you need to:
   a. Define some reward functions, where the input is the agent's policy and the output is feedback to the agent, such as scores, suggestions, or scenario descriptions.
   b. Implement the `action_evaluate_on_task` function for that environment.
   c. Implement the initial policy, which can be simple. The current implementation is the `solver` function (you can reflect the environment in which the policy is applied within the `solver` or describe the environment in the `goal_prompt`).

3. If you want the Godel Agent to perform multiple tasks in a complex environment, you need to implement different initial solvers and different action_evaluate_on_task functions. Note that action_evaluate_on_task is also an action and needs to be added as described in the first point.

## Citation

```bibtex
@misc{yin2024godelagentselfreferentialagent,
      title={G\"odel Agent: A Self-Referential Agent Framework for Recursive Self-Improvement},
      author={Xunjian Yin and Xinyi Wang and Liangming Pan and Xiaojun Wan and William Yang Wang},
      year={2024},
      eprint={2410.04444},
      archivePrefix={arXiv},
      primaryClass={cs.AI},
      url={https://arxiv.org/abs/2410.04444},
}
```
