# Analyst answer checks: do not open before a masked review

These checks are analyst work, not independent validation. The original initial judgments and computational traces are preserved separately.

## G01: math_word_problem

Correct alternative: **B**.

```text
$113.00
```

85 - 15 + 20*(1-0.20) + 30*(1-0.10) = 70 + 16 + 27 = 113.

Incorrect-alternative rationale: Ignoring both sale discounts.

## G02: math_word_problem

Correct alternative: **A**.

```text
10 tablespoons
```

80/16 = 5 pounds; 5*2 = 10 tablespoons.

Incorrect-alternative rationale: Confusing pounds of meat with tablespoons.

## G03: math_word_problem

Correct alternative: **A**.

```text
$101.00
```

10*6.50 + 6*6 = 65 + 36 = 101 dollars.

Incorrect-alternative rationale: Charging all sixteen guests the lower six-dollar rate.

## G04: math_word_problem

Correct alternative: **A**.

```text
4000 chair-rental instances
```

Each week contributes 5*60 + 2*100 = 500 rentals. Two four-week months have 8 weeks; 8*500 = 4000.

Incorrect-alternative rationale: Giving weekday/weekend daily rates equal weight.

## G05: math_word_problem

Correct alternative: **B**.

```text
9 boxes in total
```

Three equal full boxes contain 26-2=24 pencils, giving capacity 8. Total pencils 26+46=72; total boxes 72/8=9.

Incorrect-alternative rationale: Reporting additional boxes rather than total boxes.

## G06: math_word_problem

Correct alternative: **B**.

```text
$1198.00
```

Frames with etching:44*20*1.2=1056; pins:2*5=10; officer cords:(44/4)*12=132; total=1198.

Incorrect-alternative rationale: Omitting officer cords.

## G07: math_word_problem

Correct alternative: **B**.

```text
$31.00
```

32*0.25 + 95*0.10 + 120*0.05 + 750*0.01 = 8 + 9.5 + 6 + 7.5 = 31 dollars.

Incorrect-alternative rationale: Omitting all pennies.

## G08: math_word_problem

Correct alternative: **A**.

```text
$32.00
```

12+43+15+4+22=96; 96/3=32 dollars.

Incorrect-alternative rationale: Splitting between two people instead of three.

## G09: math_word_problem

Correct alternative: **A**.

```text
$36.00
```

40*1.8=72; 72*0.5=36 dollars.

Incorrect-alternative rationale: Computing January reduction from original forty-dollar price.

## G10: math_word_problem

Correct alternative: **B**.

```text
$1430.00
```

(500+800)*1.10 = 1300+130 = 1430 dollars.

Incorrect-alternative rationale: Insuring only the construction charge.

## B01: boolean_expressions

Correct alternative: **A**.

```text
True
```

not False is True; True or False is True.

Incorrect-alternative rationale: Failing to apply logical negation.

## B02: date_understanding

Correct alternative: **B**.

```text
03/12/1973
```

March 5, 1973 plus seven days is March 12, 1973; original option F.

Incorrect-alternative rationale: Selecting a date before today.

## B03: dyck_languages

Correct alternative: **A**.

```text
> >
```

Matching the supplied brackets leaves two open angle brackets. Close the inner then outer bracket with > >.

Incorrect-alternative rationale: Mismatching the innermost open angle bracket.

## B04: logical_deduction_five_objects

Correct alternative: **B**.

```text
The tractor is the second-oldest
```

Oldest to newest: minivan, tractor, limousine, convertible, sedan. Convertible must occupy rank 4 and sedan rank 5; remaining chain fixes tractor at rank 2. Original option C.

Incorrect-alternative rationale: Reversing an age constraint.

## B05: multistep_arithmetic_two

Correct alternative: **B**.

```text
702
```

First parentheses:63-24=39. Second:5-7+20=18. Product:39*18=702.

Incorrect-alternative rationale: Treating subtraction of a negative product as subtraction of a positive product.

## B06: navigate

Correct alternative: **A**.

```text
Yes
```

Horizontal:6-10+4=0. Vertical:1+8-9=0. Return to origin.

Incorrect-alternative rationale: Failing to cancel horizontal or vertical steps.

## B07: object_counting

Correct alternative: **B**.

```text
13
```

1 stove+1 bed+5 cars+1 couch+1 toaster+2 fridges+1 chair+1 lamp=13 objects.

Incorrect-alternative rationale: Counting named object categories instead of instances.

## B08: reasoning_about_colored_objects

Correct alternative: **A**.

```text
zero
```

The yellow cat toy is first in the stated row. There are no objects to its left, so zero non-teal objects; original option A.

Incorrect-alternative rationale: Counting the yellow target itself as to its left.

## B09: tracking_shuffled_objects_five_objects

Correct alternative: **B**.

```text
left midfielder
```

After Eve/Claire, Alice/Dave, Bob/Eve, Dave/Bob, Bob/Eve swaps, final positions are Alice:left winger, Bob:right midfielder, Claire:goalkeeper, Dave:left midfielder, Eve:cheerleader. Original option C.

Incorrect-alternative rationale: Confusing Dave with Bob after the swaps.

## B10: word_sorting

Correct alternative: **A**.

```text
blest buxton consternate proximity quizzes sound tariff xerxes
```

Initial letters order b,b,c,p,q,s,t,x; blest precedes buxton because l precedes u.

Incorrect-alternative rationale: Placing q before p.

