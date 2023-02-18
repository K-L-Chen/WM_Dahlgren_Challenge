# Immunized Classifier Notes
The general idea is to have an integrated Artificial Immune System and Learning Classifier System. There are two main agents:
- **Strategy Generation Agent** — Low level agent that learns the apprpriate weapons and quantity to deploy against any given target using classifiers. This is the *genetic algorithm/learning classifier* component. 
- **Strategy Coordination Agent** — Takes inputs of proposed classifiers from the *Strategy Generation Agent*, treats them as antigens, and performs *immune network dynamics* to determine the actions of the target. 

### Strategy Generation Agent
This agent treats each weapon type as an abstract B-cell (decision unit), which is a vessel for carrying antibodies, or classifiers, that contain control decisions. Any enemy projectiles it detects are treated as antigens, with intent, capability, and opportunity. Using the information it has on the enemy projectiles, each of the B-cells will produce classifiers, which the Strategy Generation Agent will then pass to the Strategy Coordination Agent. 

**Initialization**: Each B-cell's population of classifiers are initialized randomly. The connections component in each classifier is initialized to be empty. 

This agent uses a learning classifier system, which has three main phases in execution:

- **Performance** — Actions are selected using an existing batch of classifiers. To do this, a matched set $[M]$ of classifiers that match the current input messages in a population $[P]$ are formed and the acquisition reward for each action $a_i$ is calculated to obtain a prediction array $P(a_i)$ using the following equations:

    Given a set of classifiers matching the attributes of a specific B-cell $[M]$, the expected action payoff for a specific action $a_i$ is
    $$P(a_i) = \frac{\sum_{cl_{k} \in [M] | a_i} cl_{k}.p \times cl_k.F * \omega}{\sum_{cl_{k} \in [M] | a_i} cl_l.F * \omega}$$ 
    
    Where $\omega$ is the affinity between the B-cells' classifiers and antigens. In other words, $P(a_i)$ is the reward that the agent receives for performing a specific action.

    $$\omega = [1 - \prod^{q}_{i=1}(1-d_g * p_g * w_e * r_t)] * v_c$$

    In the above affinity equation, $q$ is the quantity of ammo suggested by the classifer, $d_g$ is the normalized distance between target $c$ and the combat unit, $p_g$ is the speed advantage of the fire unit weapon against the target, $w_e$ is the kill probability of the weapon suggested, $r_t$ is the ready time of the weapon if it were to be deploed, and $v_c$ is the quantified target type that estimates the value of the target. 

 - Actions that are inferred from the prediction array are selected to form a set. Classifiers that have a specific action are stored in an action set. The executed action will have an associated reward value which will be used later.
 - At this step, redundant classifiers can be removed using manual rules to stop them from being processed further (i.e. weapon has no ammunition remaining)

- **Reinforcement** - Parameters in the classifiers are updated using the reward from the performance phase.
    - Prediction $cl.p: cl.p = cl.p + \beta(R-cl.p)$
    - Prediction Error  $cl.\epsilon : cl.\epsilon = cl.\epsilon + \beta(|R-cl.p| - cl.\epsilon)$, where $R$ is the reward associated with performing a specific action. 
    - Fitness $cl.F : cl.F = cl.F + \beta(\hat{\lambda}(cl) - cl.F)$
    - Accuracy $\lambda(cl)$, where $\epsilon_0$ is an accuracy criterion constant. A classifier is accurate if $cl.\epsilon$ is smaller than $\epsilon_0$. $\alpha$ and $v$ are hyper-parameters used to control the rate at which the accuracy reduces.$$\lambda (cl) = \begin{cases} 1 & \text{if } cl.\epsilon < \epsilon_0 \\ \alpha(\frac{cl.\epsilon}{\epsilon_0})^{-v} & \text{if } cl.\epsilon \geq \epsilon_0 \end{cases}$$
    - Relative accuracy $\hat{\lambda}(cl): \hat{\lambda}(cl) = \frac{cl.n \times \lambda(cl)}{\sigma_{cl_b \in [A]} \lambda(b) \times b.n}$

- **Discovery** — In the discovery phase, the algorithm applies a genetic algorithm to generate a new batch of classifiers. Two parents with high fitness are selected from the action set, and offspring are produced using a crossover algorithm and a random bit-flip mutation. Offspring can be cloned using two methods: either cloning the entire classifier, or cloning all classifiers and replacing the consequent (action to take) with the action from high fitness classifiers. Classifiers with low fitness are deleted if the number of total classifiers in the batch get too large, and classifiers whose conditionals are already included in more accurate, experienced classifiers can be deleted.


### Strategy Coordination Agent
After receiving a set of proposed actions from the Strategy Generation Agent, this agent performs the final action selection by applying immune system dynamics and selecting the classifier with the highest concentration. 

In the immune system, each classifier has a connections component that is used to determine its appropriateness in a given situation with respect to other classifers. 

#### Classifier Representation and Encoding
- agentID | weaponID | unit state | target state | quantity to fire | connections

Classifier Concentration $a_i(t+1)$:
$$\frac{da_i(t+1)}{dt} = \left(\alpha \sum^{N}_{j=1}m_{ji}a_j(t) - \beta\sum^{N}_{j=1}m_{ik}a_k(t) + \gamma m_i - k\right) a_i(t)$$
Where $N$ is the number of classifiers that deal with the target antigen, $m_i$ is the affinity between classifier $i$ and the target antigen, $m_{ji}$ is the mutual stimulus coefficient of antibody $j$ on classifier $i$, $m_{ki}$ is the inhibitory effect of classifier $k$ on classifier $i$, $k$ is the natural death rate of classifier $i$, $a_i(t)$, $a_j(t)$, and $a_k(t)$ are the bounded concentrations that are imposed on the classifiers, and coefficients $\alpha$, $\beta$, and $\gamma$ are weight factors that determine the significance of each term. 

This ordinary differential equation embodies the immune network dynamics that this algorithm leverages. Classifiers compete with each other via this concentration value. Since it is an ordinary differential equation, you have to calculate the next step's value using previous values, like any other algorithmic differential equation solver.
