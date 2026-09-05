# Learner Worksheet

**Authors:** Alicia Chua, Pawarit Laosunthara, and Eric Tang, Anyscale

## How Do You Test Weather You Cannot Schedule?

Name or group: ______________________________  Date: __________________

## Part 1: Make a blind decision

Do this before revealing the lesson's reference rubric.

1. Which candidate would you retain? __________________
2. How confident are you? Circle one: 1  2  3  4  5
3. Record two visible observations that support your choice.

   - ________________________________________________________________
   - ________________________________________________________________

4. Name one failure that would make a generated driving clip unusable.

   __________________________________________________________________

5. Were you choosing the most visually appealing clip or the most useful test case? Explain.

   __________________________________________________________________

   __________________________________________________________________

## Part 2: Define fit for purpose

Complete the rubric before looking at the provided scores. Use observable language.

| Criterion | Operational definition | Visible evidence | Weight |
| --- | --- | --- | ---: |
| Weather fidelity |  |  |  |
| Structure preservation |  |  |  |
| Temporal stability |  |  |  |
| Additional criterion, optional |  |  |  |
| Total |  |  | 100 |

Write at least one non-negotiable rejection rule. Examples include a vehicle disappearing, lane topology changing, impossible motion, or a camera discontinuity.

**Hard rejection rule:**

____________________________________________________________________

## Part 3: Score and select

For each candidate that passes the hard gate, calculate:

```text
score_i = w_weather * weather_i
        + w_structure * structure_i
        + w_stability * stability_i
```

Use weights as proportions or divide percentage weights by 100.

| Candidate | Passes gate? | Weather | Structure | Stability | Weighted score |
| --- | --- | ---: | ---: | ---: | ---: |
| Take 01 |  |  |  |  |  |
| Take 02 |  |  |  |  |  |
| Take 03 |  |  |  |  |  |
| Take 04 |  |  |  |  |  |
| Take 05 |  |  |  |  |  |
| Take 06 |  |  |  |  |  |
| Take 07 |  |  |  |  |  |
| Take 08 |  |  |  |  |  |

Selected candidate: __________________

Runner-up: __________________

Score margin: __________________

Does the selection match your blind vote? Why or why not?

____________________________________________________________________

## Part 4: Change the mission

Create two mission profiles.

| Profile | Weather weight | Structure weight | Stability weight | Winner |
| --- | ---: | ---: | ---: | --- |
| Safety-focused AV evaluation |  |  |  |  |
| Visually compelling demonstration |  |  |  |  |

Did the winner change? Explain which priority caused the change.

____________________________________________________________________

## Part 5: Judge the judge

1. What important property is missing from your rubric?

   __________________________________________________________________

2. Could a candidate score highly and still be unsafe or unusable? Give a concrete example.

   __________________________________________________________________

3. How might repeated optimization exploit this rubric?

   __________________________________________________________________

4. Which judgments require human calibration?

   __________________________________________________________________

5. Which measurements could be automated?

   __________________________________________________________________

6. When should the selector abstain and keep no candidate?

   __________________________________________________________________

## Transfer challenge

Choose one new domain:

- robotic manipulation
- medical image generation
- warehouse simulation
- scientific surrogate modeling
- code generation
- another domain: __________________

Design its selector.

| Element | Your design |
| --- | --- |
| Candidate generator |  |
| Criterion 1 |  |
| Criterion 2 |  |
| Criterion 3 |  |
| Hard rejection gate |  |
| Human calibration data |  |
| Automated evidence |  |
| Validation method |  |

In two sentences, explain why increasing N would or would not help this system.

____________________________________________________________________

____________________________________________________________________

## Exit ticket

1. What does `N` represent in Best-of-N?
2. Why should critical gates be applied before weighted scoring?
3. Name one way a misaligned selector could choose the wrong output.
