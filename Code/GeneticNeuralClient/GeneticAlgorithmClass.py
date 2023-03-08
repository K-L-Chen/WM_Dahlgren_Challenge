"""
Contains our GeneticAlgorithm
"""
from NeuralNetModule import NeuralNet
import random 
import itertools
import torch.nn
import operator

#POPULATION_SAVE_DIR  "POPULATION_SIZE - CLONES must be divisible by 3!
POPULATION_SIZE = 100 # Number of neural nets in each generation
# POPULATION_SIZE = 50
# POPULATION_SIZE = 10
CLONES = 10 # Number of surviving/cloned neural nets that are the best per generation
# CLONES = 4
NUM_PAIRINGS_PER_GENERATION = (POPULATION_SIZE - CLONES) // 3

assert (POPULATION_SIZE - CLONES) % 3 == 0

import math
# ensure that there are enough number of possible pairings
# to refill the entire population again to its original
# population size
assert math.comb(CLONES, 2) >= NUM_PAIRINGS_PER_GENERATION

MAX_MUTATION_PERCENT = 1.0 # Can change a weight or a bias by up to MUTATION_SIZE of its current value
# MUTATION_RANGE = 2
MUTATION_RATE = 0.33 # Odds that any given weight or bias will mutate
# PARENT_PERCENTAGE = 0.2 # how much of the population we want to sample from for parents to breed
SHIFT_SIZE = 0.6 # When breeding, how much should the resulting (higher = more) children be shifted to their parents

class GeneticAlgorithm:
    
    def __init__(self, population_fp = None):
        """
        Parameters
        -------
        population - a list of neural nets loaded as .pt file, either pre-defined from training checkpoints
        or initialized as None if we're just starting off training
        """
        self.population = [NeuralNet() for _ in range(POPULATION_SIZE)]

        if population_fp:
            print(f"Loading population file from {population_fp}")
            self.set_population(population_fp)
            assert len(self.population) == POPULATION_SIZE

        print("Initializing genetic algorithm")
        print(f"POPULATION_SIZE:{POPULATION_SIZE}\nCLONES:{CLONES}\nNUM_PAIRINGS_PER_GENERATION:{NUM_PAIRINGS_PER_GENERATION}")
        print('\n')
        print(f'MAX_MUTATION_PERCENT:{MAX_MUTATION_PERCENT}\nMUTATION_RATE:{MUTATION_RATE}\nPARENT_WEIGHT:{SHIFT_SIZE}')

    
    
    def cull_and_rebuild(self):
        # Culls and rebuilds the population
        self.population.sort(reverse=True, key=operator.attrgetter("fitness"))
        survivors = self.population[0:CLONES]
        new_pairings = self.generate_pairings(survivors)

        j = 0
        for i in range(CLONES, POPULATION_SIZE, 3):
            self.population[i], self.population[i+1], self.population[i+2] = \
                self.breed(new_pairings[j][0],new_pairings[j][1])
            j += 1
        # self.reset_fitness()
        

    #Input: a list of the surviving clones from the previous generation
    #Output: a list of tuples containing two parents
    def generate_pairings(self, parents):
        pairings = itertools.combinations(parents, 2)
        return tuple(pairings)[0:NUM_PAIRINGS_PER_GENERATION]
    
    #Inputs: two parents
    #Outputs: tuple of three children:
    # 1. The average of the two parents
    # 2. Weighted towards `nn1` by SHIFT_SIZE
    # 3. Weighted towards `nn2` by SHIFT_SIZE

    def breed(self, nn1 : NeuralNet, nn2: NeuralNet):
        dimensions = nn1.get_dimensions()

        #Instantiate the three child neural networks
        c1 = NeuralNet(*dimensions)
        c2 = NeuralNet(*dimensions)
        c3 = NeuralNet(*dimensions)

        params_nn1 = nn1.named_parameters()
        params_nn2 = nn2.named_parameters()

        # children start off with parameters of `nn2`
        dict_params_c1 = dict(params_nn2)
        dict_params_c2 = {k:v for k, v in dict_params_c1.items()}
        dict_params_c3 = {k:v for k, v in dict_params_c2.items()}

        assert id(dict_params_c1) != id(dict_params_c2) \
            and id(dict_params_c1) != id(dict_params_c3) \
            and id(dict_params_c2) != id(dict_params_c3)

        for param_name, param_name_params in params_nn1:
            if param_name in dict_params_c1:
                # average of nn1 and nn2 params
                dict_params_c1[param_name].data.copy_(0.5 * (param_name_params.data + dict_params_c1[param_name].data))
                # weighted average towards nn1
                dict_params_c2[param_name].data.copy_(SHIFT_SIZE*param_name_params.data + (1 - SHIFT_SIZE)*dict_params_c2[param_name].data)
                # weighted average towards nn2
                dict_params_c3[param_name].data.copy_((1 - SHIFT_SIZE)*param_name_params.data + (SHIFT_SIZE)*dict_params_c3[param_name].data)

                # if mutation rate chance occurs
                if random.random() < MUTATION_RATE:
                    # perturbate between [0, MAX_MUTATION_PERCENT] for each child's param_name, additive or subtractive
                    # (i.e. perturbate betweeen 0 to 40% for each child's bias of this fully-connected layer)
                    mutation_val_c1 = random.uniform(-MUTATION_RATE, MUTATION_RATE)
                    mutataion_val_c2 = random.uniform(-MUTATION_RATE, MUTATION_RATE)
                    mutataion_val_c3 = random.uniform(-MUTATION_RATE, MUTATION_RATE)

                    dict_params_c1[param_name].data.copy_(dict_params_c1[param_name].data + MAX_MUTATION_PERCENT * mutation_val_c1 * dict_params_c1[param_name].data)
                    dict_params_c2[param_name].data.copy_(dict_params_c2[param_name].data + MAX_MUTATION_PERCENT * mutataion_val_c2 * dict_params_c2[param_name].data)
                    dict_params_c3[param_name].data.copy_(dict_params_c3[param_name].data + MAX_MUTATION_PERCENT * mutataion_val_c3 * dict_params_c3[param_name].data)
            else:
                print(f"Something is wrong here: the name {param_name} is not in dict_params_c1 keys: {dict_params_c1.keys()}")

        c1.load_state_dict(dict_params_c1)
        c2.load_state_dict(dict_params_c2)
        c3.load_state_dict(dict_params_c3)
        
        return c1,c2,c3 

    #Resets the fitness of all neural nets to 0, to be used between generations.
    def reset_fitness(self):
        for neural_net in self.population:
            neural_net.set_fitness(0)
            

    #Sets an entirely new population. Only called when loading an old population from a file.
    def set_population(self, population_fp):
        self.population = torch.load(population_fp)

    def save_population(self, population_fp):
        torch.save(self.population, population_fp)




"""
for param in NN.parameters():
    ....

# or
for name, param in NN.named_parameters():
    ...

    https://pytorch.org/tutorials/intermediate/reinforcement_q_learning.html
"""

