### **Algorithm Concept Design**

Given a mathematical problem dataset, the following operations are defined:

1. **Split Problem**: A problem can be split into several premises and a question.
2. **Remove Premise**: Eliminate one premise from the problem.
3. **Crossover Problems**: Swap the premises and questions between two problems.

**Background**: Large Language Models (LLMs) tend to overthink when faced with logically confusing or chaotic problems.

**Objective**: Use a genetic algorithm to optimize input problems such that the response token count from the LLM is maximized.

First, we define the core elements of the algorithm:

- **Individual**: An independent mathematical problem. For ease of manipulation, it is represented structurally, e.g., `{premises: ["premise 1", "premise 2", ...], question: "question"}`.
- **Population**: A collection of "individuals" (mathematical problems).
- **Fitness Function**: The core criterion for evaluating the quality of an individual. Here, **Fitness = Number of tokens in the LLM's response to the problem**. A higher score indicates higher "logical confusion," which is more likely to trigger "overthinking" in the model.
- **Genetic Operators**:
  - **Crossover**: Corresponds to the defined "Crossover Problems" operation.
  - **Mutation**: Corresponds to the "Remove Premise" operation, and can also include other random alterations (e.g., randomly combining premises from different problems).

### **Genetic Algorithm Core Loop Design**

Assume we have an initial population of mathematical problems (selected from the dataset and structurally formatted via the initial "Split Problem" operation).

**Loop Start:** For each preset Generation:

------



#### **Step 1: Fitness Evaluation**

This is the most critical and computationally expensive step in the loop.

1. **Iterate Population**: Retrieve each problem (individual) from the current population.
2. **Format Input**: Reassemble the structured problem `{premises, question}` into a complete text string as input to the LLM. For example: "Given [premise 1], [premise 2], ..., [question]?"
3. **Call LLM**: Send this text string to the specified LLM.
4. **Calculate Fitness**: Obtain the model's response and **count the response tokens**. This count serves as the fitness score for the problem.
5. **Record Score**: Associate the calculated fitness score with the problem.

*After this step, every problem in the current population has a distinct fitness score.*

------



#### **Step 2: Selection**



The purpose of this step is survival of the fittest, selecting superior parents to produce the next generation.

1. **Elitism**: Directly copy the top `N` problems with the highest fitness scores to the next generation. This ensures that the best solutions found so far are not lost during evolution.
2. **Parent Selection**: For the remaining slots, select "parents" from the current population. **Roulette Wheel Selection** is typically used:
   - The higher a problem's fitness score, the greater its probability of being selected as a parent.
   - This approach preserves excellent links while giving sub-optimal solutions a chance, maintaining population diversity.

------



#### **Step 3: Crossover and Mutation**



This is the core step for creating new individuals, exploring new and potentially better problem combinations through genetic recombination and random alterations.

1. **Pairing**: Pair up the parents selected in the previous step.
2. **Crossover Operation**: Apply the "**Crossover Problems**" operation to each pair of parents with a high crossover probability (e.g., `80%`).
   - **Problem A**: `{premises_A, question_A}`
   - **Problem B**: `{premises_B, question_B}`
   - Generate two new offspring problems by swapping their premises or questions. For example:
     - **Offspring C**: `{premises_A, question_B}`
     - **Offspring D**: `{premises_B, question_A}`
   - If crossover is not triggered, parents directly become offspring.
3. **Mutation Operation**: Apply mutation to each offspring generated from crossover with a low mutation probability (e.g., `10%`).
   - **Execute "Remove Premise"**: Randomly select and delete one premise from the offspring problem. This directly introduces logical inconsistency and increases confusion.
   - *(Optional)* More diverse mutation operations can be designed, such as "stealing" a premise from another random problem in the population to further increase confusion.

------



#### **Step 4: Form New Population**



Combine all new problems generated via Elitism, Crossover, and Mutation to form a new population of the same size as the previous generation.

------

**Loop End:**

This new population replaces the old population and enters the next generation loop, repeating the entire process of "Fitness Evaluation → Selection → Crossover and Mutation."

The algorithm terminates after reaching the preset number of generations. The problem with the highest fitness score (i.e., triggering the maximum response tokens from the LLM) across all generations is the final optimal solution.