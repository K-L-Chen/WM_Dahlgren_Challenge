"""
Contains our GeneticAlgorithm
"""
from NeuralNetClass import NeuralNet
import random 
import itertools
import torch.nn
import operator

#Hyperparameters - note POPULATION_SIZE - CLONES must be divisible by 3!
POPULATION_SIZE = 100 # Number of neural nets in each generation
CLONES = 10 # Number of surviving/cloned neural nets that are the best per generation
PAIRINGS_PER_GENERATION = (POPULATION_SIZE - CLONES) / 3

import math
assert math.comb(CLONES, 2) >= PAIRINGS_PER_GENERATION

MAX_MUTATION_PERCENT = 0.4 # Can change a weight or a bias by up to MUTATION_SIZE of its current value
MUTATION_RATE = 0.3 # Odds that any given weight or bias will mutate
PARENT_PERCENTAGE = 0.2 # how much of the population we want to sample from for parents to breed
SHIFT_SIZE = 0.8 # When breeding, how much should the resulting (higher = more) children be shifted to their parents

class GeneticAlgorithm:
    
    def __init__(self, population: list[NeuralNet] = None):
        """
        Parameters
        -------
        population - a list of neural nets, either pre-defined from training checkpoints
        or initialized as None if we're just starting off training
        """
        self.population = [NeuralNet() for _ in range(POPULATION_SIZE)]
        if population:
            self.population = population
            assert len(population) == POPULATION_SIZE
        

    #Input: a list of the surviving clones from the previous generation
    #Output: a list of tuples containing two parents
    def generate_pairings(self, parents):
        pairings = itertools.combinations(parents, 2)
        return pairings[0:PAIRINGS_PER_GENERATION]
    
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
        dict_params_c2 = dict(params_nn2)
        dict_params_c3 = dict(params_nn2)

        assert id(dict_params_c1) != id(dict_params_c2) \
            and id(dict_params_c1) != id(dict_params_c3) \
            and id(dict_params_c2) != id(dict_params_c3)

        for param_name, param_name_params in params_nn1:
            if param_name in dict_params_c1:
                # average of nn1 and nn2 params
                dict_params_c1[param_name].data.copy_(0.5 * (param_name_params.data + dict_params_c1[param_name].data))
                # weighted average towards nn1
                dict_params_c2[param_name].data.copy_(SHIFT_SIZE*param_name_params.data + (1- SHIFT_SIZE)*dict_params_c2[param_name].data)
                # weighted average towards nn2
                dict_params_c3[param_name].data.copy_((1 - SHIFT_SIZE)*param_name_params.data + (SHIFT_SIZE)*dict_params_c3[param_name].data)

                # if mutation rate chance occurs
                if random.random() < MUTATION_RATE:
                    # perturbate between [0, MAX_MUTATION_PERCENT] for each child's param_name, additive or subtractive
                    # (i.e. perturbate betweeen 0 to 40% for each child's bias of this fully-connected layer)
                    dict_params_c1[param_name].data.copy_(dict_params_c1[param_name].data + MAX_MUTATION_PERCENT * random.uniform(-1,1) * dict_params_c1[param_name].data)
                    dict_params_c2[param_name].data.copy_(dict_params_c2[param_name].data + MAX_MUTATION_PERCENT * random.uniform(-1,1) * dict_params_c2[param_name].data)
                    dict_params_c3[param_name].data.copy_(dict_params_c3[param_name].data + MAX_MUTATION_PERCENT * random.uniform(-1,1) * dict_params_c3[param_name].data)
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
            
    #Culls and rebuilds the population
    def cull(self):
        self.population.sort(reverse=True, key=operator.attrgetter("fitness"))
        survivors = self.population[0:CLONES]
        new_pairings = self.generate_pairings(survivors)
        for i in range(CLONES, POPULATION_SIZE, 3):
            self.population[i], self.population[i+1], self.population[i+2] = \
                self.breed(new_pairings[i//3][0],new_pairings[i//3][1])
        self.resetFitness()
            

    #Sets an entirely new population. Only called when loading an old population from a file.
    def set_population(self, population_fp: str):
        self.population = torch.load(population_fp)

    def save_population(self, population_fp: str):
        torch.save(self.population, population_fp)




"""
for param in NN.parameters():
    ....

# or
for name, param in NN.named_parameters():
    ...

    https://pytorch.org/tutorials/intermediate/reinforcement_q_learning.html
"""

