import pathlib
from utils import read_dataset, random_sample
from algorithm import GeneAttacker

DATA_PATH=pathlib.Path(__file__).parent / "data"


def run():
    data = read_dataset('svamp_test.json')
    initial_problems = random_sample(data, 10)
    
    ga = GeneAttacker(
        model_name="deepseek-reasoner",
        attacker_model_name="deepseek-chat",
        version="v1",
        fitness_strategy='min-max',
        number_to_split=5,
        population_size=len(initial_problems),
        elite_rate=0.4,
        crossover_rate=0.8,
        mutation_rate=0.2,
        generations=5,
        n_samples=1,
    )
    
    best_problem = ga.run(initial_problems)
    
    print("\n" + "="*50)
    print(f"Best problem: {best_problem}")
    print(f"Best fitness: {ga.best_fitness}")
    print(f"Best problem prompt: {best_problem.to_prompt()}")
    return {"question": best_problem.to_prompt(), "fitness": ga.best_fitness}

if __name__ == "__main__":
    run()
    
