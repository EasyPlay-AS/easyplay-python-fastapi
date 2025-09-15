param a;
param b;

var x >= 0;  # Decision variable

maximize Objective: a * b;  # Objective is to maximize "a * b"
subject to limit: x <= b+0.99;  # Constraint on "x"