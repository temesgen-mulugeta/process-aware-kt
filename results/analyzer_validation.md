# Analyzer validation (7a) — vs gold teacher annotations

Model: `gemini-3.1-flash-lite` | compared 20 incorrect records.

**error_type agreement: 15/20 = 75%**

| id | gold error_type | pred error_type | match | faulty_step token-overlap |
|---|---|---|:--:|---:|
| 805 | wrong_operation_or_concept | wrong_operation_or_concept | ✓ | 0.80 |
| 34421 | wrong_operation_or_concept | wrong_operation_or_concept | ✓ | 0.00 |
| 34620 | wrong_operation_or_concept | wrong_operation_or_concept | ✓ | 1.00 |
| 1392 | wrong_operation_or_concept | wrong_operation_or_concept | ✓ | 1.00 |
| 34692 | wrong_operation_or_concept | wrong_operation_or_concept | ✓ | 0.67 |
| 34757 | calculation_error | wrong_operation_or_concept | ✗ | 0.25 |
| 1297 | calculation_error | calculation_error | ✓ | 1.00 |
| 411 | wrong_operation_or_concept | wrong_operation_or_concept | ✓ | 0.67 |
| 2683 | wrong_operation_or_concept | wrong_operation_or_concept | ✓ | 0.00 |
| 34746 | calculation_error | calculation_error | ✓ | 0.50 |
| 2620 | wrong_operation_or_concept | calculation_error | ✗ | 0.50 |
| 2696 | careless_error | wrong_operation_or_concept | ✗ | 0.00 |
| 1458 | wrong_operation_or_concept | wrong_operation_or_concept | ✓ | 1.00 |
| 34671 | calculation_error | wrong_operation_or_concept | ✗ | 1.00 |
| 540 | wrong_operation_or_concept | wrong_operation_or_concept | ✓ | 0.60 |
| 2655 | calculation_error | wrong_operation_or_concept | ✗ | 0.00 |
| 1403 | wrong_operation_or_concept | wrong_operation_or_concept | ✓ | 1.00 |
| 3088 | wrong_operation_or_concept | wrong_operation_or_concept | ✓ | 0.33 |
| 34538 | wrong_operation_or_concept | wrong_operation_or_concept | ✓ | 0.14 |
| 34776 | wrong_operation_or_concept | wrong_operation_or_concept | ✓ | 0.50 |

### Examples (gold error_equation vs predicted faulty_step)

- **805** gold=`\frac{21}{19} \leq \frac{a}{b}`  pred=`\frac{21}{19} \leq \frac{a}{b} <\frac{31}{9}`
- **34421** gold=`0.5 \times 0.1`  pred=`0.5 	imes 0.1+0.5 	imes 0.02=0.06`
- **34620** gold=`rs-(440 \times 1.2)=rs-528`  pred=`rs-(440 \times 1.2)=rs-528`
- **1392** gold=`1600 \times(1-0.9)=160`  pred=`1600 \times(1-0.9)=160`
- **34692** gold=`1 \times(1+0.14)^2=1.2996`  pred=`1*(1+0.14)^2=1.2996`
- **34757** gold=`110 a=550 \\ & a=50`  pred=`a t+10 a=1.1 a t=550`
- **1297** gold=`(145+60) \div 2=100.25`  pred=`(145+60) \div 2=100.25`
- **411** gold=`\begin{aligned} & 111111,333333,555555,777777,999999 \\ & \Rightarrow 5 \end{aligned}`  pred=`111111,333333,555555,777777,999999 \Rightarrow 5`

**Verdict:** reasonable — proceed to full extraction.