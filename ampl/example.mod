param a;
param b;
var x >= 0;  # Decision variable

maximize Objective: a * x;  # Objective is to maximize "a * x"
subject to limit: x <= b;  # Constraint on "x"