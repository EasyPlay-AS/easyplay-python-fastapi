param a;
param b;

var x >= 0;  # Decision variable

maximize Objective: a * b * x;  # Objective is to maximize "a * b"
subject to limit: b+0.99 >= x;  # Constraint on "x"