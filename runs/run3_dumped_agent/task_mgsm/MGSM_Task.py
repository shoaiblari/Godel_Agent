

class MGSM_Task:
    def evaluate(self, solver):
        examples = get_all_examples()
        random.seed(0)
        random.shuffle(examples)
        examples = examples[:128]
        random.seed(time.time())
        random.shuffle(examples)
        examples = examples[:50]
        questions = [example['inputs'] for example in examples]
        answers = [example['targets'] for example in examples]
        max_workers = min(len(examples), 48)
        task_queue = []
        for q in questions:
            task_queue.append(q)
    
        acc_list = []
        info_list = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            results = list(tqdm(executor.map(solver, task_queue), total=len(task_queue)))

        for q_idx, res in enumerate(results):
            try:
                extracted_answer = str(res["answer"])
                correct_answer = str(answers[q_idx])
                correct = score_mgsm(correct_answer, extracted_answer)
            except Exception as e:
                info_list.append(f"Valid Sample {q_idx}:\n{repr(e)}\nModel Output: {res}\n")
                acc_list.append(0)
                continue
            acc_list.append(correct)
            info_list.append(f"Valid Sample {q_idx}:\n{task_queue[q_idx]}\nModel Output: {res}\nModel Answer: {extracted_answer}\nCorrect Answer: {correct_answer}\nIs Correct: {acc_list[-1]}\n")

        valid_acc = sum(acc_list) / len(acc_list)
        print("Acc:", valid_acc)
        if valid_acc >= threshold:
            test_acc = real_evaluate(solver)
            feedback = f"Valid Accuracy: {valid_acc}\nTest Accuracy {test_acc}\n"# + "Evaluation Info:\n" + "\n".join(info_list)
        else:
            test_acc = 0
            feedback = f"`Valid Accuracy: `{valid_acc}\nValid Accuracy less than {threshold}, no testing needed.\n" #+ "Evaluation Info:\n" + "\n".join(info_list)
        return feedback, test_acc
