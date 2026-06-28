#!/usr/bin/env python3
"""LoRA 微调实验脚本：生成 function calling 训练数据 → LoRA 微调 → 保存 adapter。"""

import json
import logging
import os
import random

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MODEL_NAME = os.getenv("BASE_MODEL", "Qwen/Qwen2.5-7B-Instruct")
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "models/agent-lora-adapter")
NUM_SAMPLES = 200
MAX_SEQ_LENGTH = 1024

TOOLS = [
    {
        "name": "search_hcp",
        "description": "搜索 HCP 信息",
        "parameters": {"type": "object", "properties": {"name": {"type": "string"}, "specialty": {"type": "string"}}, "required": ["name"]},
    },
    {
        "name": "check_compliance",
        "description": "检查合规状态",
        "parameters": {"type": "object", "properties": {"rule_id": {"type": "string"}, "entity": {"type": "string"}}, "required": ["rule_id"]},
    },
    {
        "name": "query_competitor",
        "description": "查询竞品信息",
        "parameters": {"type": "object", "properties": {"drug_name": {"type": "string"}}, "required": ["drug_name"]},
    },
    {
        "name": "calculate_budget",
        "description": "计算预算",
        "parameters": {"type": "object", "properties": {"amount": {"type": "number"}, "department": {"type": "string"}}, "required": ["amount"]},
    },
    {
        "name": "submit_report",
        "description": "提交报告",
        "parameters": {
            "type": "object",
            "properties": {"report_type": {"type": "string"}, "content": {"type": "string"}},
            "required": ["report_type", "content"],
        },
    },
]

SCENARIOS = [
    {"query": "帮我查一下 Dr. Smith 的信息", "tool": "search_hcp", "args": {"name": "Dr. Smith"}},
    {"query": "检查一下合规规则 R-001 的状态", "tool": "check_compliance", "args": {"rule_id": "R-001", "entity": "pharma"}},
    {"query": "查询阿托伐他汀的竞品信息", "tool": "query_competitor", "args": {"drug_name": "阿托伐他汀"}},
    {"query": "市场部 Q3 预算 50000", "tool": "calculate_budget", "args": {"amount": 50000, "department": "市场部"}},
    {"query": "提交拜访报告，内容：拜访了 Dr. Li", "tool": "submit_report", "args": {"report_type": "visit", "content": "拜访了 Dr. Li"}},
    {"query": "搜索心内科专家", "tool": "search_hcp", "args": {"name": "", "specialty": "心内科"}},
    {"query": "看看 R-002 的合规情况", "tool": "check_compliance", "args": {"rule_id": "R-002"}},
    {"query": "查询瑞舒伐他汀的竞品", "tool": "query_competitor", "args": {"drug_name": "瑞舒伐他汀"}},
    {"query": "预算 120000 销售部", "tool": "calculate_budget", "args": {"amount": 120000, "department": "销售部"}},
    {"query": "提交费用报告：差旅费 3000", "tool": "submit_report", "args": {"report_type": "expense", "content": "差旅费 3000"}},
]


def generate_training_data(num: int) -> list[dict]:
    data = []
    for i in range(num):
        scenario = random.choice(SCENARIOS)
        system_prompt = "你是一个医药合规助手，请根据用户意图选择合适的工具。"
        tool_defs = json.dumps(TOOLS, ensure_ascii=False)
        user_query = scenario["query"]
        assistant_response = json.dumps({"tool": scenario["tool"], "arguments": scenario["args"]}, ensure_ascii=False)

        messages = [
            {"role": "system", "content": f"{system_prompt}\n\n可用工具：\n{tool_defs}"},
            {"role": "user", "content": user_query},
            {"role": "assistant", "content": assistant_response},
        ]

        data.append({"messages": messages, "tools": TOOLS, "tool_choice": scenario["tool"]})
    return data


def train_lora(data: list[dict]):
    from peft import LoraConfig, TaskType, get_peft_model
    from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments
    from trl import SFTTrainer

    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, trust_remote_code=True)
    tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"

    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,
        trust_remote_code=True,
        torch_dtype="auto",
        device_map="auto",
    )

    lora_config = LoraConfig(
        task_type=TaskType.CAUSAL_LM,
        r=8,
        lora_alpha=32,
        lora_dropout=0.1,
        target_modules=["q_proj", "v_proj"],
        bias="none",
    )
    model = get_peft_model(model, lora_config)

    def format_func(example):
        text = ""
        for msg in example["messages"]:
            text += f"<|{msg['role']}|>\n{msg['content']}\n"
        text += "<|assistant|>\n"
        return text

    texts = [format_func(ex) for ex in data]

    training_args = TrainingArguments(
        output_dir=OUTPUT_DIR,
        per_device_train_batch_size=4,
        gradient_accumulation_steps=2,
        num_train_epochs=3,
        learning_rate=2e-4,
        fp16=True,
        save_steps=50,
        logging_steps=10,
        save_total_limit=2,
        remove_unused_columns=False,
        report_to="none",
    )

    trainer = SFTTrainer(
        model=model,
        args=training_args,
        train_dataset=texts,
        tokenizer=tokenizer,
        max_seq_length=MAX_SEQ_LENGTH,
        formatting_func=format_func,
    )

    logger.info("Starting LoRA fine-tuning on %d samples with base model %s", len(data), MODEL_NAME)
    trainer.train()
    trainer.save_model(OUTPUT_DIR)
    tokenizer.save_pretrained(OUTPUT_DIR)
    logger.info("Adapter saved to %s", OUTPUT_DIR)


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    data = generate_training_data(NUM_SAMPLES)
    with open(os.path.join(OUTPUT_DIR, "training_data.json"), "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    logger.info("Generated %d training samples", len(data))
    train_lora(data)


if __name__ == "__main__":
    main()
