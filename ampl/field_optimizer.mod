option solver 'scip';
option scip_options 'lim:time=300';
#option scip_options 'feastol=1e-6'; #Ensure binary variable values
#option scip_options 'lpfeastol=1e-6'; #Ensure binary variable values
#option scip_options 'dualfeastol=1e-6'; #Ensure binary variable values
#option scip_options 'pre:settings=3 lim:time=10'; #Disable presolving prevents relaxation of constraints



set F; #FIELDS
set G; #GROUPS
set T ordered; #TIMESLOTS
set D ordered; #DAYS
set ST within T ordered; #START TIMESLOTS FOR EACH DAY

set DT {D} within T ordered; #ALL TIMESLOTS FOR EACH DAY
set AT {G} within T ordered; #AVAILABLE STARTING TIMESLOTS FOR EACH GROUP
set PT {G} within T ordered; #PREFERED STARTING TIMESLOTS (enten denne eller parametre p_st1 osv.)
set AAT {F, G} within T ordered; # ALREADY ASSIGNED TIMESLOTS FOR A TEAM ON A FIELD
set UT {F} within T ordered; #UNAVAILABLE STARTING TIMES FOR EACH FIELD

# Derived: per-(f,g,day) times where we enforce continuity/duration equality
#set FREE_T {f in F, g in G, day in D} :=
#   DT[day] diff (AAT[f,g] inter DT[day]);


#System parameters
param T_max = max {t in T} t;
param T_min = min {t in T} t;
param last_t {day in D} := max {t in DT[day]} t;
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


# Sum of activity starts + sum of activity starts at preferred starting time
maximize preference_score: 
sum {f in F, g in G, t in T} y[f,g,t]*prio[g] + 
sum {f in F, g in G, t in PT[g]} y[f,g,t]*preference_value;


# Handle logic for first timeslot of the week
#subject to activity_can_start_timeslot_1 {f in F, g in G}:
#	x[f,g,1] <= y[f,g,1];

# Time slot occupied only if team started same timeslot or occupied last timeslot	
#subject to activity_continuity {f in F, g in G, t in T: t >= 2}:
#	x[f,g,t] <= x[f,g,t-1]+y[f,g,t];

# Activities must last the required duration for each group take 3
#subject to activity_duration {f in F, g in G, day in D}:
#    sum {t in DT[day]} x[f,g,t] = sum {t in DT[day]} y[f,g,t] * d[g];
	
# Same group can only occupy one field at a time
subject to field_cannot_change {g in G, t in T}:
	sum {f in F} x[f,g,t] <= 1;

# Handle continuity and duration of activities (excludes AAT)
subject to activity_continuity_and_duration {f in F, g in G, day in D, t in (DT[day] diff AAT[f,g])}:
	sum {s in DT[day]: s <= t and s + d[g] - 1 >= t} y[f,g,s] = x[f,g,t];

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

# Max one activity per day
subject to one_activity_per_day {g in G, day in D}:
    sum {t in DT[day], f in F} y[f,g,t] <= 1;

# Activity must fit within same day
#subject to activity_fit_within_same_day {f in F, g in G, st in ST}:
#    x[f,g,st] <= y[f,g,st];

# Activity may not start too late
subject to no_late_starts {f in F, g in G, day in D, s in DT[day] : s + d[g] - 1 > last_t[day]}:
	y[f,g,s] = 0;
