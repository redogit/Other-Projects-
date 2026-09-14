# Pass 12 — one memory bit can rescue the wrong two-class sensor

Pass 09 showed that two sensors with the same number of classes can differ in consequence because **which states are separated matters**. Pass 12 keeps the plant family, objective, action count, and two-class sensor size fixed and changes only controller memory.

The question is narrow:

```text
fixed two-class sensor loses with memoryless control
+
one controller-memory bit
-> can the exact same sensor become sufficient?
```

## Exact bounded result

Across the same **16,384** target-absorbing, two-action, four-state plant/target systems and all **7** two-class sensors:

- sensor cases: **114,688**;
- memoryless-winning sensor cases: **62,032**;
- winning with at most two controller states: **74,344**;
- sensors rescued specifically by the second controller state: **12,312**;
- systems with at least one rescued sensor: **3,528**.

Rescued sensors by block profile:

- `3+1`: **7,656**;
- `2+2`: **4,656**.

Number of rescued two-class sensors per plant/target system:

```text
0: 12,856 systems
1:    264
2:    240
3:  1,632
4:    288
5:  1,104
```

No system needs the result interpreted as “memory always beats sensing.” For this fixed family, memory enlarges the set of usable **specific** two-class sensors.

## Small exact witness

The lexicographically first rescue reuses the Pass 09 plant:

```text
target = 0
A = [0,1,0,0]
B = [0,2,1,0]
sensor = [0,0,0,1]   # states 0,1,2 merged; state 3 separate
```

Pass 09 already established that this sensor loses under every memoryless two-observation policy. A two-state controller wins with these four cells:

```text
(memory 0, obs 0) -> action B, next memory 1
(memory 0, obs 1) -> action A, next memory 0
(memory 1, obs 0) -> action A, next memory 0
(memory 1, obs 1) -> action A, next memory 0
```

The extra state lets identical current observations be acted on differently depending on the immediately retained controller context. For example, from physical state 2 the controller follows:

```text
2 -(B)-> 1 -(A)-> 1 -(B)-> 2 -(A)-> 0
```

with the internal memory alternating so the same merged observation does not force the same action every time.

## Interpretation

This is a precise finite tradeoff:

```text
sensor geometry alone insufficient
!=
sensor geometry plus bounded history insufficient
```

The added bit does not recover the hidden physical state in general. It changes the controller's available decision field by retaining a consequential history distinction.

## Run

```sh
cd "SPrime Search/decision-field/sensor-memory"
python3 audit.py --out /tmp/pass12
```

The audit uses independent exhaustive Python and C++17 implementations and deterministic repeated native execution.
