import json
import os
import random
from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class TrainingSample:
    features: dict
    label: str
    label_source: str
    timestamp: str


class DataPipeline:
    LABELS = ["compliance", "acceptance", "opportunity", "appeal"]
    LABEL_SOURCES = ["human_annotator", "llm_review", "rule_based"]

    def __init__(self, output_dir: str = "data/training"):
        self.output_dir = output_dir
        self.samples: list[TrainingSample] = []

    def _generate_mock_sample(self, label: str) -> TrainingSample:
        feature_keys = [
            "intent_score",
            "sentiment",
            "urgency",
            "key_phrase_match",
            "entity_count",
            "dialog_length",
            "talk_ratio",
        ]
        features = {k: round(random.uniform(0, 1), 4) for k in feature_keys}
        source = random.choice(self.LABEL_SOURCES)
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        return TrainingSample(features=features, label=label, label_source=source, timestamp=ts)

    def _generate_mock_data(self) -> list[TrainingSample]:
        label_distribution = {
            "compliance": 3,
            "acceptance": 2,
            "opportunity": 3,
            "appeal": 2,
        }
        samples: list[TrainingSample] = []
        for label, count in label_distribution.items():
            for _ in range(count):
                samples.append(self._generate_mock_sample(label))
        random.shuffle(samples)
        return samples

    def run(self):
        self.samples = self._generate_mock_data()
        os.makedirs(self.output_dir, exist_ok=True)
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        file_path = os.path.join(self.output_dir, f"{date_str}.jsonl")
        with open(file_path, "w") as f:
            for s in self.samples:
                f.write(
                    json.dumps(
                        {
                            "features": s.features,
                            "label": s.label,
                            "label_source": s.label_source,
                            "timestamp": s.timestamp,
                        }
                    )
                    + "\n"
                )
        print(f"Wrote {len(self.samples)} samples → {file_path}")
        self._print_summary()

    def _print_summary(self):
        counts: dict[str, int] = {}
        sources: dict[str, int] = {}
        for s in self.samples:
            counts[s.label] = counts.get(s.label, 0) + 1
            sources[s.label_source] = sources.get(s.label_source, 0) + 1
        print("\n=== Pipeline Summary ===")
        print(f"Total samples: {len(self.samples)}")
        print("By label:")
        for label in self.LABELS:
            print(f"  {label}: {counts.get(label, 0)}")
        print("By source:")
        for src in sorted(sources):
            print(f"  {src}: {sources[src]}")
        print("=======================\n")


if __name__ == "__main__":
    pipeline = DataPipeline()
    pipeline.run()
