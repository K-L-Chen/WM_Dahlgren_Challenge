from pathlib import Path

run_score_lines = []
with open(Path(__file__).parent / 'score_outputs.txt', 'r') as f:
    for line in f:
        run_score_lines.append(int(line.split(' ')[-1]))

for i in range(0, len(run_score_lines), 100):
    gen_results = run_score_lines[i: i+100]
    print(f"Average generation {i // 100} score: {sum(gen_results)/ len(gen_results)}")