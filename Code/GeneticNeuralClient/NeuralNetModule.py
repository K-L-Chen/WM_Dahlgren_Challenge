"""
Contains the NeuralNet Class 

Each NeuralNet object takes in all the information from one StatePb message and decides on a weapon-target assignment
based on meeting above a certain threshold. In other words, it decides on the engagement strategy
per timestep.
"""

# import os
# import torch
from torch import nn
import torch.nn.functional as F

class NeuralNet(nn.Module):

    def __init__(self, input_size=210, hidden_size1=128, hidden_size2=256, output_size=300):
        """
        Constructor

        input_size: number of input nodes
            Our specific setup is 210 input nodes:
            - We have up to 5 ships, each having:
                - Health (up to 4)
                - Ammo for Cannon_System
                - Ammo for Chainshot_System
                - x position
                - y position
                - whether ship is high value (HVU) or not
            - We have up to 30 missiles, each having:
                - x position
                - y position
                - z position
                - x velocity
                - y velocity
                - z velocity
            - Therefore, 5 ships * 6 attributes/ship + 30 missiles * 6 attributes/missile = 210 total attributes
            - Less than five ships or 30 missiles means we'll zero out the corresponding input nodes 
        
        output_size:
            Our output layer has 300 nodes
                - 5 ships * 30 targets * 2 weapon types = 300
                - Each node is the probability that ship x will target enemy y with weapon type z
        
        hidden_size1: number of nodes for the first hidden layer
        hidden_size2: number of nodes for the second hidden layer

        prob_threshold: the minimum required threshold for taking action
            - the idea behind this is that our neural net should be able to choose to fire at multiple targets at once
            rather than the traditional neural net output where you just select one class out of many

        """
        super().__init__()

        self.fitness = 0

        self.input_size = input_size
        self.hidden_size1 = hidden_size1
        self.hidden_size2 = hidden_size2
        self.output_size = output_size

        # an affine operation: y = Wx + b
        self.fc1 = nn.Linear(input_size, hidden_size1)
        self.fc2 = nn.Linear(hidden_size1, hidden_size2)
        self.fc3 = nn.Linear(hidden_size2, output_size) 


    def forward(self, x):
        out = F.sigmoid(self.fc1(x))
        out = F.sigmoid(self.fc2(out))
        out = F.sigmoid(self.fc3(out))
        return out
        

    def get_fitness(self):
        """
        Returns the fitness value of this NeuralNet
        """
        return self.fitness
    
    
    def set_fitness(self, new_fitness:float):
        """
        Sets the fitness value of this NeuralNet

        @param: new_fitness: The new fitness to set the score to
        """
        self.fitness = new_fitness

    def get_dimensions(self):
        """
        Returns the dimensions of this neural net as a tuple
        """
        return self.input_size, self.hidden_size1, self.hidden_size2, self.output_size
        
    