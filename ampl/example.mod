param a;
param b;

var x >= 0;  # Decision variable
var y >= 0;

maximize Objective: a * b * b;  # Objective is to maximize "a * x"
subject to limit: x <= b+0.99;  # Constraint on "x"