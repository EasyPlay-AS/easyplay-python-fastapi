option solver 'scip';
option scip_options 'lim:time=10';
option scip_options 'feastol=1e-6'; #Ensure binary variable values
option scip_options 'lpfeastol=1e-6'; #Ensure binary variable values
option scip_options 'dualfeastol=1e-6'; #Ensure binary variable values
option scip_options 'pre:settings=3'; #Disable presolving prevents relaxation of constraints

set F; #FIELDS
set G; #GROUPS
set T; #TIMESLOTS
set AT {G} within T; #AVAILABLE STARTING TIMESLOTS FOR EACH GROUP
set PT {G} within T; #PREFERED STARTING TIMESLOTS (enten denne eller parametre p_st1 osv.)
set UT {F} within T; #UNAVAILABLE STARTING TIMES FOR EACH FIELD

#System parameters
param T_max = max {t in T} t;
param T_min = min {t in T} t;
param preference_value = 1;
#param square_value = 0.1 #value of square occupied

#Club parameters
param d{G} >= 0; #How long an activity for group g should be
param n_min{G} >= 0; #minimum number of activities
param n_max{G} >= 0; #maximum number of activities
param size{F} >= 0; #size of field measured in zones
param size_req{G} >= 0; #size required for each group
param prio{G} in 1..3; # Group priority: option to prioritize activities of specific groups

#Group parameters (preferences)
param p_st1{G} default 0; #prefered start time 1
param p_st2{G} default 0; #prefered start time 2

var x {F,G,T} binary;
var y {F,G,T} binary;


maximize preference_score: 
sum {f in F, g in G, t in T} y[f,g,t]*prio[g] + # Sum of  activity starts
sum {f in F, g in G, t in PT[g]} y[f,g,t]*preference_value # Sum of activity starts at preferred starting time
;
# Handle logic for first timeslot of the week
subject to activity_can_start_timeslot_1 {f in F, g in G}:
	x[f,g,1] <= y[f,g,1];

# Time slot occupied only if team started same timeslot or occupied last timeslot	
subject to activity_continuity {f in F, g in G, t in T: t >= 2}:
	x[f,g,t] <= x[f,g,t-1]+y[f,g,t];

# Activities must last the required duration for each group
subject to activity_duration {f in F, g in G, t in T: t >= d[g]}:
	x[f,g,t] = sum {delta in 0..d[g]-1} y[f,g,t-delta];

# Activities must last the required duration for each group
#subject to activity_duration {f in F, g in G, t in T: t <= T_max - d[g]}:
#	sum {delta in 0..d[g]-1} x[f,g,t+delta] =  d[g] * y[f,g,t];
	
# Same group can only occupy one field at a time
subject to field_cannot_change {g in G, t in T}:
	sum {f in F} x[f,g,t] <= 1;

# Maximum activities for a team
subject to max_activities {g in G}:
	sum {t in T, f in F} y[f,g,t] <= n_max[g];

# Minimum activities for a team	 
subject to min_activities {g in G}:
	sum {t in T, f in F} y[f,g,t] >= n_min[g]; 
	
# Activities can not occupy unavailable field times
subject to unavailable_field_times {f in F, t in UT[f]}:
	sum {g in G} x[f,g,t] = 0;

# Activities can not start outside of the group´s timeslots.
subject to activity_can_not_start {g in G, t in T diff AT[g]}:
	sum {f in F} y[f,g,t] = 0;

# Field capacity
subject to field_capacity {t in T, f in F}:
	sum {g in G} x[f,g,t]*size_req[g] <= size[f];


#Max one activity per day
subject to day1 {g in G}:
	sum {t in 1..36, f in F} y[f,g,t] <= 1;
subject to day2 {g in G}:
	sum {t in 37..72, f in F} y[f,g,t] <= 1;
subject to day3 {g in G}:
	sum {t in 73..108, f in F} y[f,g,t] <= 1;
subject to day4 {g in G}:
	sum {t in 109..144, f in F} y[f,g,t] <= 1;
subject to day5 {g in G}:
	sum {t in 145..180, f in F} y[f,g,t] <= 1;





###GRAVEYARD###
#maximize field_utilization: sum {f in F, g in G, t in T} 
#x[f,g,t];


### Only one activity every other day ###
#subject to activity_starts_day1_day2 {g in G}:
#	sum {t in 1..72, f in F} y[f,g,t] <= 1;
	
#subject to activity_starts_day2_day3 {g in G}:
#	sum {t in 37..108, f in F} y[f,g,t] <= 1;
	
#subject to activity_starts_day3_day4 {g in G}:
#	sum {t in 73..144, f in F} y[f,g,t] <= 1;

#subject to activity_starts_day4_day5 {g in G}:
#	sum {t in 109..180, f in F} y[f,g,t] <= 1;
### Only one activity every other day ###


# Activity can at maximum last d[g] timeslots
#subject to activity_duration {g in G, f in F, t in T: t <= T_max-d[g]}:
#	sum {delta in 0..d[g]} x[f,g,t+delta] <= d[g];



