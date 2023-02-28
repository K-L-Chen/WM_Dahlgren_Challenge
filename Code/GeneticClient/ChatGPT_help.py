"""All written by ChatGPT to help us get started with PyGAD,
originally started/edited by Joseph S. Lee"""

import numpy as np
import pygad

# Define chromosome representation
def create_chromosome():
    row = []
    for i in range(9):
        row.append(np.random.uniform(low=0.0, high=1.0))
    row.append(''.join(np.random.choice(['0', '1'], size=10)))
    return row

# Define custom crossover operator
def custom_crossover(parent_1, parent_2):
    child_1 = []
    child_2 = []
    for i in range(len(parent_1)):
        if isinstance(parent_1[i], float):
            # Use uniform crossover for floating-point values
            child_1.append(np.random.choice([parent_1[i], parent_2[i]]))
            child_2.append(np.random.choice([parent_1[i], parent_2[i]]))
        elif isinstance(parent_1[i], str):
            # Use single-point crossover for bitstrings
            crossover_point = np.random.randint(low=0, high=len(parent_1[i]))
            child_1.append(parent_1[i][:crossover_point] + parent_2[i][crossover_point:])
            child_2.append(parent_2[i][:crossover_point] + parent_1[i][crossover_point:])
    return child_1, child_2

# Define custom mutation operator
def custom_mutation(chromosome):
    mutated_chromosome = []
    for i in range(len(chromosome)):
        if isinstance(chromosome[i], float):
            # Use Gaussian mutation for floating-point values
            mutated_value = np.random.normal(loc=chromosome[i], scale=0.1)
            mutated_chromosome.append(np.clip(mutated_value, 0.0, 1.0))
        elif isinstance(chromosome[i], str):
            # Use bit-flip mutation for bitstrings
            mutation_point = np.random.randint(low=0, high=len(chromosome[i]))
            mutated_bit = '0' if chromosome[i][mutation_point] == '1' else '1'
            mutated_chromosome.append(chromosome[i][:mutation_point] + mutated_bit + chromosome[i][mutation_point+1:])
    return mutated_chromosome

# Define fitness function
def fitness_function(solution, solution_idx):
    # Calculate fitness value based on the solution
    return 1.0 / (1.0 + solution[0]**2 + solution[1]**2 + ... + int(solution[-1], 2))

# Create initial population
population_size = 50
num_generations = 100
num_parents_mating = 20
ga_instance = pygad.GA(num_generations=num_generations,
                       num_parents_mating=num_parents_mating,
                       fitness_func=fitness_function,
                       sol_per_pop=population_size,
                       num_genes=10*9+10,
                       gene_type=[np.float32]*9 + [str],
                       init_range_low=0.0,
                       init_range_high=1.0,
                       gene_space=[(0.0, 1.0)]*9 + [(None, None)],
                       parent_selection_type="rank",
                       crossover_type=custom_crossover,
                       mutation_type=custom_mutation)

# Run the genetic algorithm
ga_instance.run()

# Get the best solution and its fitness value
solution, fitness = ga_instance.best_solution()

# Print the results
print("Best solution: ", solution)
print("Best fitness: ", fitness)
