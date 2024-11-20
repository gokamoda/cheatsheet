import argparse
import pickle
from collections import Counter
from pathlib import Path
from typing import Literal

from datasets import IterableDataset, load_dataset
from tqdm import tqdm
from transformers import AutoTokenizer
from transformers.utils import logging

from utils.mylogger import init_logging
from utils.path import WORK_DIR

LOG_PATH = "latest.log"
logger = init_logging(__name__, log_path=LOG_PATH, clear=True)


def get_save_path(dataset_name: str, tokenizer_name: str) -> Path:
    save_path = WORK_DIR.joinpath(f"freqs/{dataset_name}_{tokenizer_name}.pt")
    save_path.parent.mkdir(parents=True, exist_ok=True)
    return save_path


def tokenfreq(dataset, tokenizer, worker_id=0):
    freq_counter = Counter([])

    for instance in tqdm(dataset, position=worker_id, desc=f"{worker_id}"):
        text = instance["text"]
        input_ids = tokenizer(
            text,
            add_special_tokens=False,
            return_token_type_ids=False,
            return_attention_mask=False,
        )["input_ids"]
        freq_counter += Counter(input_ids)
    return freq_counter


def get_dataset(dataset_name: Literal["wikitext103", "openwebtext"]) -> IterableDataset:
    if dataset_name == "wikitext103":
        return load_dataset(
            "salesforce/wikitext",
            name="wikitext-103-raw-v1",
            split="test",
            streaming=True,
        )
    if dataset_name == "openwebtext":
        return load_dataset(
            "openwebtext", trust_remote_code=True, split="train", streaming=True
        )
    raise ValueError(f"Unknown dataset: {dataset_name}")


def main(dataset_name: str, tokenizer_name: str = None, num_workers=1):
    dataset = get_dataset(dataset_name)
    logger.info(f"Loaded dataset: {dataset_name}")

    tokenizer = AutoTokenizer.from_pretrained(tokenizer_name)
    logger.info(f"Loaded tokenizer: {tokenizer_name}")

    save_path = get_save_path(dataset_name, tokenizer_name)

    num_workers = min(num_workers, dataset.num_shards)

    if num_workers > 1:
        import multiprocessing

        with multiprocessing.Pool(num_workers) as pool:
            freq_counters = pool.starmap(
                tokenfreq,
                [
                    (
                        dataset.shard(num_shards=dataset.num_shards, index=shard),
                        tokenizer,
                        shard,
                    )
                    for shard in range(dataset.num_shards)
                ],
            )
    else:
        freq_counters = [tokenfreq(dataset, tokenizer)]

    freq_counter = Counter([])
    for counter_id in tqdm(range(len(freq_counters)), desc="Aggregating..."):
        freq_counter.update(freq_counters[counter_id])
        freq_counters[counter_id] = Counter([])

    logger.info(f"Saving to {save_path}")
    pickle.dump(freq_counter, open(save_path, "wb"))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("data", default="wiki", choices=["wikitext103", "openwebtext"])
    parser.add_argument("--tokenizer", default=None)
    parser.add_argument("--num-workers", type=int, default=1)
    args = parser.parse_args()

    main(args.data, args.tokenizer, args.num_workers)
