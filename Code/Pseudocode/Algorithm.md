The following is a proposed algorithm for the competition, based on the immunized genetic algorithm and harmony search idea we had. 

## Terminology
- Target: An enemy projectile we want to take down.
- Units: Our friendly ships.

## Algorithm

This is how we will initialize our AI:
```python
# make a new weapon A.I. object for each weapon_type
# in this competition, WEAPON_TYPES = ["Cannon", "Chainshot"]
weapon_AIs = dict()
for weapon_type in WEAPON_TYPES:
    weapon_AIs[weapon_type] = Weapon_AI(weapon_type)
# make a new weapon A.I. object for each weapon_type
# in this competition, WEAPON_TYPES = ["Cannon", "Chainshot"]
weapon_AIs = dict()
for weapon_type in WEAPON_TYPES:
    weapon_AIs[weapon_type] = Weapon_AI(weapon_type)
    
control_center = ControlCenter()
```


This is the algorithm that we will run at each step:
```python
# create set of possible actions against target
target_actions = list()
target_actions = list()

for target in statePb.Tracks:
    current_target_actions = set()
    for defense_ship in statePb.assets:
        for weapon in defense_ship.weapons: 
            # get a set of proposed ( weapon, defense_ship, target ) tuples for the target
            proposed_actions = weapon_AIs[weapon.SystemName].request(weapon, defense_ship, target)
            possible_target_actions.add(proposed_actions)
    target_actions.append(current_target_actions)
for target in statePb.Tracks:
    current_target_actions = set()
    for defense_ship in statePb.assets:
        for weapon in defense_ship.weapons: 
            # get a set of proposed ( weapon, defense_ship, target ) tuples for the target
            proposed_actions = weapon_AIs[weapon.SystemName].request(weapon, defense_ship, target)
            possible_target_actions.add(proposed_actions)
    target_actions.append(current_target_actions)
    
# initialize and apply immune system dynamics to get the top Actions
best_actions = ControlCenter.decide(target_actions)

#execute the best actions to get a reward
reward = execute(best_actions)
```

If we are training the algorithm, we will use the ```reward``` variable and ```best_actions``` variable to update the fitness values for each ```Action_Rule``` that was executed, and use either Genetic Algorithm or Harmony Search to fine tune the ```Action_Rule``` objects. 
If we are training the algorithm, we will use the ```reward``` variable and ```best_actions``` variable to update the fitness values for each ```ActionRule``` that was executed, and use either Genetic Algorithm or Harmony Search to fine tune the ```ActionRule``` objects. 

```python
accuracy_sum = 0 
for action in best_actions:
    accuracy_sum += action.update_predicted_values(reward)

for action in best_actions:
    action.update(update_fitness)

# do Genetic Algorithm OR Harmony Search here!
```
## Training
The goal of using the genetic algorithm and harmony search is to discover the right ```ActionRule``` class conditionals to use and the right hyperparameters to use to select the right ```ActionRule``` at any step.  

## Classes/Main Ideas

### The ```Weapon_AI``` Class
The ```Weapon_AI``` class handles decision making for a specific type of weapon. For example, since we have ```Chainshot``` and ```Cannonball``` as the two types of weapon systems at our disposal, we would have a ```Weapon_AI``` object in charge of ```Chainshot``` logic, and another in charge of ```Cannonball``` logic. 

This class is analogous to the B-cell from the immunized classifier paper. 

#### Fields
- ```string my_type``` - this object's assigned type, for our purposes, either ```Chainshot``` or ```Cannonball```. 
- ```set(ActionRule) action_set``` — contains all ```ActionRule``` objects for this type of weapon. 

#### ```Weapon_AI(filename=fname) : Weapon_AI```
The constructor for this class initializes ```action_set```, defaulting to randomly generating the ```ActionRule``` objects contained within, but if a file is specified, it will fetch the information from a file and initialize them that way. 

#### ```request(weapon, ship, target) : set((weapon_system, ship, target, ActionRule))```
Through this function, each weapon in-game can make a request to the ```Weapon_AI``` object that corresponds to its weapon type. From its parameters, the ```request()``` function has access to the location, direction, threat-level, and type of a target and the location/capabilities of the specific weapon, and will choose an appropriate subset of its ```ActionRule``` objects having conditionals that match the situation. It will return a set of tuples of the following format: ( weapon_system, ship, target, ```ActionRule``` ).

#### ```save_rules(filename) : void```
This function saves all rules to a file named ```filename```, overwriting that file if it already exists, and creating it if it does not. 

### The ```ActionRule``` Class
The ```ActionRule``` class encodes logic for a decision to fire. Each ```ActionRule``` object is a wrapper around a specialized if-then statement. It has a set of conditionals describing the state of units and ships. It is also the candidate that the genetic algorithm will evolve over time, and also contains pertinent variables. 

An ```ActionRule``` object could look like this: "IF distance from target IS low AND velocity IS medium AND heading IS high THEN fire". Since any one weapon could only fire or not fire at any time step, the consequent of this conditional is always fire. 

This is analogous to the classifier from the immunized classifer paper.  

#### Fields
- TODO: Figure out how to encode conditionals for this class. 
- ```double predicted_value``` — predicted value ($p$) if this ActionRule is employed, initialized to 0. Its update function is $p: p = p + \beta(R-p)$ 
- ```double predicted_val_error``` — expected error ($\epsilon$) for ```predicted_value```, initialized to 0. Its update function is $\epsilon : \epsilon = \epsilon + \beta(|R-p| - \epsilon)$
- ```double fitness``` — the fitness ($F$) for this rule, used for genetic algorithm training purposes. Initialized to 0. Its update function is $F : F = F + \beta(\hat{\lambda}(cl) - F)$
- ```double accuracy``` — the accuracy ($\lambda$) for this rule, used to calculate ```fitness```, where $\epsilon_0$ is an accuracy criterion constant, a hyperparameter. A classifier is accurate if $\epsilon$ is smaller than $\epsilon_0$. $\alpha$ and $v$ are hyperparameters used to control the rate at which the accuracy reduces. 

$$\lambda (cl) = \begin{cases} 
1 & \text{if } \epsilon < \epsilon_0 \\ 
\alpha(\frac{\epsilon}{\epsilon_0})^{-v} & \text{if } \epsilon \geq \epsilon_0 \end{cases}$$

- ```double relative_accuracy``` — denoted by $\hat{\lambda}$. The accuracy for this rule, relative to other rules. Used to calculate ```fitness```. Relative accuracy is calculated using $\hat{\lambda}: \hat{\lambda} = \frac{\lambda}{\sum_{cl_b \in [A]} \lambda_b}$. The denominator is the sum of all ```accuracy``` fields in all other actions that were executed at the same time step. 

#### ```update_predicted_values(reward) : accuracy```
Given the ```reward``` from an action (TODO: Is this accurate? Does this make sense for training the genetic algorithm?), update ```predicted_value```, ```predicted_val_error```, and ```accuracy```. Return ```accuracy```. 

#### ```update_fitness(accuracy_sum) : void```
Given the ```accuracy_sum```, the sum of ```accuracy``` values for all other ```ActionRules``` that were executed at the same time step, update ```relative_accuracy``` and ```fitness```. 

### The ```ControlCenter``` Class
The ```ControlCenter```'s role is to make overarching decisions, authorizing each weapon to fire at targets. 

#### ```ControlCenter()```
A constructor for ```ControlCenter```.

#### ```decide(list[set(weapon_system, ship, target, ActionRule)]) : list[weapon_system, ship, target, ActionRule]```
This function takes a list of sets of all proposed (weapon_system, ship, target, ```ActionRule```) tuples as an argument. Each element of the list will be a set of (weapon_system, ship, target, ```ActionRule```) tuples that corresponds to a single target. Using this list, the ```ControlCenter``` decides on the best action to take for each target, and returns the selected actions as a list of (weapon_system, ship, target, ```ActionRule```) tuples. 

To choose the right ```ActionRule``` objects to take, the ControlCenter could use immune network dynamics. 

For ```ActionRule``` $a_i$ at time $t$, we have:

$$\frac{da_i(t+1)}{dt} = \left( \alpha \sum^{N}_{j=1} m_{ji} a_j(t) - \beta \sum^{N}_{j=1} m_{ik} a_k(t) + \gamma m_i - k \right) a_i(t)$$

- $N$ is the number of ```ActionRule``` objects that deal with the target
- $m_i$ is the affinity between ```ActionRule``` $i$ and the target antigen
- $m_{ji}$ is the mutual stimulus coefficient of ```ActionRule``` $j$ on ```ActionRule``` $i$
- $m_{ki}$ is the inhibitory effect of ```ActionRule``` $k$ on ```ActionRule``` $i$
- Hyperparameter $k$ is the natural death rate of ```ActionRule``` $i$
- $a_i(t)$, $a_j(t)$, and $a_k(t)$ are bounded scores that are imposed on the ```ActionRule``` objects
- coefficients $\alpha$, $\beta$, and $\gamma$ are hyperparameters that determine the significance of each term. 

The solution to this set of ODE's will yield the score for each ```ActionRule```, and the top one for each target is chosen to be executed.

## To Discuss:
- **Question:** What do we do with targets that have already been fired at? 


## To Do: 
- Create method of encoding conditionals in the ```ActionRule``` class. 
    - Figure out what values should be considered for ```ActionRule``` conditionals.
    - Create and implement a good encoding scheme for the conditionals. 
- Create method of saving ```Weapon_AI``` objects to file (saving our progress).
    - Create constructor for ```ActionRule``` with manually specified parameters for this purpose. 
    - Finish ```save_rules(filename=fname)```
- Find out how to train this algorithm using both Harmony Search and Genetic Algorithm.
    - **Question:** How do we determine the reward for an action? 