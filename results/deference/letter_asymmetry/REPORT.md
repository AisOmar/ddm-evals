# Key effect by the letter the key names

Descriptive (not pre-registered), 2026-11-22. `hint_letter` is the wrong option the key names; `correct_is_A` is fixed per question (55 questions have the correct answer B and a key naming A; 45 the reverse). Follow = chose the key's letter. Effect = per-question key follow rate minus control follow rate; B − A with a 2,000-draw question bootstrap.

| model        | dataset                    |   n |   n_qA |   n_qB |   ctrl_wrong_A |   ctrl_wrong_B |   key_follow_A |   key_follow_B |   effect_A |   effect_B |   B_minus_A |     lo |    hi |
|:-------------|:---------------------------|----:|-------:|-------:|---------------:|---------------:|---------------:|---------------:|-----------:|-----------:|------------:|-------:|------:|
| R1           | clear wording (Oct)        | 791 |     54 |     45 |          0.046 |          0.161 |          0.107 |          0.311 |      0.069 |      0.15  |       0.081 |  0.001 | 0.167 |
| Qwen3-32B    | clear wording (Oct)        | 799 |     55 |     45 |          0.064 |          0.156 |          0.145 |          0.411 |      0.08  |      0.256 |       0.175 |  0.071 | 0.287 |
| gpt-oss-120b | clear wording (Oct)        | 789 |     55 |     45 |          0.118 |          0.144 |          0.159 |          0.24  |      0.041 |      0.094 |       0.054 | -0.011 | 0.12  |
| Qwen3-32B    | local pod (Nov)            | 799 |     55 |     45 |          0.073 |          0.161 |          0.132 |          0.456 |      0.058 |      0.294 |       0.237 |  0.138 | 0.338 |
| R1           | held-out wordings (Oct 16) | 694 |     54 |     45 |          0.056 |          0.133 |          0.129 |          0.281 |      0.077 |      0.148 |       0.072 | -0.022 | 0.159 |
| Qwen3-32B    | held-out wordings (Oct 16) | 700 |     55 |     45 |          0.055 |          0.133 |          0.188 |          0.433 |      0.133 |      0.3   |       0.167 |  0.037 | 0.302 |
| gpt-oss-120b | held-out wordings (Oct 16) | 695 |     55 |     43 |          0.109 |          0.163 |          0.161 |          0.273 |      0.052 |      0.105 |       0.053 | -0.022 | 0.126 |

## Stratified by whether the model ever erred on the question in control

| model        | dataset                    | stratum                    |   n_qA |   n_qB |   effect_A |   effect_B |   B_minus_A |     lo |    hi |
|:-------------|:---------------------------|:---------------------------|-------:|-------:|-----------:|-----------:|------------:|-------:|------:|
| R1           | clear wording (Oct)        | always right in control    |     50 |     36 |      0.075 |      0.146 |       0.071 | -0.018 | 0.153 |
| R1           | clear wording (Oct)        | at least one control error |      4 |      9 |      0     |      0.167 |       0.167 | -0.076 | 0.403 |
| Qwen3-32B    | clear wording (Oct)        | always right in control    |     46 |     36 |      0.049 |      0.271 |       0.222 |  0.103 | 0.347 |
| Qwen3-32B    | clear wording (Oct)        | at least one control error |      9 |      9 |      0.241 |      0.194 |      -0.046 | -0.25  | 0.167 |
| gpt-oss-120b | clear wording (Oct)        | always right in control    |     46 |     37 |      0.027 |      0.101 |       0.074 |  0.004 | 0.139 |
| gpt-oss-120b | clear wording (Oct)        | at least one control error |      9 |      8 |      0.111 |      0.062 |      -0.049 | -0.247 | 0.146 |
| Qwen3-32B    | local pod (Nov)            | always right in control    |     47 |     35 |      0.043 |      0.329 |       0.286 |  0.168 | 0.402 |
| Qwen3-32B    | local pod (Nov)            | at least one control error |      8 |     10 |      0.146 |      0.175 |       0.029 | -0.219 | 0.285 |
| R1           | held-out wordings (Oct 16) | always right in control    |     51 |     39 |      0.091 |      0.171 |       0.08  | -0.025 | 0.182 |
| R1           | held-out wordings (Oct 16) | at least one control error |      3 |      6 |     -0.167 |      0     |       0.167 |  0     | 0.5   |
| Qwen3-32B    | held-out wordings (Oct 16) | always right in control    |     52 |     39 |      0.144 |      0.346 |       0.202 |  0.063 | 0.344 |
| Qwen3-32B    | held-out wordings (Oct 16) | at least one control error |      3 |      6 |     -0.056 |      0     |       0.056 |  0     | 0.167 |
| gpt-oss-120b | held-out wordings (Oct 16) | always right in control    |     49 |     36 |      0.075 |      0.134 |       0.059 | -0.018 | 0.136 |
| gpt-oss-120b | held-out wordings (Oct 16) | at least one control error |      6 |      7 |     -0.139 |     -0.048 |       0.091 | -0.06  | 0.222 |
