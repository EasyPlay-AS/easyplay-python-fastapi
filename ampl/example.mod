param a;
param b;

var x >= 0;  # Decision variable

maximize Objective: a * b * x;  # Objective is to maximize "a * x"
subject to limit: x <= b+0.99;  # Constraint on "x"