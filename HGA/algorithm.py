from abc import abstractmethod,ABC
import swanlab
import random
import re
import os
from dotenv import load_dotenv
from typing import List, Literal, Sequence, Tuple
from models.model import TargetModel, AttackerModel, BaseProblem
from prompts.prompts import *
from collections import Counter
import logging
load_dotenv()

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class GeneAttacker:

    def __init__(self,
                 model_name: str = "deepseek-reasoner",
                 attacker_model_name: str = "deepseek-chat",
                 version: Literal["v1", "v2"] = "v1", # v1 for spilit premises, v2 for split subquestions
                 number_to_split: int = 3, # only for v2
                 fitness_strategy :Literal['length', 'overthink', 'z-score', 'min-max'] = 'length',
                 population_size: int = 20,
                 elite_rate: float = 0.2,
                 crossover_rate: float = 0.8,
                 mutation_rate: float = 0.1,
                 generations: int = 10,
                 n_samples: int = 1, # number of rollouts
                 test_name: str = "genetic-algorithm",
                 ):

        self.model = TargetModel(model_name)
        self.attacker = AttackerModel(attacker_model_name, version=version, number=number_to_split)
        self.version = version
        self.population_size = population_size
        self.elite_size = int(elite_rate * population_size)
        self.crossover_rate = crossover_rate
        self.mutation_rate = mutation_rate
        self.generations = generations
        self.n_samples = n_samples

        if fitness_strategy == 'length':
            self.fitness_func = lambda length,_, **kwargs: length
        elif fitness_strategy == 'overthink':
            self.fitness_func = lambda _, overthink, **kwargs: overthink
        elif fitness_strategy == 'z-score':
            def z_score(length, overthink, **kwargs):
                avg_length = kwargs.get('avg_length', 0)
                std_length = kwargs.get('std_length', 1)
                avg_overthink = kwargs.get('avg_overthink', 0)
                std_overthink = kwargs.get('std_overthink', 1)
                length_z = (length - avg_length) / (std_length + 1e-5)
                overthink_z = (overthink - avg_overthink) / (std_overthink + 1e-5)
                return length_z + overthink_z
            self.fitness_func = z_score
        elif fitness_strategy == 'min-max':
            def min_max(length, overthink, **kwargs):
                length_min = kwargs.get('length_min', 0)
                length_max = kwargs.get('length_max', 1)
                overthink_min = kwargs.get('overthink_min', 0)
                overthink_max = kwargs.get('overthink_max', 1)
                length_score = (length - length_min) / (length_max - length_min + 1e-5)
                overthink_score = (overthink - overthink_min) / (overthink_max - overthink_min + 1e-5) 
                return length_score + overthink_score
            self.fitness_func = min_max
        
        self.population = []
        self.best_individual = None
        self.best_fitness = 0
        self.fitness_history = []
        
        self.overthink_word = [
            "alternatively", "but", "wait","perhaps", "another", "maybe"
        ]
        self.metadata = []
        swanlab.init(
            project="overthink-black",
            name=test_name,
            config={
                "model_name": model_name,
                "population_size": population_size,
                "elite_rate": elite_rate,
                "crossover_rate": crossover_rate,
                "mutation_rate": mutation_rate,
                "generations": generations,
                "n_samples": n_samples,
            }
        )
    
    def count_tokens(self, chat_usage)->int:
        if chat_usage is None:
            return 0

        if hasattr(chat_usage.completion_tokens_details, "reasoning_tokens"):
            return chat_usage.completion_tokens_details.reasoning_tokens
        elif hasattr(chat_usage, "completion_tokens"):
            return chat_usage.completion_tokens
        else:
            return 0
    
    def _get_metadta(self, resps, chat_usages) -> dict:
        def word_count(text):
            words = re.findall(r'\w+', text.lower())
    
            total_count = len(words)
            counter = Counter(words)
            
            cnt = 0
            for word in self.overthink_word:
                word_lower = word.lower()
                cnt += counter.get(word_lower, 0)
            
            return cnt
        
        if chat_usages is None or len(chat_usages) == 0:
            return {"length": 0.0,  "overthink_count": 0}
        else:
            sample_tokens = [self.count_tokens(usage) for usage in chat_usages]
            avg_length = sum(sample_tokens) / len(sample_tokens) if sample_tokens else 0.0
            overthink_index = sum([word_count(resp) for resp in resps]) / len(resps)
            return {
                "length": avg_length,
                "overthink_count": overthink_index,
            }
    
    def evaluate_fitness(self):
        try:
            prompts = [ind.to_prompt() for ind in self.population]
            results = self.model.agenerate(prompts, n_samples=self.n_samples)
            if results is None:
                return []
            lengths = []
            counts = []
            for i, result in enumerate(results):
                resp, chat_usages = result
                metadata = self._get_metadta(resp, chat_usages)
                lengths.append(metadata["length"])
                counts.append(metadata["overthink_count"])
                
            avg_length = sum(lengths) / len(lengths)
            std_length = (sum((l - avg_length) ** 2 for l in lengths) / len(lengths)) ** 0.5
            avg_overthink = sum(counts) / len(counts)
            std_overthink = (sum((o - avg_overthink) ** 2 for o in counts) / len(counts)) ** 0.5
            
            for i in range(len(self.population)):
                self.population[i].fitness =  \
                    self.fitness_func(lengths[i], counts[i], 
                                      avg_length=avg_length, std_length=std_length,
                                      avg_overthink=avg_overthink, std_overthink=std_overthink,
                                      length_min=min(lengths), length_max=max(lengths),
                                      overthink_min=min(counts), overthink_max=max(counts),
                                      )
            
            self.metadata.append({
                "avg_length": avg_length,
                "max_length": max(lengths),
                "std_length": std_length,
                "avg_overthink": avg_overthink,
                "std_overthink": std_overthink,
                "max_overthink": max(counts),
            })
            
            
        except Exception as e:
            print(f"Error evaluating fitness: {e}")
            raise e
    
    def evaluate_population(self):
        self.evaluate_fitness()
        
        for individual in self.population:
            if individual.fitness > self.best_fitness:
                self.best_fitness = individual.fitness
                self.best_individual = individual.copy()

    
    def roulette_wheel_selection(self, num_parents: int) -> Sequence[BaseProblem]:

        total_fitness = sum(ind.fitness for ind in self.population)
        try:
            probabilities = [ind.fitness / total_fitness for ind in self.population]

            
            parents = random.choices(self.population, weights=probabilities, k=num_parents)
        except Exception as e:
            return random.choices(self.population, k=num_parents)
        return parents
        
    
    def crossover(self, parent1: BaseProblem, parent2: BaseProblem) -> Tuple[BaseProblem, BaseProblem]:

        child1 = parent1.copy()
        child2 = parent2.copy()
        if self.version == "v1":
            if random.random() < self.crossover_rate:
                if random.random() < 0.5:

                    if parent1.children and parent2.children:

                        premise1 = random.choice(parent1.children)
                        premise2 = random.choice(parent2.children)

                        child1.children = [premise2 if p == premise1 else p for p in parent1.children]
                        child2.children = [premise1 if p == premise2 else p for p in parent2.children]
                else:
                    child1.question, child2.question = parent2.question, parent1.question
        else:
            if random.random() < self.crossover_rate:
                n = min(len(parent1.children),len(parent2.children))
                num_groups = (n + 1) // 2  
                for group_index in range(1, num_groups + 1):
                    start = (group_index - 1) * 2
                    end = min(start + 2, n)
                    if group_index % 2 == 0:  
                        for j in range(start, end):
                            parent1.children[j], parent2.children[j] = parent2.children[j], parent1.children[j]
                child1.children, child2.children = parent2.children.copy(), parent1.children.copy()
        return child1, child2
    
    def mutate(self, individual: BaseProblem) -> BaseProblem:
        mutated = individual.copy()
        if random.random() < self.mutation_rate:
            mutation_type = random.choice(["remove_premise", "add_premise"])
            
            if mutation_type == "remove_premise" and len(mutated.children) > 0:
                # eliminate a random child
                mutated.children.pop(random.randint(0, len(mutated.children) - 1))
            
            elif mutation_type == "add_premise" and len(self.population) > 1:
                # add a random child from another individual
                other_individual = random.choice(self.population)
                if other_individual.children:
                    new_premise = random.choice(other_individual.children)
                    if new_premise not in mutated.children:
                        insert_pos = random.randint(0, len(mutated.children))
                        mutated.children.insert(insert_pos, new_premise)
        
        return mutated
    
    def evolve_generation(self):
        """Evolve one generation"""
        # 1. Fitness evaluation
        self.evaluate_population()
        
        # 2. Selection: Elitism
        self.population.sort(key=lambda x: x.fitness, reverse=True)
        new_population = [ind.copy() for ind in self.population[:self.elite_size]]
        
        # 3. Generate remaining individuals
        while len(new_population) < self.population_size:
            # Select parents
            parents = self.roulette_wheel_selection(2)
            parent1, parent2 = parents[0], parents[1]
            
            # Crossover
            child1, child2 = self.crossover(parent1, parent2)
            
            # Mutation
            child1 = self.mutate(child1)
            child2 = self.mutate(child2)
            
            # Add to new population
            new_population.extend([child1, child2])
        
        # Ensure correct population size
        self.population = new_population[:self.population_size]
    
    def run(self, initial_problems: List[str]) -> BaseProblem:
        
        self.population = list(self.attacker.split_question(initial_problems))
        
        logger.info(f"Start attacking. Set size: {self.population_size}, generation: {self.generations}")
        
        for generation in range(self.generations):
            print(f"\n=== Gen {generation} ===")
            
            self.evolve_generation()
            
            current_best_fitness = max(ind.fitness for ind in self.population)
            self.fitness_history.append(current_best_fitness)
            current_mean_fitness = sum(ind.fitness for ind in self.population) / len(self.population)
            current_std_fitness = (sum((ind.fitness - current_mean_fitness) ** 2 for ind in self.population) / len(self.population)) ** 0.5
            logger.info(f"Current average fitness: {current_mean_fitness}")
            logger.info(f"Current fitness std: {current_std_fitness}")
            logger.info(f"Current best fitness: {current_best_fitness}")
            logger.info(f"All best fitness: {self.best_fitness}")
            logger.info(f"Current max tokens: {self.metadata[-1]['max_length']}")
            logger.info(f"Current max overthink count: {self.metadata[-1]['max_overthink']}")
            
            swanlab.log({
                "current_best_fitness": current_best_fitness,
                "best_fitness": self.best_fitness,
                "current_mean_fitness": current_mean_fitness,
                "current_std_fitness": current_std_fitness,
                **self.metadata[-1],
            })
            
            if self.best_individual:
                print(f"Best individual: {self.best_individual}")
        
        if self.best_individual is None:
            self.population.sort(key=lambda x: x.fitness, reverse=True)
            return self.population[0]
        swanlab.finish()
        return self.best_individual
